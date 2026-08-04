from flask import request, jsonify, render_template, current_app
from app import db
from src.admin import bp, login_required, require_admin, api_admin_required, _log_audit
from models import SiteSetting

_DEFAULT_SETTINGS = {
    "items_per_page": "30",
    "comments_per_page": "10",
    "catalogue_per_page": "20",
    "site_name": "A.N.A.N.A.S",
    "site_subtitle": "Atlas Numérique d'Archives de Nœuds et d'Accès Synchronisés",
    "site_logo": "/static/images/logo/ANANAS.png",
    "site_favicon": "/static/images/logo/ANANAS.ico",
    "enable_registration": "true",
    "maintenance_mode": "false",
    "home_eyebrow": "Partage de données géospatiales",
    "home_hero_title": "Partagez vos géodonnées avec des torrents vérifiés",
    "home_hero_subtitle": "A.N.A.N.A.S permet de partager et télécharger des données géographiques. Vérification d'intégrité et accès rapide.",
    "home_show_mirrors": "true",
    "home_show_geopackages": "true",
    "home_show_featured": "true",
    "home_show_simple_files": "true",
    "catalogue_donnees_title": "Catalogue des géodonnées",
    "catalogue_cartes_title": "Catalogue des cartes",
    "catalogue_applications_title": "Catalogue d'applications",
}

_SETTING_META = [
    {"key": "items_per_page", "label": "Éléments par page (catalogue)", "type": "number", "default": "30", "help": "Nombre d'éléments affichés par page dans le catalogue principal."},
    {"key": "comments_per_page", "label": "Commentaires par page", "type": "number", "default": "10", "help": "Nombre de commentaires visibles par page sur la fiche d'un item."},
    {"key": "catalogue_per_page", "label": "Éléments par page (JSON)", "type": "number", "default": "20", "help": "Nombre d'éléments retournés par requête JSON (API catalogue)."},
    {"key": "site_name", "label": "Nom du site", "type": "text", "default": "A.N.A.N.A.S", "help": "Nom affiché dans l'onglet du navigateur, l'en-tête et le pied de page."},
    {"key": "site_subtitle", "label": "Sous-titre du site", "type": "text", "default": "Atlas Numérique d'Archives de Nœuds et d'Accès Synchronisés", "help": "Sous-titre affiché sous le logo dans l'en-tête."},
    {"key": "enable_registration", "label": "Inscriptions ouvertes", "type": "boolean", "default": "true", "help": "Permet aux nouveaux visiteurs de créer un compte. Désactiver pour limiter l'accès aux membres existants."},
    {"key": "maintenance_mode", "label": "Mode maintenance", "type": "boolean", "default": "false", "help": "Affiche une page de maintenance aux visiteurs non-administrateurs."},
    {"key": "", "label": "─ Page d'accueil ─", "type": "separator", "default": ""},
    {"key": "home_eyebrow", "label": "Accueil — Sur-titre (eyebrow)", "type": "text", "default": "Partage de données géospatiales", "help": "Texte discret affiché au-dessus du titre principal sur la page d'accueil."},
    {"key": "home_hero_title", "label": "Accueil — Titre principal", "type": "text", "default": "Partagez vos géodonnées avec des torrents vérifiés", "help": "Grand titre visible sur la bannière de la page d'accueil."},
    {"key": "home_hero_subtitle", "label": "Accueil — Sous-titre", "type": "text", "default": "A.N.A.N.A.S permet de partager et télécharger des données géographiques...", "help": "Sous-titre affiché sous le titre principal sur la page d'accueil."},
    {"key": "home_show_mirrors", "label": "Accueil — Afficher sites miroirs", "type": "boolean", "default": "true", "help": "Affiche la section des sites miroirs sur la page d'accueil."},
    {"key": "home_show_geopackages", "label": "Accueil — Afficher packs GeoPackage", "type": "boolean", "default": "true", "help": "Affiche la section des packs GeoPackage sur la page d'accueil."},
    {"key": "home_show_featured", "label": "Accueil — Afficher données en avant", "type": "boolean", "default": "true", "help": "Affiche la section des données mises en avant sur la page d'accueil."},
    {"key": "home_show_simple_files", "label": "Accueil — Afficher fichiers simples", "type": "boolean", "default": "true", "help": "Affiche la section des fichiers simples sur la page d'accueil."},
    {"key": "", "label": "─ Catalogue ─", "type": "separator", "default": ""},
    {"key": "catalogue_donnees_title", "label": "Catalogue — Titre géodonnées", "type": "text", "default": "Catalogue des géodonnées", "help": "Titre de l'onglet/encart du catalogue des géodonnées."},
    {"key": "catalogue_cartes_title", "label": "Catalogue — Titre cartes", "type": "text", "default": "Catalogue des cartes", "help": "Titre de l'onglet/encart du catalogue des cartes."},
    {"key": "catalogue_applications_title", "label": "Catalogue — Titre applications", "type": "text", "default": "Catalogue d'applications", "help": "Titre de l'onglet/encart du catalogue des applications."},
]


def _ensure_table():
    try:
        SiteSetting.__table__.create(db.engine, checkfirst=True)
    except Exception:
        current_app.logger.exception("Failed to ensure settings table")


def get_setting(key, default=None):
    _ensure_table()
    try:
        row = SiteSetting.query.filter_by(key=key).first()
        if row is None:
            return _DEFAULT_SETTINGS.get(key, default)
        return row.value
    except Exception:
        current_app.logger.exception("Failed to get setting: %s", key)
        return _DEFAULT_SETTINGS.get(key, default)


def get_all_settings():
    _ensure_table()
    try:
        rows = {r.key: r.value for r in SiteSetting.query.all()}
    except Exception:
        current_app.logger.exception("Failed to load all settings")
        rows = {}
    result = {}
    for key, default in _DEFAULT_SETTINGS.items():
        result[key] = rows.get(key, default)
    for key, value in rows.items():
        if key not in _DEFAULT_SETTINGS:
            result[key] = value
    return result


def set_setting(key, value):
    _ensure_table()
    try:
        row = SiteSetting.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
        else:
            db.session.add(SiteSetting(key=key, value=str(value)))
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to set setting: %s", key)


@bp.route("/admin/settings")
@login_required
@require_admin
def admin_settings():
    current_values = get_all_settings()
    settings = []
    for meta in _SETTING_META:
        settings.append({**meta, "value": current_values.get(meta["key"], meta["default"])})
    from src.admin import get_catalogues_status, _CATALOGUES_INFO
    status = get_catalogues_status()
    catalogues = [{"type": info["type"], "label": info["label"], "active": status.get(info["type"], True)} for info in _CATALOGUES_INFO]
    return render_template(
        "admin/settings.html",
        title="Administration — Paramètres",
        meta_description="Paramètres globaux du site",
        settings=settings,
        catalogues=catalogues,
    )


@bp.route("/api/admin/settings/update", methods=["POST"])
@login_required
@api_admin_required
def admin_settings_update():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Données invalides"}), 400
    for key, value in data.items():
        set_setting(key, value)
    _log_audit("settings_update", details=data)
    return jsonify({"status": "updated", "settings": get_all_settings()})


@bp.route("/api/admin/settings/logo-upload", methods=["POST"])
@login_required
@api_admin_required
def admin_logo_upload():
    import os
    import secrets
    from werkzeug.utils import secure_filename

    if "logo" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    file = request.files["logo"]
    if not file.filename:
        return jsonify({"error": "Fichier invalide"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico"):
        return jsonify({"error": "Format d'image non supporté (png, jpg, webp, svg, ico)"}), 400

    header = file.read(16)
    file.seek(0)
    is_valid = False
    if ext in (".jpg", ".jpeg") and header[:3] in (b"\xff\xd8\xff",):
        is_valid = True
    elif ext == ".png" and header[:8] == b"\x89PNG\r\n\x1a\n":
        is_valid = True
    elif ext == ".webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        is_valid = True
    elif ext == ".svg":
        is_valid = True
    elif ext == ".ico":
        is_valid = True
    if not is_valid:
        return jsonify({"error": "Le fichier n'est pas une image valide"}), 400

    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "logos")
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(f"site_logo_{secrets.token_hex(8)}{ext}")
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    logo_path = f"/static/uploads/logos/{filename}"
    set_setting("site_logo", logo_path)

    favicon_name = secure_filename(f"site_favicon_{secrets.token_hex(8)}.png")
    favicon_url = logo_path
    try:
        from PIL import Image
        img = Image.open(filepath)
        img = img.convert("RGBA")
        favicon = img.resize((32, 32), Image.LANCZOS)
        favicon_path = os.path.join(upload_dir, favicon_name)
        favicon.save(favicon_path, "PNG")
        favicon_url = f"/static/uploads/logos/{favicon_name}"
        set_setting("site_favicon", favicon_url)
    except Exception:
        set_setting("site_favicon", logo_path)

    _log_audit("logo_upload", details={"logo": logo_path, "favicon": favicon_url})

    return jsonify({"status": "updated", "logo_path": logo_path})