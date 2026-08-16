import datetime as dt

from flask import Blueprint, request, redirect, url_for, jsonify
from app import db
from models import Comment, Item, Rating
from src.shared import login_required, get_current_user
from utils.security import sanitize_html

bp = Blueprint("interactions", __name__)

MAX_COMMENT_LENGTH = 2000
MAX_AUTHOR_NAME_LENGTH = 80


@bp.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
@login_required
def rate_item(item_id):

    item = Item.query.get_or_404(item_id)
    rating_value = request.form.get("rating")
    current_user = get_current_user()

    if not rating_value or not rating_value.isdigit():
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    rating = int(rating_value)
    if rating < 1 or rating > 5:
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    existing = Rating.query.filter_by(item_id=item_id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
    else:
        db.session.add(Rating(item_id=item_id, user_id=current_user.id, rating=rating))

    db.session.commit()
    return redirect(url_for("items.item_detail_view", item_id=item_id))


@bp.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
@login_required
def add_comment(item_id):

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    raw_author = request.form.get("author", "").strip() or (f"{current_user.prenom} {current_user.nom}" if current_user else "")
    author_name = sanitize_html(raw_author)[:MAX_AUTHOR_NAME_LENGTH]
    content = sanitize_html(request.form.get("text", ""))[:MAX_COMMENT_LENGTH]
    parent_id = request.form.get("parent_id", type=int)

    if not content:
        page = request.args.get("page", 1, type=int)
        return redirect(f"{url_for('items.item_detail_view', item_id=item_id)}?page={page}")

    if parent_id:
        parent = Comment.query.filter_by(id=parent_id, item_id=item_id).first()
        if not parent:
            parent_id = None

    db.session.add(Comment(
        item_id=item_id, user_id=current_user.id if current_user else None,
        author_name=author_name, content=content, parent_id=parent_id,
    ))
    db.session.commit()

    page = request.args.get("page", 1, type=int)
    return redirect(f"{url_for('items.item_detail_view', item_id=item_id)}?page={page}")


@bp.route("/api/catalogue/item/<int:item_id>/reply", methods=["POST"])
@login_required
def reply_comment_json(item_id):

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    data = request.get_json(silent=True) or {}
    parent_id = data.get("parent_id")
    if parent_id is not None:
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            parent_id = None
    content = sanitize_html(data.get("text", ""))[:MAX_COMMENT_LENGTH]

    if not content:
        return jsonify({"error": "Le commentaire ne peut pas être vide"}), 400

    if parent_id:
        parent = Comment.query.filter_by(id=parent_id, item_id=item_id).first()
        if not parent:
            return jsonify({"error": "Commentaire parent introuvable"}), 404

    raw_author = f"{current_user.prenom} {current_user.nom}" if current_user else ""
    author_name = sanitize_html(raw_author)[:MAX_AUTHOR_NAME_LENGTH]

    comment = Comment(
        item_id=item_id, user_id=current_user.id if current_user else None,
        author_name=author_name, content=content, parent_id=parent_id,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "id": comment.id,
        "author_name": comment.author_name,
        "content": comment.content,
        "created_at": comment.created_at.strftime("%d/%m/%Y") if comment.created_at else "",
        "parent_id": comment.parent_id,
        "user_id": comment.user_id,
        "user_avatar": comment.user.avatar_path if comment.user else None,
    })


@bp.route("/api/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
    status = data.get("status", "")
    if status not in ("verified", "unofficial", "rejected"):
        return jsonify({"error": "Statut invalide"}), 400

    item = Item.query.get_or_404(item_id)
    item.verification_status = status
    item.verifier_user_id = current_user.id
    item.verified_at = dt.datetime.now() if status == "verified" else None
    item.verification_notes = sanitize_html(data.get("notes", "")).strip() if data.get("notes") else None

    db.session.commit()
    return jsonify({"status": "updated", "item_id": item_id, "new_status": status})