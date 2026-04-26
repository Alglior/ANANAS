import os
from flask import Flask, render_template
from flask_wtf import CSRFProtect


class Config:
    """Configuration de l'application."""
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    def __init__(self):
        # Si aucune clé n'est configurée, lecture du fichier .secret
        if not self.SECRET_KEY and os.path.isfile(".secret"):
            with open(".secret", "r") as f:
                for line in f:
                    if line.startswith("FLASK_SECRET_KEY="):
                        # Safe partition instead of hardcoded index slicing
                        self.SECRET_KEY = line.partition("=")[2].strip()
                        break

    def validate(self):
        """Valider la clé et garantir sa robustesse."""
        # Correction automatique des clés faibles (inférieures à 32 caractères)
        if len(self.SECRET_KEY) < 32:
            self.SECRET_KEY = _generate_secret_key()

        # En mode production, l'application bloque si aucune clé valide n'est trouvée
        if not self.SECRET_KEY and os.environ.get("FLASK_ENV", "development") == "production":
            raise ValueError(
                "CRITICAL: No secret key configured! Set FLASK_SECRET_KEY in your environment or provide a valid .secret file."
            )


def _generate_secret_key():
    """Générer une clé secrète de 32 octets et sauvegarder dans le fichier .secret."""
    import secrets

    key = secrets.token_hex(32)
    with open(".secret", "w") as f:
        f.write(f"FLASK_SECRET_KEY={key}\n")
    os.chmod(".secret", 0o600)
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
        return response

    # Configuration des cookies sécurisés (par défaut désactivé pour le HTTP local)
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Empêche les scripts JavaScript de lire le cookie de session
    app.config["SESSION_EXPIRED_SECONDS"] = 3600   # Les sessions expireront automatiquement après 1 heure

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
