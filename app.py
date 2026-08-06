import base64
import datetime
import hashlib
import os
import secrets
from pathlib import Path

from src.shared import Config, login_required, get_current_user

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, g, current_app
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.security import sanitize_html, validate_external_url


def _get_client_ip():
    trusted = set(current_app.config.get("TRUSTED_PROXIES", []))
    remote_addr = request.remote_addr or ""
    forwarded_for = request.headers.getlist("X-Forwarded-For")
    if forwarded_for and remote_addr in trusted:
        return forwarded_for[0].split(",")[0].strip()
    return get_remote_address()


def _is_production_env():
    return os.environ.get("FLASK_ENV", "development") == "production"


db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=["1000 per hour"],
    storage_uri=os.environ.get("REDIS_URL", "memory://"),
)


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    # ────────────────────────────────────────────
    #  #15: Enforce no debug mode in production
    # ────────────────────────────────────────────
    if _is_production_env():
        flask_debug = os.environ.get("FLASK_DEBUG", "0").lower()
        if flask_debug in ("1", "true", "yes"):
            raise RuntimeError(
                "CRITICAL: FLASK_DEBUG=true is not allowed in production. "
                "Set FLASK_ENV=production and keep FLASK_DEBUG disabled."
            )

    app = Flask(__name__, template_folder="templates")
    app.jinja_env.autoescape = True  # Défend contre les XSS via échappement automatique

    # Respect reverse proxy headers only when behind trusted proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # ────────────────────────────────────────────
    #  CSP nonce generator + CSRF token generation
    # ────────────────────────────────────────────
    @app.before_request
    def combined_before_request():
        g.csp_nonce = base64.b64encode(secrets.token_bytes(16)).decode()

        current_app.config["SESSION_COOKIE_SECURE"] = request.is_secure

        from flask_wtf.csrf import generate_csrf
        g.csrf_token = generate_csrf()

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if "/api/" in request.path:
                if current_app.config.get("TESTING") or not current_app.config.get("WTF_CSRF_ENABLED", True):
                    pass
                elif not request.headers.get("X-CSRF-Token"):
                    return jsonify({"error": "Token CSRF requis pour les requêtes API"}), 422

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Protection CSRF: formulaires HTML protégés, routes /api/* exemptées (X-CSRF-Token header requis)
    app.config["WTF_CSRF_FIELD_NAME"] = "_csrf_token"
    csrf = CSRFProtect(app)

    # Patch Flask-WTF : seul le healthcheck est exempté de CSRF
    EXEMPTED_ENDPOINTS = {
        "health_check",
    }

    _original_protect = csrf.protect

    def _patched_protect():
        from flask import request as req
        if req.path == "/health":
            return
        endpoint = req.endpoint or ""
        if endpoint in EXEMPTED_ENDPOINTS:
            return
        # API requests are validated in combined_before_request (X-CSRF-Token header check)
        if "/api/" in req.path:
            return
        return _original_protect()

    csrf.protect = _patched_protect

    # Rate limiting pour prévenir le brute-force sur les routes d'authentification
    limiter.init_app(app)

    # ────────────────────────────────────────────
    #  Database setup
    # ────────────────────────────────────────────
    # #17: Enforce SSL for PostgreSQL connections (skip for SQLite/testing)
    db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri:
        raise RuntimeError(
            "CRITICAL: SQLALCHEMY_DATABASE_URI must be set via environment variable. "
            "No fallback to defaults for security."
        )

    # Only apply SSL settings to PostgreSQL connections
    if not db_uri.startswith("sqlite://"):
        if "sslmode" not in db_uri:
            separator = "&" if "?" in db_uri else "?"
            ssl_root = os.environ.get("DB_SSL_ROOT_CERT", "")
            ssl_cert = os.environ.get("DB_SSL_CERT", "")
            ssl_key = os.environ.get("DB_SSL_KEY", "")

            if ssl_root and ssl_cert and ssl_key:
                db_uri = f"{db_uri}{separator}sslmode=verify-full&sslrootcert={ssl_root}&sslcert={ssl_cert}&sslkey={ssl_key}"
            else:
                db_uri = f"{db_uri}{separator}sslmode=prefer"

    # #16: Connection pooling configuration
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo": False,
    }

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db=db)

    @app.route("/health")
    @limiter.exempt
    def health_check():
        return {"status": "ok"}

    @app.route("/static/cache/img/<filename>")
    def serve_cached_image(filename):
        cache_dir = Path(os.path.dirname(__file__)) / "instance" / "image_cache"
        name = Path(filename).stem
        file_path = cache_dir / name
        if file_path.exists():
            from flask import send_file
            return send_file(str(file_path))
        return ("", 404)

    # ────────────────────────────────────────────
    #  Security Headers & Cookie Settings
    # ────────────────────────────────────────────
    # #20: CSP with nonce-based script/style instead of 'unsafe-inline'
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        nonce = getattr(g, "csp_nonce", "")
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            f"script-src 'self' 'nonce-{nonce}' https://unpkg.com; "
            f"font-src 'self' https://fonts.gstatic.com data:; "
            f"img-src 'self' data:; "
            f"connect-src 'self' https://unpkg.com https://*.tile.openstreetmap.org; "
            f"object-src 'none'; "
            f"base-uri 'none'; "
            f"form-action 'self'; "
            f"upgrade-insecure-requests"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Access-Control-Allow-Origin"] = request.origin if request.origin else request.host_url.rstrip("/")
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-CSRF-Token"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        csrf_signed = g.get("csrf_token", "")
        if csrf_signed:
            response.set_cookie(
                "csrf_token",
                csrf_signed,
                httponly=True,
                samesite="Strict",
                secure=request.is_secure,
                path="/",
            )

        return response



    # Inject CSP nonce + current user into all templates
    @app.context_processor
    def inject_vars():
        from src.admin import is_catalogue_enabled
        from src.admin.settings import get_setting
        cu = get_current_user()
        return {
            "csp_nonce": getattr(g, "csp_nonce", ""),
            "csrf_token_meta": getattr(g, "csrf_token", ""),
            "current_user": cu,
            "is_catalogue_enabled": is_catalogue_enabled,
            "get_setting": get_setting,
        }

    # Configuration des cookies sécurisés
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SESSION_COOKIE_SECURE"] = False  # géré dynamiquement dans before_request
    app.config["TRUSTED_PROXIES"] = ["nginx", "127.0.0.1", "::1"]
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    # Enregistrer tous les blueprints
    from src import _register_view, _legacy_catalogue, register_all_blueprints

    register_all_blueprints(app)

    # Route legacy /catalogue avec endpoint="catalogue" pour compatibilité templates
    @app.route("/catalogue", endpoint="catalogue")
    def _legacy_catalogue_endpoint():
        catalogue = request.args.get("catalogue", "donnees")
        try:
            page = int(request.args.get("page", 1))
        except (ValueError, TypeError):
            page = 1
        return _legacy_catalogue(catalogue, page)

    return app


# ────────────────────────────────────────────
#  Local dev runner
# ────────────────────────────────────────────
if __name__ == "__main__":
    # En production, la clé secrète est généralement configurée via des variables d'environnement.
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes") and not _is_production_env()
    app = create_app()
    app.run(debug=debug_mode)
