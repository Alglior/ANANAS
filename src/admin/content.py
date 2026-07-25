import datetime as dt

from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required, get_current_user
from src.admin import _serialize_comment, _serialize_item, _log_audit, _paginate
from src.shared import ITEMS_PER_PAGE


# --- Comments ---

@bp.route("/api/admin/comments", methods=["GET"])
@login_required
@api_admin_required
def list_comments():
    from models import Comment

    item_id = request.args.get("item_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", ITEMS_PER_PAGE, type=int)

    query = Comment.query
    if item_id:
        query = query.filter_by(item_id=item_id)

    since_param = request.args.get("since")
    if since_param:
        try:
            query = query.filter(Comment.created_at >= dt.datetime.fromisoformat(since_param))
        except (ValueError, TypeError):
            pass

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(Comment.created_at.desc()), page, per_page
    )
    return jsonify({
        "comments": [_serialize_comment(c) for c in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/comments/<int:comment_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_comment(comment_id):
    from models import Comment

    comment = Comment.query.get_or_404(comment_id)
    item_title = comment.item.title if comment.item else None
    db.session.delete(comment)
    db.session.commit()
    _log_audit("comment_deleted", "comment", comment_id, {"item_title": item_title, "content_preview": (comment.content[:80] if comment.content else "")})
    return jsonify({"status": "deleted", "comment_id": comment_id})


# --- Items ---

@bp.route("/api/admin/items", methods=["GET"])
@login_required
@api_admin_required
def list_items():
    from models import Item

    item_type = request.args.get("type", "all")
    page = int(request.args.get("page", 1))

    query = Item.query
    if item_type != "all":
        query = query.filter_by(type=item_type)

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(Item.created_at.desc()), page
    )
    return jsonify({
        "items": [_serialize_item(it) for it in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/items/<int:item_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_item(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    title = item.title
    type_name = item.type
    db.session.delete(item)
    db.session.commit()
    _log_audit("item_deleted", "item", item_id, {"title": title, "type": type_name})
    return jsonify({"status": "deleted", "item_id": item_id, "title": title})


@bp.route("/api/admin/items/<int:item_id>/verify", methods=["POST"])
@login_required
@api_admin_required
def verify_item(item_id):
    from models import Item

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    item.verification_status = 'verified'
    item.verifier_user_id = current_user.id
    item.verified_at = db.func.now()
    db.session.commit()
    _log_audit("item_verified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "verified"})


@bp.route("/api/admin/items/<int:item_id>/unverify", methods=["POST"])
@login_required
@api_admin_required
def unverify_item(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    item.verification_status = 'unofficial'
    item.verifier_user_id = None
    item.verified_at = None
    db.session.commit()
    _log_audit("item_unverified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "unofficial"})