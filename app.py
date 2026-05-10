import os

SECRET_FILE = ".secret"

from flask import Flask, render_template, redirect, url_for
from flask_wtf import CSRFProtect

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
    _CATALOGUE_ITEMS.append({
        "id": i,
        "title": f"Géodonnée {i:04d}",
        "description": f"{LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)]}",
        "format": ["Shapefile", "GeoJSON", "GeoPackage"][i % 3],
        "size": f"{(i * 17) % 500 + 10} Mo",
        "magnet": f"magnet:?xt=urn:btih:{i:032d}",
        "image": "/static/images/logo/ANANAS.png",
        "author": _AUTHOR_NAMES[i % len(_AUTHOR_NAMES)],
        "created_at": _pseudo_date(i),
        "gallery": _build_gallery_item(i),
    })

def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE):
    """Retourne la page `total_page` d'items (1-indexed)."""
    items = _CATALOGUE_ITEMS[(total_page - 1) * per_page: total_page * per_page]
    if not items:
        return None
    total_pages = (len(_CATALOGUE_ITEMS) + per_page - 1) // per_page
    page_numbers = _build_page_numbers(total_page, total_pages)
    return {
        "items": items,
        "page": total_page,
        "per_page": per_page,
        "total_items": len(_CATALOGUE_ITEMS),
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

    # Catalogue route (supports pagination via <int:page>)
    def catalogue_view(page=1):
        if page < 1:
            return redirect(url_for("catalogue", page=1))
        data = get_catalogue_page(page)
        if data is None:
            return redirect(url_for("catalogue", page=1))
        return render_template(
            "catalogue.html",
            title=f"A.N.A.N.A.S. | Catalogue — Page {page}",
            meta_description="Parcourez le catalogue complet des géodonnées A.N.A.N.A.S.",
            **data,
        )

    app.add_url_rule("/catalogue", endpoint="catalogue", view_func=catalogue_view)
    app.add_url_rule("/catalogue/<int:page>", endpoint="catalogue_page", view_func=catalogue_view)

    # ────────────────────────────────────────────
    #  Favicon (silently ignore requests)
    # ────────────────────────────────────────────
    @app.route("/favicon.ico")
    def favicon_route():
        return "", 204

    # Item detail route
    def item_detail_view(item_id):
        item = next((i for i in _CATALOGUE_ITEMS if i["id"] == item_id), None)
        if item is None:
            return redirect(url_for("catalogue"))
        related_items = [
            i for i in _CATALOGUE_ITEMS
            if i["format"] == item["format"] and i["id"] != item_id
        ][:3]
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
        item = next((i for i in _CATALOGUE_ITEMS if i["id"] == item_id), None)
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
