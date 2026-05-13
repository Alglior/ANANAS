import os

SECRET_FILE = ".secret"

from flask import Flask, render_template, redirect, url_for
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# ────────────────────────────────────────────
#  Catalogue Items (mock data — replace with DB)
# ────────────────────────────────────────────
ITEMS_PER_PAGE = 30

_CATALOGUE_ITEMS = []
LOREM_IPSUM_FR = [
    "Données topographiques détaillées couvrant une zone rurale avec des informations altimétriques précises, incluant les courbes de niveau et les modèles numériques d'élévation. Ce jeu de données a été acquis par photogrammétrie aérienne à bord d'un aéronef non piloté utilisant un système de positionnement global différentiel pour la géolocalisation de chaque cliché. La précision planimétrique atteint 1,2 mètre et l'altitude est déterminée avec une erreur verticale inférieure à 0,8 mètre selon les standards du service public d'information géographique.",
    "Couche SIG administrative avec limites territoriales complètes pour les régions françaises, incluant les codes INSEE et les centres-bourgs principaux de chaque commune. La base de données est mise à jour trimestriellement en collaboration avec les services de l'État et la DGFiP. Elle contient plus de 35 000 entités administratives classées par ordre croissant de niveau hiérarchique : régions, départements, arrondissements, cantons et communes.",
    "Imagerie satellite multispectrale haute résolution avec classification automatique des types d'occupation du sol selon la méthodologie CORINE Land Cover. Les acquisitions ont été réalisées sur trois dates distinctes entre mai et octobre pour couvrir les variations saisonnières de la végétation. Le processus de classification supervisée utilise l'algorithme Random Forest entraîné sur 500 surfaces de contrôle terrain validées par des experts.",
    "Réseau hydrographique vectorisé avec attribution hydraulique complète — pentes, débits moyens, classes de rivière et régime des cours d'eau permanents ou temporaires. La source primaire provient de l'analyse SIG du modèle numérique de terrain résolu à 1 mètre produit par la BD ALTI nationale. Chaque tronçon est associé à une classe hydrographique selon la nomenclature du SANDRE et un indice hiérarchique Strahler calculé automatiquement.",
    "Données pédologiques régionalisées avec profiling sur terrain incluant profils horizontaux, propriétés chimiques et classification selon la référence française SSD. Plus de 1200 points d'observation ont été relevés entre 2022 et 2024 avec un espacement moyen de 1 observation par 5 kilomètres carrées. Les paramètres mesurés comprennent le pH eau, la teneur en carbone organique, les granulométries fraction sable limon argile et la profondeur effective du sol.",
    "Orthophotographie Aigée 15 cm par pixel acquise en été, géoréférencée RGF13/IgG69, radiométriquement corrigée avec orthorectification fine pour cartographier les zones urbaines denses. La restitution a été effectuée à partir de images panchromatiques fusionnées avec le spectre multispectral pour produire un produit final 4 bandes couleurs rouge vert bleu infrarouge proche en 5 cm par pixel.",
    "Couverture forestière nationale issue de l'inventaire forestier du ministère chargé de l'Ecologie. Les données combinent l'imagerie aérienne LiDAR aéroporté et les observations terrain des stations permanentes réparties sur un quadrillage régulier de 8 km. L'altitude point LiDAR brute est filtrée puis classifiée en points sol végétation bâti selon la norme ASPRS LAS 1.7.",
    "Carte des zones inondables élaborée à partir des modèles hydrauliques HEC-RAS calés sur les crues historiques de référence décennale et centennale. Les altimétries sont intégrées depuis des levés topographiques terrestres et aéroportés par drone avec un contrôle qualité certifié ISO 17025.",
    "Réseau routier complet issu de la base nationale Routière à partir de traitements automatisés d'images aériennes validées terrain par les services du Ministère. Chaque segment contient l'indice hiérarchique, le nombre de voies, le revêtement, la vitesse autorisée et les informations fonctionnelles selon le standard SIG.",
    "Données démographiques agrégées par IRIS (IR分区 d'Repartition des Iris) pour les 52 millions d'habitants. La population municipale, la population totale et les indicateurs socio-économiques sont actualisés annuellement depuis les recensements INSEE décentralisés avec un report tous les cinq ans.",
]

_AUTHOR_NAMES = [
    "Jean Dupont", "Marie Laurent", "Pierre Martin",
    "Sophie Durand", "Nicolas Moreau", "Isabelle Petit",
    "François Le Gall", "Catherine Rousseau", "Philippe Simon",
    "Françoise Bonnet", "Jacques Blanc", "Émilie Garnier",
    "Jean-Pierre Rivière", "Anne Charpentier", "Bernard Leroy",
    "Nathalie Roux", "Laurent David", "Valérie Thomas",
    "Sylvain Dumas", "Corinne Michel",
]

import hashlib

def _pseudo_date(seed, start_year=2022, end_year=2025):
    h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16)
    year_start = h % (end_year - start_year + 1) + start_year
    month = (h >> 8) % 12 + 1
    day = (h >> 16) % 28 + 1
    return f"{year_start}-{month:02d}-{day:02d}"

_GALLERY_IMAGES = [
    "/static/images/gallery/map-{}.png",
    "/static/images/gallery/carte-{}.svg",
]

def _build_gallery_item(item_id):
    fmt = item_id % 3
    types = {0: ["image", "csv"], 1: ["dashboard", "interactive_map"], 2: ["image", "interactive_map"]}
    gallery = []
    base_labels = [
        "Vue cartographique générale",
        "Couche SIG brute",
        "Extraction CSV analysée",
        "Tableau de bord thématique",
        "Carte interactive zoomable",
        "Données brutes visualisées",
        "Orthophoto annotée",
        "Rendu cartographique final",
    ]
    n = 7 + (item_id % 4)
    for j in range(1, n + 1):
        media_type = types[fmt][(j - 1) % len(types[fmt])]
        label = base_labels[(j - 1) % len(base_labels)]
        if media_type == "image":
            gallery.append({"type": "image", "src": f"/static/images/gallery/map-{(item_id % 5) + 1}.svg", "label": label})
        elif media_type == "csv":
            csv_data = [
                ["id", "nom", "valeur"],
                ["1", f"Zone_{j}", str(item_id * j)],
                ["2", f"Segment_{j}_N", str(item_id + j * 0.5)],
                ["3", f"Segment_{j}_S", str(item_id - j)],
                ["4", f"Nœud_{j}", str(j * 100 + item_id)],
            ]
            gallery.append({"type": "csv", "data": csv_data, "label": label})
        elif media_type == "dashboard":
            dash_data = [
                {"metric": "Superficie (ha)", "value": f"{item_id * 127 + 43}"},
                {"metric": "Couverts (%)", "value": f"{(item_id * 13) % 60 + 25}%"},
                {"metric": "Points ({% raw %}{% endraw %}N)", "value": str(item_id * 847)},
                {"metric": "Densité (/km²)", "value": f"{item_id / 3:.2f}"},
            ]
            gallery.append({"type": "dashboard", "metrics": dash_data, "label": label})
        elif media_type == "interactive_map":
            gallery.append({"type": "interactive_map", "id": f"map-gallery-{item_id}", "label": label})
    return gallery

for i in range(1, 201):
    format_name = ["Shapefile", "GeoJSON", "GeoPackage"][i % 3]
    tags = []
    if i % 5 == 0:
        tags.extend(["topographie", "altimétrie"])
    elif i % 4 == 0:
        tags.extend(["hydrologie", "réseau"])
    elif i % 3 == 0:
        tags.extend(["occupation du sol", "classification"])
    elif i % 7 == 0:
        tags.extend(["administratif", "communes"])
    else:
        tags = ["donnée", format_name]

    _CATALOGUE_ITEMS.append({
        "id": i,
        "title": f"Géodonnée {i:04d}",
        "description": f"{LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)]}",
        "format": format_name,
        "size": f"{(i * 17) % 500 + 10} Mo",
        "magnet": f"magnet:?xt=urn:btih:{i:032d}",
        "image": "/static/images/logo/ANANAS.png",
        "author": _AUTHOR_NAMES[i % len(_AUTHOR_NAMES)],
        "created_at": _pseudo_date(i),
        "tags": tags,
        "gallery": _build_gallery_item(i),
        "pdf_doc": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/r6.pdf",
    })

_CARTES_ITEMS = []
_MAP_FORMATS = ["Carte raster", "Carte vectorielle", "SIG interactif", "Orthophoto"]
_MAP_TITLES = [
    "Carte bathymétrique des fonds marins",
    "Atlas géologique du territoire national",
    "Carte d'aléa sismique régionale",
    "Couverture orthophotographique aérienne",
    "Carte topographique au 1:25000",
    "Map des zones de protection environnementale",
    "Relevé cartographique LiDAR haute résolution",
    "Carte géomorphologique structurale",
    "Couche SIG administrative régionale",
    "Mosaïque satellite multispectrale",
]

for i in range(1, 201):
    format_name = _MAP_FORMATS[i % len(_MAP_FORMATS)]
    title = f"{_MAP_TITLES[i % len(_MAP_TITLES)]} — Secteur {i:04d}"
    tags = []
    if i % 5 == 0:
        tags.extend(["cartographie", "topographie"])
    elif i % 4 == 0:
        tags.extend(["SIG", "vectoriel"])
    elif i % 3 == 0:
        tags.extend(["raster", "satellite"])
    else:
        tags = ["carte", format_name]

    _CARTES_ITEMS.append({
        "id": i,
        "title": title,
        "description": f"{LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)]}",
        "format": format_name,
        "size": f"{(i * 17) % 500 + 10} Mo",
        "magnet": f"magnet:?xt=urn:btih:{i:032d}",
        "image": "/static/images/logo/ANANAS.png",
        "author": _AUTHOR_NAMES[i % len(_AUTHOR_NAMES)],
        "created_at": _pseudo_date(i + 500),
        "tags": tags,
        "gallery": _build_gallery_item(i),
        "pdf_doc": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/r6.pdf",
    })

_APPS_ITEMS = []
_APP_TYPES = ["Web App", "Dashboard", "Microservice", "API REST"]
_APP_NAMES = [
    "Visualiseur cartographique en ligne",
    "Application de traitement SIG batch",
    "Portail d'échange de données géographiques",
    "Système de gestion des alertes environnementales",
    "Outil d'analyse spatiale multi-couches",
    "Plateforme de modélisation hydologique",
    "API de géocodage et reverse-geocodage",
    "Dashboard de surveillance territoriale",
    "Application mobile de collecte terrain",
    "Système de publication cartographique web",
]

for i in range(1, 201):
    app_type = _APP_TYPES[i % len(_APP_TYPES)]
    name = f"{_APP_NAMES[i % len(_APP_NAMES)]} — v{i // 10 + 1}.{i % 10}"
    tags = []
    if i % 5 == 0:
        tags.extend(["web", "visualisation"])
    elif i % 4 == 0:
        tags.extend(["api", "service"])
    elif i % 3 == 0:
        tags.extend(["dashboard", "analytique"])
    else:
        tags = ["application", app_type]

    _APPS_ITEMS.append({
        "id": i,
        "title": name,
        "description": f"{LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)]}",
        "format": app_type,
        "size": f"{(i * 17) % 500 + 10} Mo",
        "magnet": f"magnet:?xt=urn:btih:{i:032d}",
        "image": "/static/images/logo/ANANAS.png",
        "author": _AUTHOR_NAMES[i % len(_AUTHOR_NAMES)],
        "created_at": _pseudo_date(i + 1000),
        "tags": tags,
        "gallery": _build_gallery_item(i),
        "pdf_doc": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/r6.pdf",
    })

_ALL_CATALOGUES = {
    "donnees": _CATALOGUE_ITEMS,
    "cartes": _CARTES_ITEMS,
    "applications": _APPS_ITEMS,
}


def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE, catalogue="donnees"):
    """Retourne la page `total_page` d'items (1-indexed)."""
    items_list = _ALL_CATALOGUES[catalogue]
    items = items_list[(total_page - 1) * per_page: total_page * per_page]
    if not items:
        return None
    total_pages = (len(items_list) + per_page - 1) // per_page
    page_numbers = _build_page_numbers(total_page, total_pages)
    return {
        "items": items,
        "page": total_page,
        "per_page": per_page,
        "total_items": len(items_list),
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }


def _build_page_numbers(current, total):
    """Construit la liste des numéros à afficher (ex: [1, 2, 3, '...', 15])."""
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

    def catalogue_view(catalogue="donnees", page=1):
        if catalogue not in _ALL_CATALOGUES:
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

    app.add_url_rule("/catalogue", endpoint="catalogue", view_func=catalogue_view)
    app.add_url_rule("/catalogue/donnees", endpoint="catalogue_donnees", view_func=catalogue_view)
    app.add_url_rule("/catalogue/cartes", endpoint="catalogue_cartes", view_func=catalogue_view)
    app.add_url_rule("/catalogue/applications", endpoint="catalogue_apps", view_func=catalogue_view)
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
        item = None
        for items in _ALL_CATALOGUES.values():
            found = next((i for i in items if i["id"] == item_id), None)
            if found:
                item = found
                break
        if item is None:
            return redirect(url_for("catalogue"))
        related_items = []
        for catalog_items in _ALL_CATALOGUES.values():
            related_items.extend(
                i for i in catalog_items
                if i["format"] == item["format"] and i["id"] != item_id
            )
        related_items = related_items[:3]
        # Extract only image items from gallery for the inline gallery strip
        img_gallery = [g for g in item.get("gallery", []) if g["type"] == "image"]

        return render_template(
            "item_detail.html",
            title=f"A.N.A.N.A.S. | {item['title']}",
            meta_description=item["description"][:160],
            item=item,
            related_items=related_items,
            image_gallery=img_gallery,
        )

    app.add_url_rule("/catalogue/item/<int:item_id>", endpoint="item_detail", view_func=item_detail_view)

    # Standalone gallery page
    def item_gallery_view(item_id):
        item = None
        for items in _ALL_CATALOGUES.values():
            found = next((i for i in items if i["id"] == item_id), None)
            if found:
                item = found
                break
        if item is None:
            return redirect(url_for("catalogue"))
        return render_template(
            "gallery.html",
            title=f"Galerie — {item['title']}",
            meta_description="Galerie de " + item["title"],
            item=item,
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
