from flask import Blueprint, render_template, session, Response, request, g, abort, jsonify
from app import db
from src.shared import get_current_user, user_owns_item_or_admin, ITEMS_PER_PAGE, _build_page_numbers

COMMENTS_PER_PAGE = 10

bp = Blueprint("items", __name__)


def get_image_gallery(item):
    result = []
    for g in item.gallery_items:
        if g.media_type != "image":
            continue
        entry = {
            "src": g.src,
            "label": g.label,
        }
        if g.data_json and isinstance(g.data_json, dict):
            entry["magnet_link"] = g.data_json.get("magnet_link", "")
        result.append(entry)
    return result


def _serialize_comment(c):
    return {
        "id": c.id,
        "author_name": c.author_name,
        "content": c.content,
        "created_at": c.created_at,
        "parent_id": c.parent_id,
        "user_id": c.user_id,
        "user_avatar": c.user.avatar_path if c.user else None,
    }


def _build_comment_tree(comments):
    comment_map = {}
    roots = []
    for c in comments:
        d = _serialize_comment(c)
        d["replies"] = []
        comment_map[c.id] = d
    for c in comments:
        d = comment_map[c.id]
        if c.parent_id and c.parent_id in comment_map:
            comment_map[c.parent_id]["replies"].append(d)
        else:
            d["parent_id"] = None
            roots.append(d)
    return roots


def _paginate_comments(item_id, page=1):
    from models import Comment
    from sqlalchemy.orm import joinedload

    total = Comment.query.filter_by(item_id=item_id, parent_id=None).count()
    total_pages = max((total + COMMENTS_PER_PAGE - 1) // COMMENTS_PER_PAGE, 1)
    page = min(max(page, 1), total_pages) or 1
    top_comments = (
        Comment.query.options(joinedload(Comment.user))
        .filter_by(item_id=item_id, parent_id=None)
        .order_by(Comment.created_at.desc())
        .offset((page - 1) * COMMENTS_PER_PAGE)
        .limit(COMMENTS_PER_PAGE)
        .all()
    )
    top_ids = [c.id for c in top_comments]
    replies = (
        Comment.query.options(joinedload(Comment.user))
        .filter(
            Comment.item_id == item_id,
            Comment.parent_id.in_(top_ids),
        )
        .order_by(Comment.created_at.asc())
        .all()
    ) if top_ids else []
    all_comments = top_comments + replies
    comment_tree = _build_comment_tree(all_comments)
    page_numbers = _build_page_numbers(page, total_pages)
    return comment_tree, {
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


@bp.route("/catalogue/item/<int:item_id>/details/json")
def item_details_json(item_id):
    from models import Item, DataChunk, VisualizationLink

    item = Item.query.get_or_404(item_id)
    item_dict = item.to_dict()
    viz_links = [vl.to_dict() for vl in VisualizationLink.query.filter_by(parent_item_id=item_id).all()]
    all_chunks = [c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=item_id).all()]

    return jsonify({
        "item": item_dict,
        "visualization_links": viz_links,
        "data_chunks": all_chunks,
    })


@bp.route("/api/items/<int:item_id>/image-status")
def item_image_status(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    return jsonify({
        "pending": item.image_magnets_pending,
        "total": item.image_magnets_total,
        "current": len(item.gallery_items),
    })


@bp.route("/catalogue/item/<int:item_id>")
def item_detail_view(item_id):
    from models import Item, User

    item = Item.query.get_or_404(item_id)

    current_user = get_current_user()

    if item.status == "draft":
        if not current_user or item.owner_user_id != current_user.id:
            from flask import abort
            abort(404)

    related_items = Item.query.filter(
        Item.format_type == item.format_type,
        Item.id != item_id,
        Item.status != "draft",
    ).limit(3).all()

    img_gallery = get_image_gallery(item)

    from models import Comment

    from models import VisualizationLink

    comment_page = 1
    try:
        comment_page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        comment_page = 1

    comments, pag_info = _paginate_comments(item_id, comment_page)
    item_dict = item.to_dict()
    item_dict["comment_count"] = Comment.query.filter_by(item_id=item_id).count()
    viz_links = [vl.to_dict() for vl in VisualizationLink.query.filter_by(parent_item_id=item_id).all()]
    from models import DataChunk
    data_chunks = [c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=item_id).all()]

    ZOOM_ORDER = {"iris": 0, "communes": 1, "cantons": 2, "departements": 3, "regions": 4, "pays": 5}
    if item_dict.get("magnet_links"):
        item_dict["magnet_links"].sort(key=lambda ml: ZOOM_ORDER.get(ml.get("zoom_level", ""), 99))
        grouped = {}
        for ml in item_dict["magnet_links"]:
            zl = ml.get("zoom_level", "")
            grouped.setdefault(zl, []).append(ml["magnet_link"])
        item_dict["magnet_links_grouped"] = [{"zoom_level": z, "links": grouped[z]} for z in sorted(grouped, key=lambda z: ZOOM_ORDER.get(z, 99))]

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S | {item.title}",
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
        show_data_visualization_tabs=item.type == "geodonnee",
        viz_links=viz_links,
        data_chunks=data_chunks,
    )


ZOOM_LABELS = {"iris": "IRIS", "communes": "Communes", "cantons": "Cantons", "departements": "Départements", "regions": "Régions", "pays": "Pays"}
ZOOM_ORDER = {"iris": 0, "communes": 1, "cantons": 2, "departements": 3, "regions": 4, "pays": 5}


@bp.route("/catalogue/item/<int:item_id>/magnets/download")
def download_item_magnets(item_id):
    from models import Item
    item = Item.query.get_or_404(item_id)
    lines = []
    lines.append(f"# A.N.A.N.A.S — Liens Magnet")
    lines.append(f"# Titre : {item.title}")
    lines.append(f"# Format : {item.format_type}")
    lines.append(f"# URL : https://ananas.fr/catalogue/item/{item_id}")
    lines.append("")

    if item.data_format_level in ("simple", "pack"):
        magnet = item.magnet_link or ""
        if magnet:
            lines.append(f"# Magnet unique ({item.data_format_level})")
            lines.append(magnet)
    elif item.data_format_level == "individual" and item.metadata_json:
        magnets = sorted(item.metadata_json, key=lambda m: ZOOM_ORDER.get(m.get("zoom_level", ""), 99))
        current_zoom = None
        for ml in magnets:
            zl = ml.get("zoom_level", "")
            if zl != current_zoom:
                lines.append(f"")
                lines.append(f"# {ZOOM_LABELS.get(zl, zl)}")
                current_zoom = zl
            lines.append(ml.get("magnet_link", ""))

    text = "\n".join(lines)
    filename = f"ananas_magnets_{item_id}.magnet"
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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

    if item.type != "geodonnee":
        return abort(404)

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S | Données — {item.title}",
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
        show_data_visualization_tabs=item.type == "geodonnee",
        active_data_tab=True,
        viz_links=viz_links,
        data_chunks=all_chunks,
    )


@bp.route("/catalogue/item/<int:item_id>/gallery")
def item_gallery_view(item_id):
    from models import Item, DataChunk, VisualizationLink, Comment

    item = Item.query.get_or_404(item_id)
    if item.type != "geodonnee":
        return abort(404)

    current_user = get_current_user()
    comments, _ = _paginate_comments(item_id, 1)
    item_dict = item.to_dict()
    item_dict["comment_count"] = Comment.query.filter_by(item_id=item_id).count()
    viz_links = [vl.to_dict() for vl in VisualizationLink.query.filter_by(parent_item_id=item_id).all()]
    related_items = [ri.to_dict() for ri in Item.query.filter(
        Item.format_type == item.format_type, Item.id != item_id
    ).limit(3).all()]

    return render_template(
        "item_detail.html",
        title=f"A.N.A.N.A.S | Réutilisation — {item.title}",
        meta_description=item.description[:160],
        item=item_dict,
        comments=comments,
        comment_count=item_dict["comment_count"],
        related_items=related_items,
        image_gallery=get_image_gallery(item),
        current_user=current_user,
        show_data_visualization_tabs=True,
        active_reuse_tab=True,
        viz_links=viz_links,
        data_chunks=[c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=item_id).all()],
    )
