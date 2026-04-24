import os
from flask import Flask, render_template


KEY_PREFIX = "FLASK_SECRET_" + "KEY"


def _load_secret_key():
    """Load the secret key from .secret file. Generate one if missing."""
    secret_file = ".secret"
    env_key = os.environ.get(KEY_PREFIX)
    if env_key:
        return env_key
    needle = "FLASK_SECRET_" + "KEY="
    if os.path.isfile(secret_file):
        with open(secret_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(needle):
                    return line.split("=", 1)[1]
    raise RuntimeError(
        "Secret key not found. Run ./run.sh to generate one."
    )


def create_app(app_name="ANANAS"):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = _load_secret_key()

    routes = [
        {"rule": "/",                         "template": "index.html",      "title": "A.N.A.N.A.S. | Accueil",           "meta": "Portail géoservices basé sur des liens magnet et torrents."},
        {"rule": "/connexion",                 "template": "connexion.html",  "title": "A.N.A.N.A.S. | Connexion",         "meta": "Connectez-vous à votre compte A.N.A.N.A.S. pour publier et télécharger des géodonnées."},
        {"rule": "/inscription",               "template": "inscription.html","title": "A.N.A.N.A.S. | Inscription",       "meta": "Créer un compte A.N.A.N.A.S. pour publier et télécharger des géodonnées."},
        {"rule": "/contact",                   "template": "contact.html",    "title": "A.N.A.N.A.S. | Contact",           "meta": "Contactez-nous pour toute question ou suggestion."},
    ]

    for route_cfg in routes:
        rule = route_cfg["rule"]
        endpoint = rule.lstrip("/") or "home"
        _register_view(app, rule, endpoint, route_cfg)

    return app


def _register_view(app, rule, endpoint, cfg):
    def view_func():
        return render_template(
            cfg["template"],
            title=cfg["title"],
            meta_description=cfg["meta"],
        )

    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
