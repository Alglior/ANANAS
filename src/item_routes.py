from flask import Blueprint, render_template, session, Response
from app import db

bp = Blueprint("items", __name__)


@bp.route("/favicon.ico")
def favicon_route():
    return Response("", 204)


@bp.route("/catalogue/item/<int:item_id>")
def item_detail_view(item_id):
    from models import Item, User

    item = Item.query.get_or_404(item_id)
    related_items = Item.query.filter(
        Item.format_type == item.format_type,
        Item.id != item_id,
        Item.is_published == True
    ).limit(3).all()

    img_gallery = [g for g in item.gallery_items if g.media_type == "image"]

    current_user = None
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S. | {item.title}",
        meta_description=item.description[:160],
        item=item.to_dict(),
        related_items=[ri.to_dict() for ri in related_items],
        image_gallery=img_gallery,
        current_user=current_user,
    )


@bp.route("/catalogue/item/<int:item_id>/gallery")
def item_gallery_view(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    return render_template(
        "gallery.html",
        title=f"Galerie — {item.title}",
        meta_description="Galerie de " + item.title,
        item=item.to_dict(),
    )
