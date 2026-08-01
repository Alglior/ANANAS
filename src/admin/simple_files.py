from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _serialize_simple_file, _log_audit, _get_json_data


@bp.route("/api/admin/simple-files", methods=["GET"])
@login_required
@api_admin_required
def list_simple_files():
    from models import SimpleFileItem

    items = SimpleFileItem.query.order_by(SimpleFileItem.display_order, SimpleFileItem.id).all()
    return jsonify({"simple_files": [_serialize_simple_file(f) for f in items]})


@bp.route("/api/admin/simple-files", methods=["POST"])
@login_required
@api_admin_required
def create_simple_file():
    from models import SimpleFileItem, Item

    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id requis."}), 400
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item introuvable."}), 404
    if SimpleFileItem.query.filter_by(item_id=item_id).first():
        return jsonify({"error": "Cet item est déjà dans les fichiers simples."}), 409

    max_order = db.session.query(db.func.max(SimpleFileItem.display_order)).scalar() or 0
    sf = SimpleFileItem(item_id=item_id, display_order=max_order + 1, is_active=True)
    db.session.add(sf)
    db.session.commit()
    _log_audit("simple_file_created", "simple_file", sf.id, {"item_id": item_id, "title": item.title})

    return jsonify({"status": "created", "simple_file": _serialize_simple_file(sf)})


@bp.route("/api/admin/simple-files/<int:sf_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_simple_file(sf_id):
    from models import SimpleFileItem

    sf = SimpleFileItem.query.get_or_404(sf_id)
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    if "display_order" in data:
        sf.display_order = int(data["display_order"])
    if "is_active" in data:
        sf.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("simple_file_updated", "simple_file", sf_id, {"item_id": sf.item_id})
    return jsonify({"status": "updated", "simple_file": _serialize_simple_file(sf)})


@bp.route("/api/admin/simple-files/<int:sf_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_simple_file(sf_id):
    from models import SimpleFileItem

    sf = SimpleFileItem.query.get_or_404(sf_id)
    db.session.delete(sf)
    db.session.commit()
    _log_audit("simple_file_deleted", "simple_file", sf_id, {"title": sf.item.title if sf.item else None})
    return jsonify({"status": "deleted", "id": sf_id})