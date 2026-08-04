from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _serialize_mirror, _log_audit, _get_json_data
from utils.security import sanitize_html, validate_external_url


@bp.route("/api/admin/mirrors", methods=["GET"])
@login_required
@api_admin_required
def list_mirrors():
    from models import MirrorSite

    mirrors = MirrorSite.query.order_by(MirrorSite.display_order, MirrorSite.id).all()
    return jsonify({"mirrors": [_serialize_mirror(m) for m in mirrors]})


@bp.route("/api/admin/mirrors", methods=["POST"])
@login_required
@api_admin_required
def create_mirror():
    from models import MirrorSite

    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    description = (data.get("description") or "").strip()

    if not name or not url or not description:
        return jsonify({"error": "Tous les champs sont requis."}), 400
    if len(name) > 200 or len(url) > 500 or len(description) > 500:
        return jsonify({"error": "Champs trop longs."}), 400
    if not validate_external_url(url):
        return jsonify({"error": "URL invalide ou non sécurisée."}), 400

    max_order = db.session.query(db.func.max(MirrorSite.display_order)).scalar() or 0
    mirror = MirrorSite(
        name=sanitize_html(name), url=url.strip(),
        description=sanitize_html(description),
        display_order=max_order + 1, is_active=True,
    )
    db.session.add(mirror)
    db.session.commit()
    _log_audit("mirror_created", "mirror", mirror.id, {"name": mirror.name, "url": mirror.url})
    return jsonify({"status": "created", "mirror": _serialize_mirror(mirror)})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_mirror(mirror_id):
    from models import MirrorSite

    mirror = MirrorSite.query.get_or_404(mirror_id)
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    if "name" in data:
        mirror.name = sanitize_html(data["name"].strip())
    if "url" in data:
        new_url = data["url"].strip()
        if not validate_external_url(new_url):
            return jsonify({"error": "URL invalide ou non sécurisée."}), 400
        mirror.url = new_url
    if "description" in data:
        mirror.description = sanitize_html(data["description"].strip())
    if "display_order" in data:
        mirror.display_order = int(data["display_order"])
    if "is_active" in data:
        mirror.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("mirror_updated", "mirror", mirror_id, {"name": mirror.name})
    return jsonify({"status": "updated", "mirror": _serialize_mirror(mirror)})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_mirror(mirror_id):
    from models import MirrorSite

    mirror = MirrorSite.query.get_or_404(mirror_id)
    db.session.delete(mirror)
    db.session.commit()
    _log_audit("mirror_deleted", "mirror", mirror_id, {"name": mirror.name})
    return jsonify({"status": "deleted", "id": mirror_id})