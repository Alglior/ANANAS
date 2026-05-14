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


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    app = Flask(__name__, template_folder="templates")

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Activation globale de la protection CSRF (nécessite une clé secrète)
    csrf = CSRFProtect(app)

    # Rate limiting pour prévenir le brute-force sur les routes d'authentification
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per hour"]
    )

    # ────────────────────────────────────────────
    #  Database setup
    # ────────────────────────────────────────────
    db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri:
        pg_user = os.environ.get("POSTGRES_USER", "ananas_user")
        pg_pass = os.environ.get("POSTGRES_PASSWORD", "password")
        pg_host = os.environ.get("POSTGRES_HOST", "postgres")
        pg_db = os.environ.get("POSTGRES_DB", "ananas")
        db_uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db=db)

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    # ────────────────────────────────────────────
    #  Security Headers & Cookie Settings
    # ────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com https://unpkg.com; "
            "script-src 'self' https://unpkg.com; "
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
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # Les sessions expireront après 1 heure (clé correcte Flask)

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(interactions_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)

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
