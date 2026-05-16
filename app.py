import os

from src.shared import Config, _build_page_numbers, ITEMS_PER_PAGE, SECRET_FILE, login_required, get_current_user

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.security import sanitize_html, validate_external_url

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per hour"])


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    app = Flask(__name__, template_folder="templates")

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Protection CSRF: formulaires HTML protégés, routes /api/* exemptées (X-CSRF-Token header requis)
    csrf = CSRFProtect(app)

    # Patch Flask-WTF pour exempter les routes /api/* et /health du contrôle CSRF automatique
    _original_protect = csrf.protect
    def _patched_protect():
        from flask import request as req
        if '/api/' in req.path or req.path == '/health':
            return  # bypass CSRF pour API et health
        return _original_protect()
    csrf.protect = _patched_protect

    @app.before_request
    def check_csrf_header():
        """Exiger un token X-CSRF-Token pour les requêtes JSON API"""
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            content_type = request.content_type or ""
            if "/api/" in request.path and "application/json" in content_type:
                if not request.headers.get("X-CSRF-Token"):
                    return jsonify({"error": "Token CSRF requis pour les requêtes API"}), 422

    # Rate limiting pour prévenir le brute-force sur les routes d'authentification
    limiter.init_app(app)

    # ────────────────────────────────────────────
    #  Database setup
    # ────────────────────────────────────────────
    db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri:
        raise RuntimeError(
            "CRITICAL: SQLALCHEMY_DATABASE_URI must be set via environment variable. "
            "No fallback to defaults for security."
        )
    elif "sslmode" not in db_uri:
        separator = "&" if "?" in db_uri else "?"
        db_uri = f"{db_uri}{separator}sslmode=disable"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db=db)

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    @app.route("/connexion", methods=["POST"])
    @limiter.limit("5 per hour")
    def connexion_post():
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        from models import User
        from werkzeug.security import check_password_hash

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
            session.pop("_csrf_token", None)
            session["user_id"] = user.id
            session.modified = True
            return redirect(url_for("home"))

        if user and (not user.is_active or user.banned):
            return render_template("connexion.html", error="banned"), 401

        return render_template("connexion.html", error="Identifiants incorrects"), 401

    # ────────────────────────────────────────────
    #  Security Headers & Cookie Settings
    # ────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self' https://unpkg.com https://*.tile.openstreetmap.org"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response



    @app.context_processor
    def inject_user():
        cu = get_current_user()
        return {"current_user": cu}

    # Configuration des cookies sécurisés
    # Déterminer si on est en production
    is_production = os.environ.get("FLASK_ENV", "development") == "production"

    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Empêche les scripts JavaScript de lire le cookie de session
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Protection contre les attaques CSRF par cookie
    app.config["SESSION_COOKIE_SECURE"] = is_production  # En production seulement, force HTTPS pour les cookies
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # Les sessions expireront après 30 minutes
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # Limite de 10 Mo pour les uploads (Max-Content-Length)

    # Définition des routes statiques
    routes = [
        {
            "rule": "/",
            "template": "index.html",
            "title": "A.N.A.N.A.S. | Accueil",
            "meta": "Portail géoservices basé sur des liens magnet et torrents.",
        },

        {
            "rule": "/contact",
            "template": "contact.html",
            "title": "A.N.A.N.A.S. | Contact",
            "meta": "Contactez-nous pour toute question ou suggestion.",
        },
    ]

    # Enregistrement dynamique des routes
    from src import _register_view, _legacy_catalogue, register_all_blueprints

    for route_cfg in routes:
        rule = route_cfg["rule"]
        endpoint = rule.lstrip("/") or "home"
        _register_view(app, rule, route_cfg["template"], route_cfg["title"], route_cfg["meta"])

    # Enregistrer tous les blueprints (catalogue convertisseur + routes)
    register_all_blueprints(app)

    # Enregistrer les autres blueprints
    from src.auth_routes import bp as auth_bp
    from src.item_routes import bp as items_bp
    from src.interactions import bp as interactions_bp
    from src.organization_routes import bp as org_bp
    from src.admin_routes import bp as admin_bp
    from src.upload_routes import bp as upload_bp
    from src.user_routes import bp as user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(interactions_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(user_bp)

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
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app = create_app()
    app.run(debug=debug_mode)
