import datetime as dt

from flask import Blueprint, request, redirect, url_for, jsonify
from app import db
from src.shared import login_required, get_current_user
from utils.security import sanitize_html

bp = Blueprint("interactions", __name__)


@bp.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
def rate_item(item_id):
    from models import Item, Rating

    item = Item.query.get_or_404(item_id)
    rating_value = request.form.get("rating")

    if not rating_value or not rating_value.isdigit():
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    rating = int(rating_value)
    existing = Rating.query.filter_by(item_id=item_id).first()
    if existing:
        existing.rating = rating
    else:
        new_rating = Rating(item_id=item_id, rating=rating)
        db.session.add(new_rating)

    ratings = Rating.query.filter_by(item_id=item_id).all()
    avg = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
    item.format_type = getattr(item, "_rating_avg", None) or 0

    db.session.commit()
    return redirect(url_for("items.item_detail_view", item_id=item_id))


@bp.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
def add_comment(item_id):
    from models import Item, Comment

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    author_name = request.form.get("author", "").strip() or (f"{current_user.prenom} {current_user.nom}" if current_user else "")
    content = sanitize_html(request.form.get("text", ""))

    if not content:
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    comment = Comment(
        item_id=item_id,
        author_name=author_name,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for("items.item_detail_view", item_id=item_id))


@bp.route("/api/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):
    from models import Item

    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    status = data.get("status", "")

    if status not in ("verified", "unofficial", "rejected"):
        return jsonify({"error": "Statut invalide"}), 400

    item = Item.query.get_or_404(item_id)

    item.verification_status = status
    item.verifier_user_id = current_user.id
    item.verified_at = dt.datetime.now() if status == "verified" else None
    item.verification_notes = data.get("notes")

    db.session.commit()

    return jsonify({
        "status": "updated",
        "item_id": item_id,
        "new_status": status,
    })
