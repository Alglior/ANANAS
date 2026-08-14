from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _serialize_featured, _log_audit, _get_json_data
from models import FeaturedItem, Item


@bp.route("/api/admin/featured", methods=["GET"])
@login_required
@api_admin_required
def list_featured():

    featured = FeaturedItem.query.order_by(FeaturedItem.display_order, FeaturedItem.id).all()
    return jsonify({"featured": [_serialize_featured(f) for f in featured]})


@bp.route("/api/admin/items/search", methods=["GET"])
@login_required
@api_admin_required
def search_items():

    q = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 20))

    query = Item.query.filter(Item.status == "published")
    if q:
        query = query.filter(Item.title.ilike(f"%{q}%"))

    items = query.order_by(Item.title).limit(limit).all()
    return jsonify({
        "items": [
            {"id": it.id, "title": it.title, "type": it.type,
             "format_type": it.format_type, "description": it.description[:100] if it.description else ""}
            for it in items
        ],
    })


@bp.route("/api/admin/featured", methods=["POST"])
@login_required
@api_admin_required
def create_featured():

    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id requis."}), 400
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item introuvable."}), 404
    if FeaturedItem.query.filter_by(item_id=item_id).first():
        return jsonify({"error": "Cet item est déjà mis en avant."}), 409

    max_order = db.session.query(db.func.max(FeaturedItem.display_order)).scalar() or 0
    featured = FeaturedItem(item_id=item_id, display_order=max_order + 1, is_active=True)
    db.session.add(featured)
    db.session.commit()
    _log_audit("featured_created", "featured", featured.id, {"item_id": item_id, "title": item.title})

    return jsonify({"status": "created", "featured": _serialize_featured(featured)})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_featured(featured_id):

    featured = FeaturedItem.query.get_or_404(featured_id)
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    if "display_order" in data:
        featured.display_order = int(data["display_order"])
    if "is_active" in data:
        featured.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("featured_updated", "featured", featured_id, {"item_id": featured.item_id})
    return jsonify({"status": "updated", "featured": _serialize_featured(featured)})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_featured(featured_id):

    featured = FeaturedItem.query.get_or_404(featured_id)
    db.session.delete(featured)
    db.session.commit()
    _log_audit("featured_deleted", "featured", featured_id, {"title": featured.item.title if featured.item else None})
    return jsonify({"status": "deleted", "id": featured_id})