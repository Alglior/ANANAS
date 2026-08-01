from flask import request, jsonify, render_template
from app import db
from src.admin import bp, login_required, require_admin, api_admin_required, _log_audit
from models import SiteSetting

_DEFAULT_SETTINGS = {
    "items_per_page": "30",
    "comments_per_page": "10",
    "catalogue_per_page": "20",
    "site_name": "A.N.A.N.A.S",
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
    {"key": "items_per_page", "label": "Éléments par page (catalogue)", "type": "number", "default": "30"},
    {"key": "comments_per_page", "label": "Commentaires par page", "type": "number", "default": "10"},
    {"key": "catalogue_per_page", "label": "Éléments par page (JSON)", "type": "number", "default": "20"},
    {"key": "site_name", "label": "Nom du site", "type": "text", "default": "A.N.A.N.A.S"},
    {"key": "enable_registration", "label": "Inscriptions ouvertes", "type": "boolean", "default": "true"},
    {"key": "maintenance_mode", "label": "Mode maintenance", "type": "boolean", "default": "false"},
    {"key": "", "label": "─ Page d'accueil ─", "type": "separator", "default": ""},
    {"key": "home_eyebrow", "label": "Accueil — Sur-titre (eyebrow)", "type": "text", "default": "Partage de données géospatiales"},
    {"key": "home_hero_title", "label": "Accueil — Titre principal", "type": "text", "default": "Partagez vos géodonnées avec des torrents vérifiés"},
    {"key": "home_hero_subtitle", "label": "Accueil — Sous-titre", "type": "text", "default": "A.N.A.N.A.S permet de partager et télécharger des données géographiques..."},
    {"key": "home_show_mirrors", "label": "Accueil — Afficher sites miroirs", "type": "boolean", "default": "true"},
    {"key": "home_show_geopackages", "label": "Accueil — Afficher packs GeoPackage", "type": "boolean", "default": "true"},
    {"key": "home_show_featured", "label": "Accueil — Afficher données en avant", "type": "boolean", "default": "true"},
    {"key": "home_show_simple_files", "label": "Accueil — Afficher fichiers simples", "type": "boolean", "default": "true"},
    {"key": "", "label": "─ Catalogue ─", "type": "separator", "default": ""},
    {"key": "catalogue_donnees_title", "label": "Catalogue — Titre géodonnées", "type": "text", "default": "Catalogue des géodonnées"},
    {"key": "catalogue_cartes_title", "label": "Catalogue — Titre cartes", "type": "text", "default": "Catalogue des cartes"},
    {"key": "catalogue_applications_title", "label": "Catalogue — Titre applications", "type": "text", "default": "Catalogue d'applications"},
]


def _ensure_table():
    try:
        SiteSetting.__table__.create(db.engine, checkfirst=True)
    except Exception:
        pass


def get_setting(key, default=None):
    _ensure_table()
    try:
        row = SiteSetting.query.filter_by(key=key).first()
        if row is None:
            return _DEFAULT_SETTINGS.get(key, default)
        return row.value
    except Exception:
        return _DEFAULT_SETTINGS.get(key, default)


def get_all_settings():
    _ensure_table()
    try:
        rows = {r.key: r.value for r in SiteSetting.query.all()}
    except Exception:
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