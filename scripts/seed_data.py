import datetime
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Item, ItemTag, ItemGallery


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

AUTHOR_NAMES = [
    "Jean Dupont", "Marie Laurent", "Pierre Martin",
    "Sophie Durand", "Nicolas Moreau", "Isabelle Petit",
    "François Le Gall", "Catherine Rousseau", "Philippe Simon",
    "Françoise Bonnet", "Jacques Blanc", "Émilie Garnier",
    "Jean-Pierre Rivière", "Anne Charpentier", "Bernard Leroy",
    "Nathalie Roux", "Laurent David", "Valérie Thomas",
    "Sylvain Dumas", "Corinne Michel",
]

GALLERY_FORMATS = ["Shapefile", "GeoJSON", "GeoPackage"]
MAP_FORMATS = ["Carte raster", "Carte vectorielle", "SIG interactif", "Orthophoto"]
APP_TYPES = ["Web App", "Dashboard", "Microservice", "API REST"]
APP_NAMES = [
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

MAP_TITLES = [
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


def _pseudo_date(seed, start_year=2022, end_year=2025):
    h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16)
    year_start = h % (end_year - start_year + 1) + start_year
    month = (h >> 8) % 12 + 1
    day = (h >> 16) % 28 + 1
    return datetime.datetime(year_start, month, day)


def _get_tags(category, i):
    if category == "donnees":
        fmt = GALLERY_FORMATS[i % 3]
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
            tags = ["donnée", fmt]
        return tags, fmt

    if category == "cartes":
        fmt = MAP_FORMATS[i % len(MAP_FORMATS)]
        tags = []
        if i % 5 == 0:
            tags.extend(["cartographie", "topographie"])
        elif i % 4 == 0:
            tags.extend(["SIG", "vectoriel"])
        elif i % 3 == 0:
            tags.extend(["raster", "satellite"])
        else:
            tags = ["carte", fmt]
        return tags, fmt

    if category == "applications":
        app_type = APP_TYPES[i % len(APP_TYPES)]
        tags = []
        if i % 5 == 0:
            tags.extend(["web", "visualisation"])
        elif i % 4 == 0:
            tags.extend(["api", "service"])
        elif i % 3 == 0:
            tags.extend(["dashboard", "analytique"])
        else:
            tags = ["application", app_type]
        return tags, app_type


def _build_gallery(item_id):
    fmt = item_id % 3
    types = {0: ["image", "csv"], 1: ["dashboard", "interactive_map"], 2: ["image", "interactive_map"]}
    gallery = []
    base_labels = [
        "Vue cartographique générale", "Couche SIG brute", "Extraction CSV analysée",
        "Tableau de bord thématique", "Carte interactive zoomable",
        "Données brutes visualisées", "Orthophoto annotée", "Rendu cartographique final",
    ]
    n = 7 + (item_id % 4)
    for j in range(1, n + 1):
        media_type = types[fmt][(j - 1) % len(types[fmt])]
        label = base_labels[(j - 1) % len(base_labels)]
        if media_type == "image":
            gallery.append({
                "type": "image",
                "src": f"/static/images/gallery/map-{(item_id % 5) + 1}.svg",
                "label": label,
            })
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


def seed_items(category, count, type_val, title_fn, format_fn, id_offset=0):
    items_created = 0
    for i in range(1, count + 1):
        actual_id = i + id_offset
        tags, fmt = format_fn(i)
        title = title_fn(i)
        author_idx = i % len(AUTHOR_NAMES)

        item = Item(
            type=type_val,
            title=title,
            description=LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)],
            format_type=fmt if isinstance(fmt, str) else fmt[0] if isinstance(fmt, list) else "unknown",
            size_mb=(i * 17) % 500 + 10,
            magnet_link=f"magnet:?xt=urn:btih:{actual_id:032d}",
            image_path="/static/images/logo/ANANAS.png",
            author_name=AUTHOR_NAMES[author_idx],
            created_at=_pseudo_date(i),
        )
        db.session.add(item)
        db.session.flush()

        for tag in tags:
            db.session.add(ItemTag(item_id=item.id, tag=tag))

        gallery = _build_gallery(actual_id)
        for g in gallery:
            gallery_entry = ItemGallery(
                item_id=item.id,
                media_type=g["type"],
                src=g.get("src"),
                data_json=g.get("data") or g.get("metrics"),
                label=g["label"],
            )
            db.session.add(gallery_entry)

        items_created += 1
        if items_created % 50 == 0:
            db.session.commit()
            print(f"  Seed {category}: {min(items_created, count)} items committed")

    db.session.commit()
    print(f"  Seed {category}: {items_created} items done")


def seed_all():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            print("Creating database tables...")
            db.create_all()
            print("Tables created.\n")
        else:
            print(f"Tables found: {', '.join(existing_tables)}\n")

        from sqlalchemy import func
        before = db.session.execute(func.count(Item.id)).scalar()
        print(f"Items before seeding: {before}\n")

        if before > 0:
            print(f"Clearing existing {before} items...")
            db.session.execute(db.table("item_gallery").delete())
            db.session.execute(db.table("item_tags").delete())
            db.session.execute(db.table("items").delete())
            db.session.commit()

        print("Seeding sample data...\n")

        seed_items(
            category="donnees",
            count=200,
            type_val="geodonnee",
            title_fn=lambda i: f"Géodonnée {i:04d}",
            format_fn=lambda i: _get_tags("donnees", i),
        )

        seed_items(
            category="cartes",
            count=200,
            type_val="carte",
            title_fn=lambda i: f"{MAP_TITLES[i % len(MAP_TITLES)]} — Secteur {i:04d}",
            format_fn=lambda i: _get_tags("cartes", i),
            id_offset=200,
        )

        seed_items(
            category="applications",
            count=200,
            type_val="application",
            title_fn=lambda i: f"{APP_NAMES[i % len(APP_NAMES)]} — v{i // 10 + 1}.{i % 10}",
            format_fn=lambda i: _get_tags("applications", i),
            id_offset=400,
        )

        total = db.session.execute(func.count(Item.id)).scalar()
        print(f"\nDone. Total items in database: {total}")


if __name__ == "__main__":
    seed_all()
