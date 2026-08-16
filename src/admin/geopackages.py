from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _serialize_geopackage, _log_audit, _require_json
from utils.security import sanitize_html, validate_external_url
from models import GeoPackage


@bp.route("/api/admin/geopackages", methods=["GET"])
@login_required
@api_admin_required
def list_geopackages():

    packages = GeoPackage.query.order_by(GeoPackage.display_order, GeoPackage.id).all()
    return jsonify({"packages": [_serialize_geopackage(p) for p in packages]})


@bp.route("/api/admin/geopackages", methods=["POST"])
@login_required
@api_admin_required
def create_geopackage():

    data, error, code = _require_json()
    if error:
        return error, code
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    format_info = (data.get("format_info") or "").strip()
    link_url = (data.get("link_url") or "").strip()

    if not title or not description or not format_info or not link_url:
        return jsonify({"error": "Tous les champs sont requis."}), 400
    if len(title) > 200 or len(description) > 500 or len(format_info) > 200 or len(link_url) > 500:
        return jsonify({"error": "Champs trop longs."}), 400
    if not validate_external_url(link_url):
        return jsonify({"error": "URL invalide ou non sécurisée."}), 400

    max_order = db.session.query(db.func.max(GeoPackage.display_order)).scalar() or 0
    pkg = GeoPackage(
        title=sanitize_html(title), description=sanitize_html(description),
        format_info=sanitize_html(format_info), link_url=link_url,
        display_order=max_order + 1, is_active=True,
    )
    db.session.add(pkg)
    db.session.commit()
    _log_audit("geopackage_created", "geopackage", pkg.id, {"title": pkg.title})
    return jsonify({"status": "created", "package": _serialize_geopackage(pkg)})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_geopackage(pkg_id):

    pkg = GeoPackage.query.get_or_404(pkg_id)
    data, error, code = _require_json()
    if error:
        return error, code

    if "title" in data:
        pkg.title = sanitize_html(data["title"].strip())
    if "description" in data:
        pkg.description = sanitize_html(data["description"].strip())
    if "format_info" in data:
        pkg.format_info = sanitize_html(data["format_info"].strip())
    if "link_url" in data:
        new_url = data["link_url"].strip()
        if not validate_external_url(new_url):
            return jsonify({"error": "URL invalide ou non sécurisée."}), 400
        pkg.link_url = new_url
    if "display_order" in data:
        pkg.display_order = int(data["display_order"])
    if "is_active" in data:
        pkg.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("geopackage_updated", "geopackage", pkg_id, {"title": pkg.title})
    return jsonify({"status": "updated", "package": _serialize_geopackage(pkg)})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_geopackage(pkg_id):

    pkg = GeoPackage.query.get_or_404(pkg_id)
    db.session.delete(pkg)
    db.session.commit()
    _log_audit("geopackage_deleted", "geopackage", pkg_id, {"title": pkg.title})
    return jsonify({"status": "deleted", "id": pkg_id})