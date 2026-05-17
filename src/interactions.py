import datetime as dt

from flask import Blueprint, request, redirect, url_for, jsonify
from app import db
from src.shared import login_required, get_current_user
from utils.security import sanitize_html

bp = Blueprint("interactions", __name__)


@bp.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
@login_required
def rate_item(item_id):
    from models import Item, Rating

    item = Item.query.get_or_404(item_id)
    rating_value = request.form.get("rating")
    import logging
    current_user = get_current_user()
    logging.warning(f"[RATE] item_id={item_id} raw_rating='{rating_value}' user_id={current_user.id if current_user else None}")

    if not rating_value or not rating_value.isdigit():
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    rating = int(rating_value)
    existing = Rating.query.filter_by(item_id=item_id, user_id=current_user.id).first()
    logging.warning(f"[RATE] found_existing={bool(existing)} new_rating={rating}")
    if existing:
        existing.rating = rating
    else:
        new_rating = Rating(item_id=item_id, user_id=current_user.id, rating=rating)
        db.session.add(new_rating)

    ratings = Rating.query.filter_by(item_id=item_id).all()
    logging.warning(f"[RATE] all_ratings={[(r.id, r.user_id, r.rating) for r in ratings]}")

    db.session.commit()
    return redirect(url_for("items.item_detail_view", item_id=item_id))


@bp.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
def add_comment(item_id):
    from models import Item, Comment

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    raw_author = request.form.get("author", "").strip() or (f"{current_user.prenom} {current_user.nom}" if current_user else "")
    author_name = sanitize_html(raw_author)
    content = sanitize_html(request.form.get("text", ""))

    if not content:
        return redirect(url_for("items.item_detail_view", item_id=item_id))

    comment = Comment(
        item_id=item_id,
        user_id=current_user.id if current_user else None,
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

    return jsonify({
        "status": "updated",
        "item_id": item_id,
        "new_status": status,
    })
