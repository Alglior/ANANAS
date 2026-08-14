from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _log_audit, _get_json_data
from utils.security import sanitize_html
from models import PredefinedTag, PredefinedTagCategory


def _serialize_category(cat):
    return {
        "id": cat.id,
        "name": cat.name,
        "display_order": cat.display_order,
        "tags": [
            {"id": t.id, "name": t.name, "display_order": t.display_order}
            for t in cat.tags
        ],
    }


@bp.route("/api/admin/tags", methods=["GET"])
@login_required
@api_admin_required
def list_tag_categories():

    categories = PredefinedTagCategory.query.order_by(
        PredefinedTagCategory.display_order, PredefinedTagCategory.id
    ).all()
    return jsonify({"categories": [_serialize_category(c) for c in categories]})


@bp.route("/api/admin/tags", methods=["POST"])
@login_required
@api_admin_required
def create_tag_category():

    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Le nom est requis."}), 400
    if len(name) > 100:
        return jsonify({"error": "Nom trop long (100 caractères max)."}), 400

    existing = PredefinedTagCategory.query.filter_by(name=name).first()
    if existing:
        return jsonify({"error": "Une catégorie avec ce nom existe déjà."}), 400

    max_order = (
        db.session.query(db.func.max(PredefinedTagCategory.display_order)).scalar()
        or 0
    )
    cat = PredefinedTagCategory(
        name=sanitize_html(name), display_order=max_order + 1
    )
    db.session.add(cat)
    db.session.commit()
    _log_audit("tag_category_created", "tag_category", cat.id, {"name": cat.name})
    return jsonify({"status": "created", "category": _serialize_category(cat)})


@bp.route("/api/admin/tags/<int:category_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_tag_category(category_id):

    cat = PredefinedTagCategory.query.get_or_404(category_id)
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Le nom ne peut pas être vide."}), 400
        if len(name) > 100:
            return jsonify({"error": "Nom trop long (100 caractères max)."}), 400
        existing = PredefinedTagCategory.query.filter_by(name=name).first()
        if existing and existing.id != category_id:
            return jsonify({"error": "Une catégorie avec ce nom existe déjà."}), 400
        cat.name = sanitize_html(name)
    if "display_order" in data:
        cat.display_order = int(data["display_order"])

    db.session.commit()
    _log_audit("tag_category_updated", "tag_category", cat.id, {"name": cat.name})
    return jsonify({"status": "updated", "category": _serialize_category(cat)})


@bp.route("/api/admin/tags/<int:category_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_tag_category(category_id):

    cat = PredefinedTagCategory.query.get_or_404(category_id)
    db.session.delete(cat)
    db.session.commit()
    _log_audit(
        "tag_category_deleted", "tag_category", category_id, {"name": cat.name}
    )
    return jsonify({"status": "deleted", "id": category_id})


@bp.route("/api/admin/tags/<int:category_id>/tags", methods=["POST"])
@login_required
@api_admin_required
def create_tag(category_id):

    cat = PredefinedTagCategory.query.get_or_404(category_id)
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Le nom du tag est requis."}), 400
    if len(name) > 100:
        return jsonify({"error": "Nom trop long (100 caractères max)."}), 400

    existing = PredefinedTag.query.filter_by(
        category_id=category_id, name=name
    ).first()
    if existing:
        return jsonify({"error": "Ce tag existe déjà dans cette catégorie."}), 400

    max_order = (
        db.session.query(db.func.max(PredefinedTag.display_order))
        .filter(PredefinedTag.category_id == category_id)
        .scalar()
        or 0
    )
    tag = PredefinedTag(
        category_id=cat.id,
        name=sanitize_html(name),
        display_order=max_order + 1,
    )
    db.session.add(tag)
    db.session.commit()
    _log_audit("tag_created", "tag", tag.id, {"name": tag.name, "category": cat.name})
    return jsonify(
        {
            "status": "created",
            "tag": {
                "id": tag.id,
                "name": tag.name,
                "display_order": tag.display_order,
            },
        }
    )


@bp.route("/api/admin/tags/<int:category_id>/tags/<int:tag_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_tag(category_id, tag_id):

    tag = PredefinedTag.query.filter_by(
        id=tag_id, category_id=category_id
    ).first_or_404()
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Le nom ne peut pas être vide."}), 400
        if len(name) > 100:
            return jsonify({"error": "Nom trop long (100 caractères max)."}), 400
        existing = PredefinedTag.query.filter_by(
            category_id=category_id, name=name
        ).first()
        if existing and existing.id != tag_id:
            return jsonify({"error": "Ce tag existe déjà dans cette catégorie."}), 400
        tag.name = sanitize_html(name)
    if "display_order" in data:
        tag.display_order = int(data["display_order"])

    db.session.commit()
    _log_audit("tag_updated", "tag", tag.id, {"name": tag.name})
    return jsonify(
        {
            "status": "updated",
            "tag": {
                "id": tag.id,
                "name": tag.name,
                "display_order": tag.display_order,
            },
        }
    )


@bp.route("/api/admin/tags/<int:category_id>/tags/<int:tag_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_tag(category_id, tag_id):

    tag = PredefinedTag.query.filter_by(
        id=tag_id, category_id=category_id
    ).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    _log_audit("tag_deleted", "tag", tag_id, {"name": tag.name})
    return jsonify({"status": "deleted", "id": tag_id})