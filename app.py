import os
from flask import Flask, render_template, redirect, url_for
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

ITEMS_PER_PAGE = 30


def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE, catalogue="donnees", filter_verified=False, org_slug=None):
    from models import Item, Organization

    type_map = {
        "donnees": "geodonnee",
        "cartes": "carte",
        "applications": "application"
    }
    item_type = type_map[catalogue]

    query = Item.query.filter_by(type=item_type)
    if org_slug:
        org = Organization.query.filter_by(slug=org_slug).first()
        if org:
            query = query.filter_by(organization_id=org.id)
    if filter_verified:
        query = query.filter_by(verification_status="verified")
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    if total_page > total_pages or total_page < 1:
        return None

    items = query.offset((total_page - 1) * per_page).limit(per_page).all()

    result_items = [item.to_dict() for item in items]
    page_numbers = _build_page_numbers(total_page, total_pages)

    return {
        "items": result_items,
        "page": total_page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }


def _build_page_numbers(current, total):
    if total <= 7:
        return list(range(1, total + 1))

    pages = []
    if current <= 4:
        pages.extend([1, 2, 3, 4])
        pages.append("...")
        pages.append(total)
    elif current > (total - 5):
        pages.append(1)
        pages.append("...")
        pages.extend(range(total - 3, total + 1))
    else:
        pages.append(1)
        pages.append("...")
        pages.extend(range(current - 1, current + 2))
        pages.append("...")
        pages.append(total)
    return pages


class Config:
    """Configuration de l'application."""

    def __init__(self):
        self.SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")

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


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    from models import Item, Organization

    app = Flask(__name__, template_folder="templates")

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Activation globale de la protection CSRF (nécessite une clé secrète)
    csrf = CSRFProtect(app)

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

    # Catalogue routes (donnees, cartes, applications)
    _CATALOGUE_META = {
        "donnees": {
            "title_prefix": "Catalogue des géodonnées",
            "meta": "Parcourez le catalogue complet des géodonnées A.N.A.N.A.S.",
        },
        "cartes": {
            "title_prefix": "Catalogue des cartes",
            "meta": "Explorez la collection de cartes et produits cartographiques A.N.A.N.A.S.",
        },
        "applications": {
            "title_prefix": "Catalogue d'applications",
            "meta": "Découvrez les applications et services web géospatiaux A.N.A.N.A.S.",
        },
    }

    type_map = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}

    def catalogue_view(catalogue="donnees", page=1):
        if catalogue not in type_map:
            return redirect(url_for("catalogue"))
        if page < 1:
            return redirect(url_for("catalogue", catalogue=catalogue, page=1))
        meta = _CATALOGUE_META[catalogue]
        data = get_catalogue_page(page, catalogue=catalogue)
        if data is None:
            return redirect(url_for("catalogue", catalogue=catalogue, page=1))
        return render_template(
            "catalogue.html",
            title=f"A.N.A.N.A.S. | {meta['title_prefix']} — Page {page}",
            meta_description=meta["meta"],
            catalogue_type=catalogue,
            **data,
        )

    app.add_url_rule("/catalogue", endpoint="catalogue", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/donnees", endpoint="catalogue_donnees", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/cartes", endpoint="catalogue_cartes", view_func=lambda catalogue="cartes", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/applications", endpoint="catalogue_apps", view_func=lambda catalogue="applications", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/<int:page>", endpoint="catalogue_page", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/donnees/<int:page>", endpoint="catalogue_donnees_page", view_func=lambda catalogue="donnees", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/cartes/<int:page>", endpoint="catalogue_cartes_page", view_func=lambda catalogue="cartes", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/applications/<int:page>", endpoint="catalogue_apps_page", view_func=lambda catalogue="applications", page=1: catalogue_view(catalogue=catalogue, page=page))

    # ────────────────────────────────────────────
    #  Favicon (silently ignore requests)
    # ────────────────────────────────────────────
    @app.route("/favicon.ico")
    def favicon_route():
        return "", 204

    # Item detail route
    def item_detail_view(item_id):
        item = Item.query.get_or_404(item_id)
        related_items = Item.query.filter(
            Item.format_type == item.format_type,
            Item.id != item_id,
            Item.is_published == True
        ).limit(3).all()

        img_gallery = [g for g in item.gallery_items if g.media_type == "image"]

        return render_template(
            "item_detail.html",
            title=f"A.N.A.N.A.S. | {item.title}",
            meta_description=item.description[:160],
            item=item.to_dict(),
            related_items=[ri.to_dict() for ri in related_items],
            image_gallery=img_gallery,
        )

    app.add_url_rule("/catalogue/item/<int:item_id>", endpoint="item_detail", view_func=item_detail_view)

    # Standalone gallery page
    def item_gallery_view(item_id):
        item = Item.query.get_or_404(item_id)
        return render_template(
            "gallery.html",
            title=f"Galerie — {item.title}",
            meta_description="Galerie de " + item.title,
            item=item.to_dict(),
        )

    app.add_url_rule("/catalogue/item/<int:item_id>/gallery", endpoint="item_gallery", view_func=item_gallery_view)

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
