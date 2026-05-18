from flask import Blueprint, render_template, session, Response, request, g, abort, jsonify
from app import db
from src.shared import get_current_user, user_owns_item_or_admin, ITEMS_PER_PAGE, _build_page_numbers

COMMENTS_PER_PAGE = 10

bp = Blueprint("items", __name__)


def get_image_gallery(item):
    return [g for g in item.gallery_items if g.media_type == "image"]


def _paginate_comments(item_id, page=1):
    from models import Comment

    total = Comment.query.filter_by(item_id=item_id).count()
    total_pages = max((total + COMMENTS_PER_PAGE - 1) // COMMENTS_PER_PAGE, 1)
    page = min(max(page, 1), total_pages) or 1
    comments = (
        Comment.query.filter_by(item_id=item_id)
        .order_by(Comment.created_at.desc())
        .offset((page - 1) * COMMENTS_PER_PAGE)
        .limit(COMMENTS_PER_PAGE)
        .all()
    )
    comment_dicts = [
        {
            "author_name": c.author_name,
            "content": c.content,
            "created_at": c.created_at,
        }
        for c in comments
    ]
    page_numbers = _build_page_numbers(page, total_pages)
    return comment_dicts, {
        "page": page,
        "per_page": COMMENTS_PER_PAGE,
        "total_items": total,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }


@bp.route("/favicon.ico")
def favicon_route():
    return Response("", 204)


@bp.route("/catalogue/item/<int:item_id>/comments/json")
def item_comments_json(item_id):
    from models import Item, Comment

    item = Item.query.get_or_404(item_id)
    current_user = get_current_user()

    comment_page = 1
    try:
        comment_page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        comment_page = 1

    comments, pag_info = _paginate_comments(item_id, comment_page)
    item_dict = item.to_dict()
    return jsonify({
        "item": item_dict,
        "comments": comments,
        "comment_count": Comment.query.filter_by(item_id=item_id).count(),
        **pag_info,
    })


@bp.route("/catalogue/item/<int:item_id>")
def item_detail_view(item_id):
    from models import Item, User

    item = Item.query.get_or_404(item_id)
    related_items = Item.query.filter(
        Item.format_type == item.format_type,
        Item.id != item_id,
    ).limit(3).all()

    img_gallery = get_image_gallery(item)

    current_user = get_current_user()

    from models import Comment

    comment_page = 1
    try:
        comment_page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        comment_page = 1

    comments, pag_info = _paginate_comments(item_id, comment_page)
    item_dict = item.to_dict()
    item_dict["comment_count"] = Comment.query.filter_by(item_id=item_id).count()

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S. | {item.title}",
        meta_description=item.description[:160],
        item=item_dict,
        comments=comments,
        comment_count=item_dict["comment_count"],
        comment_page=pag_info["page"],
        comment_total_pages=pag_info["total_pages"],
        comment_page_numbers=pag_info["page_numbers"],
        related_items=[ri.to_dict() for ri in related_items],
        image_gallery=img_gallery,
        current_user=current_user,
    )


@bp.route("/catalogue/item/<int:item_id>/data")
def item_data_view(item_id):
    from models import Item, DataChunk, VisualizationLink, User

    item = Item.query.get_or_404(item_id)
    current_user = get_current_user()

    from models import Comment

    comment_page = 1
    try:
        comment_page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        comment_page = 1

    comments, pag_info = _paginate_comments(item_id, comment_page)
    item_dict = item.to_dict()
    item_dict["comment_count"] = Comment.query.filter_by(item_id=item_id).count()
    viz_links = [vl.to_dict() for vl in VisualizationLink.query.filter_by(parent_item_id=item_id).all()]
    all_chunks = [c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=item_id).all()]

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S. | Données — {item.title}",
        meta_description=item.description[:160],
        item=item_dict,
        comments=comments,
        comment_count=item_dict["comment_count"],
        comment_page=pag_info["page"],
        comment_total_pages=pag_info["total_pages"],
        comment_page_numbers=pag_info["page_numbers"],
        related_items=[ri.to_dict() for ri in Item.query.filter(
            Item.format_type == item.format_type, Item.id != item_id
        ).limit(3).all()],
        image_gallery=get_image_gallery(item),
        current_user=current_user,
        active_data_tab=True,
        viz_links=viz_links,
        data_chunks=all_chunks,
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
