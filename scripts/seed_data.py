import datetime
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Item, ItemTag, ItemGallery, DataChunk, Report, User


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


ZOOM_LEVELS = [1, 2, 4, 8, 16]
BAND_NAMES = ["Lambert II étendu", "Lambert III", "WGS84/UTM32"]
CHUNK_FORMATS = ["GeoTIFF", "NTF", "Shapefile zip", "GeoPackage", "E00"]

SYSTEM_USER_ID = None


def _ensure_system_user():
    global SYSTEM_USER_ID
    from models import User
    if not SYSTEM_USER_ID:
        try:
            from werkzeug.security import generate_password_hash
        except ImportError:
            generate_password_hash = lambda x: x
        admin_password = os.environ.get("ADMIN_PASSWORD", "system")
        user = User(
            prenom="Système", nom="ANANAS",
            email="system@ananas.local",
            password_hash=generate_password_hash(admin_password),
            is_active=True, banned=False, is_admin=True
        )
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            existing = db.session.execute(
                db.select(User).filter(User.email == "system@ananas.local")
            ).scalar_one_or_none()
            if existing:
                SYSTEM_USER_ID = existing.id
                return
        SYSTEM_USER_ID = user.id


def _build_chunks(item_id, pack_title):
    _ensure_system_user()
    n_chunks = 3 + (item_id % 4)
    chunks = []
    for j in range(n_chunks):
        lvl = ZOOM_LEVELS[j % len(ZOOM_LEVELS)]
        band = BAND_NAMES[(j * item_id) % len(BAND_NAMES)]
        fmt = CHUNK_FORMATS[j % len(CHUNK_FORMATS)]
        chunk = DataChunk(
            parent_item_id=item_id,
            name=f"{pack_title}_L{lvl}_{band}",
            format_type=fmt,
            magnet_link=f"magnet:?xt=urn:btih:{item_id:032d}chunk{j:03d}",
            owner_user_id=SYSTEM_USER_ID,
        )

        chunks.append(chunk)
    return chunks


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


COMMENT_CONTENTS = [
    "Excellentes données, très précises et bien structurées. Merci pour le partage !",
    "J'ai utilisé ces données pour un projet de cartographie et les résultats sont convaincants. Bravo.",
    "Quelques petites erreurs dans l'attribut 'surface_ha', vérifiez les valeurs pour les zones 45 à 60.",
    "Format Shapefile impeccable, tout ouvre sans problème dans QGIS. Bien joué.",
    "Seriez-vous en mesure de fournir une version en GeoJSON ? Le Shapefile ne supporte pas bien les encodages UTF-8 complexes.",
    "Très utile pour la comparaison interannuelle que je prépare sur l'évolution du territoire régional.",
    "La résolution spatiale est令人叹为观止 (wow)! On voit clairement les détails de l'occupation du sol.",
    "Attention, le système de coordonnées indiqué ne correspond pas toujours à celui des données brutes.",
    "Merci pour ce travail minutieux. Serait-il possible d'ajouter la couche linéaire des cours d'eau ?",
    "J'ai croisé ces données avec le cadastre et les recoupements sont quasi parfaits — bravo.",
    "Données un peu anciennes (2022) mais toujours pertinentes pour l'échelle de mon étude.",
    "Les métadonnées sont bien documentées, c'est rare et ça fait plaisir !",
    "Le format GeoPackage serait plus performant pour les gros volumes. À envisager pour la prochaine version.",
    "J'ai testé sur le secteur sud — pas de problème détecté pour l'heure. Je reviendrai vers vous si besoin.",
    "Cette ressource a considérablement accéléré notre rapport annuel. Merci infiniment à l'auteur.",
    "On regrette l'absence d'un indicateur de confiance / qualité par valeur, pourtant essentiel pour les analyses quantitatives.",
    "Parfait pour alimenter le dashboard du service urbanisme. Le partage est vraiment bénéfique pour tous.",
    "Petit bémol sur la cohérence des codes INSEE dans la table attributaire — quelques coquilles à corriger.",
    "Données hydro : le débit moyen semble sous-estimé de 15% par rapport aux relevés Sandre. À vérifier ?",
    "Excellente couverture orthophoto, bien plus précise que celle disponible en open source. Merci !",
]

COMMENT_AUTHORS = [
    "Lucas Dubois", "Marie Laurent", "Pierre Martin", "Sophie Durand",
    "Nicolas Moreau", "Isabelle Petit", "Thomas Leroy", "Camille Roux",
    "Antoine Morel", "Léa Fournier", "Jules Girard", "Emma Bernard",
]

REPORT_REASONS = [
    "spam", "contenu_inapproprié", "fake_data", "other", "données_fausses",
    "harcèlement", "proposition_non_conforme", "contenu_suspect",
]
REPORT_DESCRIPTIONS = [
    "Signalement automatique détecté par le système de modération.",
    "L'utilisateur signalé a été accusé d'utiliser des données falsifiées.",
    "Ce rapport concerne un abus de confiance dans la communauté.",
    "La publication signalée semble contenir des informations trompeuses.",
    "Plusieurs utilisateurs ont déjà soumis un signalement similaire.",
    "Contenu potentiellement illégal ou non conforme aux conditions d'utilisation.",
    "Données publiées sans autorisation préalable du propriétaire initial.",
    "L'utilisateur signalé multiplie les tentatives de publication non vérifiée.",
    "Signalement lié à une activité suspecte de scraping ou de collecte massive.",
    "Publication ne respectant pas la charte qualité de la plateforme.",
]

REPORT_TYPES = ["user", "item_geodonnee", "item_carte", "item_application"]


def seed_reports():
    if db.session.execute(db.select(db.func.count()).select_from(Report)).scalar() > 0:
        print("Reports already exist. Skipping seeding.")
        return

    users = db.session.execute(
        db.select(User).order_by(User.id)
    ).scalars().all()

    items = db.session.execute(
        db.select(Item).order_by(Item.id)
    ).scalars().all()

    if len(users) < 5:
        print("Not enough users to seed reports (need at least 5). Skipping.")
        return

    admin_user = None
    for u in users:
        if u.is_admin:
            admin_user = u
            break

    items_by_type = {
        "item_geodonnee": [i.id for i in items if i.type == "geodonnee"],
        "item_carte": [i.id for i in items if i.type == "carte"],
        "item_application": [i.id for i in items if i.type == "application"],
    }

    reports_to_add = []
    n_reports = 50

    for i in range(1, n_reports + 1):
        reporter_id = users[i % len(users)].id
        reported_user_id = users[(i * 7) % len(users)].id
        report_type = REPORT_TYPES[i % len(REPORT_TYPES)]
        target_item_id = None

        if item_list := items_by_type.get(report_type):
            target_item_id = item_list[i % len(item_list)]

        reason = REPORT_REASONS[i % len(REPORT_REASONS)]
        description = REPORT_DESCRIPTIONS[i % len(REPORT_DESCRIPTIONS)]
        status = "pending" if i <= 35 else ("resolved" if i <= 42 else "dismissed")
        reviewed_by_id = admin_user.id if status != "pending" else None

        created_at = _pseudo_date(f"report_{i}")

        reviewed_at = None
        if reviewed_by_id:
            review_offset = i + 30
            reviewed_at = created_at + datetime.timedelta(days=review_offset % 30, hours=review_offset % 24)

        report = Report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            report_type=report_type,
            target_item_id=target_item_id,
            reason=reason,
            description=description,
            status=status,
            reviewed_by=reviewed_by_id,
            reviewed_at=reviewed_at,
            created_at=created_at,
        )
        reports_to_add.append(report)

    db.session.add_all(reports_to_add)
    try:
        db.session.commit()
        print(f"  Seed reports: {len(reports_to_add)} reports created (pending={sum(1 for r in reports_to_add if r.status == 'pending')}, resolved={sum(1 for r in reports_to_add if r.status == 'resolved')}, dismissed={sum(1 for r in reports_to_add if r.status == 'dismissed')})")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding reports: {e}")


def seed_comments():
    from models import Comment
    if db.session.execute(db.select(db.func.count()).select_from(Comment)).scalar() > 0:
        print("Comments already exist. Skipping seeding.")
        return

    items = db.session.execute(
        db.select(Item.id).order_by(Item.id)
    ).scalars().all()

    if not items:
        print("No items found to attach comments to. Skipping comment seeding.")
        return

    comments_to_add = []
    n_comments = 120
    for i in range(1, n_comments + 1):
        author = COMMENT_AUTHORS[i % len(COMMENT_AUTHORS)]
        item_id = items[(i * 3) % len(items)]
        content = COMMENT_CONTENTS[i % len(COMMENT_CONTENTS)]
        created_at = _pseudo_date(f"comment_{i}")

        comment = Comment(
            item_id=item_id,
            author_name=author,
            content=content,
            created_at=created_at,
        )
        comments_to_add.append(comment)

    db.session.add_all(comments_to_add)
    try:
        db.session.commit()
        print(f"  Seed comments: {len(comments_to_add)} comments created")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding comments: {e}")


def seed_items(category, count, type_val, title_fn, format_fn, is_pack=False):
    item_records = []
    gallery_idx = 1
    for i in range(1, count + 1):
        tags, fmt = format_fn(i)
        title = title_fn(i)
        author_idx = i % len(AUTHOR_NAMES)

        item = Item(
            type=type_val,
            title=title,
            description=LOREM_IPSUM_FR[i % len(LOREM_IPSUM_FR)],
            format_type=fmt if isinstance(fmt, str) else fmt[0] if isinstance(fmt, list) else "unknown",
            magnet_link=f"magnet:?xt=urn:btih:{i:032d}",
            image_path="/static/images/logo/ANANAS.png",
            author_name=AUTHOR_NAMES[author_idx],
            created_at=_pseudo_date(i),
        )
        if is_pack:
            item.data_format_level = "pack"
        db.session.add(item)
        item_records.append({"item": item, "title": title, "tags": tags})

    db.session.commit()

    for idx, rec in enumerate(item_records):
        item = rec["item"]
        for tag_str in (rec["tags"] if isinstance(rec["tags"], list) else []):
            db.session.add(ItemTag(item_id=item.id, tag=tag_str))

        if is_pack:
            chunks = _build_chunks(item.id, rec["title"])
            for chunk in chunks:
                db.session.add(chunk)

        gallery = _build_gallery(gallery_idx)
        gallery_idx += 1
        for g in gallery:
            gallery_entry = ItemGallery(
                item_id=item.id,
                media_type=g["type"],
                src=g.get("src"),
                data_json=g.get("data") or g.get("metrics"),
                label=g["label"],
            )
            db.session.add(gallery_entry)

    items_created = len(item_records)
    db.session.commit()
    print(f"  Seed {category}: {items_created} items done (ids={min(r['item'].id for r in item_records)}-{max(r['item'].id for r in item_records)})")


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
            for tbl in ["visualization_links", "reports", "ratings", "comments", "item_gallery", "item_tags", "user_uploads", "data_chunks"]:
                db.session.execute(db.table(tbl).delete())
            db.session.execute(db.table("items").delete())
            db.session.commit()

        print("Seeding sample data...\n")

        PACK_TITLES = [
            "Pack Regional Hauts-de-France",
            "Pack Metropolitan France LIDAR",
            "Pack Donnees OpenStreetMap FR",
            "Pack Orthophoto Raster 25cm",
            "Pack BD ALTI Completa",
            "Pack SIG Administrative Entieres",
            "Pack Hydrographie SANDRE Global",
            "Pack Occupation Sol CORINE",
            "Pack Pedologie Reference France",
            "Pack Catastral Property Parcels",
        ]

        seed_items(
            category="donnees",
            count=100,
            type_val="geodonnee",
            title_fn=lambda i: f"Gedonnee {i:04d}",
            format_fn=lambda i: _get_tags("donnees", i),
        )

        seed_items(
            category="donnees packs",
            count=25,
            type_val="geodonnee",
            title_fn=lambda i: PACK_TITLES[(i - 1) % len(PACK_TITLES)],
            format_fn=lambda i: _get_tags("donnees", i + 50),
            is_pack=True,
        )

        seed_items(
            category="cartes",
            count=200,
            type_val="carte",
            title_fn=lambda i: f"{MAP_TITLES[i % len(MAP_TITLES)]} — Secteur {i:04d}",
            format_fn=lambda i: _get_tags("cartes", i),
        )

        seed_items(
            category="applications",
            count=200,
            type_val="application",
            title_fn=lambda i: f"{APP_NAMES[i % len(APP_NAMES)]} — v{i // 10 + 1}.{i % 10}",
            format_fn=lambda i: _get_tags("applications", i),
        )

        # Seed mock comments and reports
        seed_comments()
        seed_reports()

        total = db.session.execute(func.count(Item.id)).scalar()
        stmt = db.select(db.func.count()).where(Item.data_format_level == "pack")
        packs = db.session.execute(stmt).scalar()
        print(f"\nDone. Total items: {total}, Packs: {packs}")


if __name__ == "__main__":
    seed_all()
