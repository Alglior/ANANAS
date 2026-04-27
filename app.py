import os

SECRET_FILE = ".secret"

from flask import Flask, render_template
from flask_wtf import CSRFProtect


class Config:
    """Configuration de l'application."""
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")

    def __init__(self):
        # Si aucune clé n'est configurée, lecture du fichier SECRET_FILE
        if not self.SECRET_KEY and os.path.isfile(SECRET_FILE):
            with open(SECRET_FILE, "r") as f:
                for line in f:
                    if line.startswith("FLASK_SECRET_KEY="):
                        _, _, key = line.partition("=")
                        self.SECRET_KEY = key.strip()
                        break

    def validate(self):
        """Valider la clé et garantir sa robustesse."""
        is_production = os.environ.get("FLASK_ENV", "development") == "production"
        
        # Si aucune clé n'est trouvée ou si elle est trop courte (< 32 chars)
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            if is_production:
                raise ValueError(
                    "CRITICAL: No secret key configured! Set FLASK_SECRET_KEY in your environment or provide a valid .secret file."
                )
            else:
                # En développement, générer une nouvelle clé
                self.SECRET_KEY = _generate_secret_key()


def _generate_secret_key():
    """Générer une clé secrète de 32 octets et sauvegarder dans le fichier SECRET_FILE."""
    import secrets

    key = secrets.token_hex(32)
    with open(SECRET_FILE, "w") as f:
        f.write(f"FLASK_SECRET_KEY={key}\n")
    os.chmod(SECRET_FILE, 0o600)
    return key


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    app = Flask(__name__, template_folder="templates")

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Activation globale de la protection CSRF (nécessite une clé secrète)
    csrf = CSRFProtect(app)

    # ────────────────────────────────────────────
    #  Security Headers & Cookie Settings
    # ────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; img-src 'self' data:;"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Configuration des cookies sécurisés
    # Déterminer si on est en production
    is_production = os.environ.get("FLASK_ENV", "development") == "production"
    
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Empêche les scripts JavaScript de lire le cookie de session
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Protection contre les attaques CSRF par cookie
    app.config["SESSION_COOKIE_SECURE"] = is_production  # En production seulement, force HTTPS pour les cookies
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # Les sessions expireront après 1 heure (clé correcte Flask)

    # Définition des routes
    routes = [
        {
            "rule": "/",
            "template": "index.html",
            "title": "A.N.A.N.A.S. | Accueil",
            "meta": "Portail géoservices basé sur des liens magnet et torrents.",
        },
        {
            "rule": "/connexion",
            "template": "connexion.html",
            "title": "A.N.A.N.A.S. | Connexion",
            "meta": "Connectez-vous à votre compte A.N.A.N.A.S. pour publier et télécharger des géodonnées.",
        },
        {
            "rule": "/inscription",
            "template": "inscription.html",
            "title": "A.N.A.N.A.S. | Inscription",
            "meta": "Créer un compte A.N.A.N.A.S. pour publier et télécharger des géodonnées.",
        },
        {
            "rule": "/contact",
            "template": "contact.html",
            "title": "A.N.A.N.A.S. | Contact",
            "meta": "Contactez-nous pour toute question ou suggestion.",
        },
    ]

    # Enregistrement dynamique des routes
    for route_cfg in routes:
        rule = route_cfg["rule"]
        endpoint = rule.lstrip("/") or "home"
        _register_view(app, rule, endpoint, route_cfg)

    return app


def _register_view(app: Flask, rule: str, endpoint: str, cfg: dict):
    """Enregistrer une fonction de vue avec un nom d'extrémité (endpoint) unique."""

    def view_func():
        return render_template(
            cfg["template"],
            title=cfg["title"],
            meta_description=cfg["meta"],
        )

    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)


# ────────────────────────────────────────────
#  Local dev runner
# ────────────────────────────────────────────
if __name__ == "__main__":
    # En production, la clé secrète est généralement configurée via des variables d'environnement.
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app = create_app()
    app.run(debug=debug_mode)
