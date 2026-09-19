from flask import Blueprint, request, render_template, redirect, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.routing import BaseConverter, ValidationError
from app import db
from models import Item, ItemTag, Organization, PredefinedTag, PredefinedTagCategory
from src.admin import is_catalogue_enabled
from src.shared import ITEM_TYPE_MAP, _build_page_numbers, _paginate

_CATALOGUE_META = {
    "donnees": {
        "title_prefix": "Catalogue des géodonnées",
        "meta": "Parcourez le catalogue complet des géodonnées A.N.A.N.A.S",
    },
    "cartes": {
        "title_prefix": "Catalogue des cartes",
        "meta": "Explorez la collection de cartes et produits cartographiques A.N.A.N.A.S",
    },
    "applications": {
        "title_prefix": "Catalogue d'applications",
        "meta": "Découvrez les applications et services web géospatiaux A.N.A.N.A.S",
    },
}

type_map = ITEM_TYPE_MAP

bp = Blueprint("catalogue", __name__)


class CatalogueTypeConverter(BaseConverter):
    def to_url(self, value):
        return value

    def to_python(self, value):
        if value not in type_map:
            raise ValidationError()
        return value


def _build_filtered_query(catalogue_type, filter_verified=False, filter_unofficial=False, filter_format="", org_slug=None, filter_imod="", filter_tag=None, filter_category=None, search_query=None, exclude_tags=None, filter_year=None):

    item_type = type_map.get(catalogue_type)
    if not item_type:
        return None

    query = Item.query.filter_by(type=item_type).filter(Item.status == "published")

    # Recherche par titre ou description
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Item.title.ilike(search),
                Item.description.ilike(search)
            )
        )

    if org_slug:
        org = Organization.query.filter_by(slug=org_slug).first()
        if org:
            query = query.filter_by(organization_id=org.id)

    if filter_verified:
        query = query.filter_by(verification_status="verified")
    elif filter_unofficial:
        query = query.filter(Item.verification_status != "verified")

    if filter_format:
        query = query.filter_by(data_format_level=filter_format)

    if filter_tag:
        if isinstance(filter_tag, list) and len(filter_tag) > 0:
            for tag in filter_tag:
                sub = db.session.query(ItemTag.item_id).filter(ItemTag.tag == tag).subquery()
                query = query.filter(Item.id.in_(sub))
        elif isinstance(filter_tag, str) and filter_tag:
            sub = db.session.query(ItemTag.item_id).filter(ItemTag.tag == filter_tag).subquery()
            query = query.filter(Item.id.in_(sub))

    if exclude_tags:
        for tag in exclude_tags:
            sub = db.session.query(ItemTag.item_id).filter(ItemTag.tag == tag).subquery()
            query = query.filter(~Item.id.in_(sub))

    if filter_category:
        sub = db.session.query(ItemTag.item_id).join(
            PredefinedTag, ItemTag.tag == PredefinedTag.name
        ).join(
            PredefinedTagCategory
        ).filter(PredefinedTagCategory.name == filter_category).subquery()
        query = query.filter(Item.id.in_(sub))

    if filter_year:
        import re
        m = re.fullmatch(r"\s*(\d{4})\s*(?:[-\u2013]\s*(\d{4})\s*)?", str(filter_year))
        if m:
            year_start = int(m.group(1))
            year_end = int(m.group(2)) if m.group(2) else year_start
            if year_end < year_start:
                year_start, year_end = year_end, year_start
            query = query.filter(
                db.and_(
                    db.or_(Item.data_year_start.isnot(None), Item.data_year_end.isnot(None)),
                    db.or_(Item.data_year_start.is_(None), Item.data_year_start <= year_end),
                    db.or_(
                        db.and_(Item.data_year_end.isnot(None), Item.data_year_end >= year_start),
                        db.and_(Item.data_year_end.is_(None), Item.data_year_start >= year_start),
                    ),
                )
            )

    query = query.options(
        subqueryload(Item.tags),
        subqueryload(Item.gallery_items),
        subqueryload(Item.ratings),
        subqueryload(Item.comments),
        subqueryload(Item.visualization_links),
        joinedload(Item.verifier),
        joinedload(Item.organization),
    )

    return query


def _build_catalogue_urls(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, _filter_imod="", filter_year=None):
    base = f"/catalogue/{catalogue}"

    def _build_url(include_verif=False, include_unofficial=False, include_format=None):
        parts = []
        if include_verif:
            parts.append("verified=1")
        elif include_unofficial:
            parts.append("unofficial=1")
        if include_format:
            parts.append(f"format_level={include_format}")
        if filter_year:
            parts.append(f"year={filter_year}")
        if org_slug:
            parts.append(f"org={org_slug}")
        return base + ("?" + "&".join(parts) if parts else "")

    return {
        "url_all": base,
        "url_verified": _build_url(include_verif=True, include_format=filter_format or None),
        "url_unofficial": _build_url(include_unofficial=True, include_format=filter_format or None),
        "url_pack": _build_url(include_verif=filter_verified, include_unofficial=filter_unofficial, include_format="pack"),
        "url_simple": _build_url(include_verif=filter_verified, include_unofficial=filter_unofficial, include_format="simple"),
        "url_ind": _build_url(include_verif=filter_verified, include_unofficial=filter_unofficial, include_format="individual"),
        "url_imod_high": _build_url(include_verif=filter_verified, include_unofficial=filter_unofficial, include_format=filter_format or None) + ("&" if filter_verified or filter_unofficial or filter_format or org_slug else "?") + "imod=high",
        "url_imod_low": _build_url(include_verif=filter_verified, include_unofficial=filter_unofficial, include_format=filter_format or None) + ("&" if filter_verified or filter_unofficial or filter_format or org_slug else "?") + "imod=low",
    }


def _build_filter_qs(filter_tag="", exclude_tags=None, filter_category="", filter_verified=False, filter_unofficial=False, filter_format="", filter_imod="", org_slug="", filter_year=""):
    parts = []
    if filter_tag:
        for t in filter_tag.split(",") if isinstance(filter_tag, str) else [filter_tag]:
            if t:
                from urllib.parse import quote
                parts.append(f"tag={quote(t)}")
    if exclude_tags:
        for t in exclude_tags.split(",") if isinstance(exclude_tags, str) else exclude_tags:
            if t:
                from urllib.parse import quote
                parts.append(f"exclude_tag={quote(t)}")
    if filter_category:
        from urllib.parse import quote
        parts.append(f"category={quote(filter_category)}")
    if filter_verified:
        parts.append("verified=1")
    if filter_unofficial:
        parts.append("unofficial=1")
    if filter_format:
        parts.append(f"format_level={filter_format}")
    if filter_imod:
        parts.append(f"imod={filter_imod}")
    if filter_year:
        parts.append(f"year={filter_year}")
    if org_slug:
        parts.append(f"org={org_slug}")
    return "&".join(parts)


def _do_catalogue(catalogue_type, page, per_page=None):
    if per_page is None:
        try:
            from src.admin.settings import get_setting
            per_page = int(get_setting("items_per_page", "30"))
        except Exception:
            per_page = 30
    catalogue = catalogue_type
    if catalogue not in type_map:
        return redirect(url_for("catalogue.catalogue_view", catalogue_type="donnees"))

    if not is_catalogue_enabled(catalogue):
        return redirect(url_for("catalogue.catalogue_view", catalogue_type="donnees"))

    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    filter_imod = request.args.get("imod", "")
    org_slug = request.args.get("org")
    filter_tags = request.args.getlist("tag")
    filter_tag = ",".join(filter_tags) if filter_tags else request.args.get("tag", "")
    filter_category = request.args.get("category", "")
    filter_year = request.args.get("year", "")
    format_param = request.args.get("format", "")
    search_query = request.args.get("q", "").strip()
    exclude_tags = request.args.getlist("exclude_tag")
    exclude_tag_display = ",".join(exclude_tags) if exclude_tags else ""

    query = _build_filtered_query(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, filter_imod, filter_tags or filter_tag, filter_category, search_query, exclude_tags, filter_year)

    # Le score IMOD est persisté (colonne imod_score) : le tri et la pagination
    # sont réalisés en SQL, évitant de charger et trier toute la collection en mémoire.
    score_col = func.coalesce(Item.imod_score, 0)
    if filter_imod == "low":
        query = query.order_by(score_col.asc())
    else:
        query = query.order_by(score_col.desc())

    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)

    if page < 1:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}")
        page = 1
    elif page > total_pages:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}?page={total_pages}")
        page = total_pages

    items_page = query.offset((page - 1) * per_page).limit(per_page).all()
    result_items = [item.to_dict(include_details=True) for item in items_page]

    page_numbers = _build_page_numbers(page, total_pages)

    item_type = type_map.get(catalogue)
    all_categories = (
        PredefinedTagCategory.query
        .join(PredefinedTag, PredefinedTagCategory.id == PredefinedTag.category_id)
        .join(ItemTag, ItemTag.tag == PredefinedTag.name)
        .join(Item, Item.id == ItemTag.item_id)
        .filter(Item.type == item_type)
        .filter(Item.status == "published")
        .filter(PredefinedTagCategory.name != "Types de données")
        .distinct()
        .order_by(PredefinedTagCategory.display_order)
        .all()
    )
    all_category_names = [c.name for c in all_categories]

    urls = _build_catalogue_urls(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, filter_imod, filter_year)
    meta = _CATALOGUE_META[catalogue]

    data = {
        "title": f"A.N.A.N.A.S | {meta['title_prefix']} — Page {page}",
        "meta_description": meta["meta"],
        "canonical_url": request.url_root.rstrip("/") + f"/catalogue/{catalogue}",
        "catalogue_type": catalogue,
        "filter_verified": filter_verified, "filter_unofficial": filter_unofficial,
        "filter_format": filter_format, "filter_imod": filter_imod, "org_slug": org_slug,
        "filter_tag": filter_tag, "filter_category": filter_category,
        "filter_year": filter_year,
        "exclude_tags": exclude_tag_display,
        "filter_qs_all": _build_filter_qs(
            filter_tag="", exclude_tags="",
            filter_category=filter_category,
            filter_verified=filter_verified, filter_unofficial=filter_unofficial,
            filter_format=filter_format, filter_imod=filter_imod, org_slug=org_slug,
            filter_year=filter_year
        ),
        "filter_qs_no_exclude": _build_filter_qs(
            filter_tag=filter_tag, exclude_tags="",
            filter_category=filter_category,
            filter_verified=filter_verified, filter_unofficial=filter_unofficial,
            filter_format=filter_format, filter_imod=filter_imod, org_slug=org_slug,
            filter_year=filter_year
        ),
        "filter_qs_no_tag": _build_filter_qs(
            filter_tag="", exclude_tags=exclude_tag_display,
            filter_category=filter_category,
            filter_verified=filter_verified, filter_unofficial=filter_unofficial,
            filter_format=filter_format, filter_imod=filter_imod, org_slug=org_slug,
            filter_year=filter_year
        ),
        "filter_qs_no_category": _build_filter_qs(
            filter_tag=filter_tag, exclude_tags=exclude_tag_display,
            filter_category="",
            filter_verified=filter_verified, filter_unofficial=filter_unofficial,
            filter_format=filter_format, filter_imod=filter_imod, org_slug=org_slug,
            filter_year=filter_year
        ),
        "filter_qs_no_year": _build_filter_qs(
            filter_tag=filter_tag, exclude_tags=exclude_tag_display,
            filter_category=filter_category,
            filter_verified=filter_verified, filter_unofficial=filter_unofficial,
            filter_format=filter_format, filter_imod=filter_imod, org_slug=org_slug,
            filter_year=""
        ),
        "search_query": search_query,
        "all_categories": all_category_names,
        **urls,
        "items": result_items, "page": page, "per_page": per_page,
        "total_items": total_items, "total_pages": total_pages, "page_numbers": page_numbers,
    }
    json_data = {k: v for k, v in data.items() if k in ("items", "page", "per_page", "total_items", "total_pages", "page_numbers")}

    if format_param == "json":
        return _make_response(json_data, "json")
    return _make_response(data, "")


def _make_response(data, format_param=""):
    from flask import jsonify as j
    if format_param == "json":
        return j(data)
    return render_template("catalogue.html", **data)


@bp.route("/catalogue/<catalogue_type>")
@bp.route("/catalogue/<catalogue_type>/<int:page>")
def catalogue_view(catalogue_type, page=1):
    if "page" in request.args:
        try:
            page = int(request.args.get("page", 1))
        except (TypeError, ValueError):
            page = 1
    if page < 1:
        return redirect(f"/catalogue/{catalogue_type}")
    return _do_catalogue(catalogue_type, page)


@bp.route("/catalogue/<catalogue_type>/recherche-avancee")
def advanced_search(catalogue_type):
    if catalogue_type not in type_map:
        return redirect(url_for("catalogue.catalogue_view", catalogue_type="donnees"))

    if not is_catalogue_enabled(catalogue_type):
        return redirect(url_for("catalogue.catalogue_view", catalogue_type="donnees"))

    item_type = type_map.get(catalogue_type)

    all_records = (
        db.session.query(PredefinedTag, PredefinedTagCategory)
        .join(PredefinedTagCategory, PredefinedTag.category_id == PredefinedTagCategory.id)
        .join(ItemTag, ItemTag.tag == PredefinedTag.name)
        .join(Item, Item.id == ItemTag.item_id)
        .filter(Item.type == item_type)
        .filter(Item.status == "published")
        .order_by(PredefinedTagCategory.display_order, PredefinedTag.display_order)
        .all()
    )

    seen_names = set()
    tag_data_dict = {}
    for tag, cat in all_records:
        if tag.name not in seen_names:
            seen_names.add(tag.name)
            if cat.id not in tag_data_dict:
                tag_data_dict[cat.id] = {"category": cat, "tags": []}
            tag_data_dict[cat.id]["tags"].append(tag)

    tag_data = sorted(tag_data_dict.values(), key=lambda x: x["category"].display_order)

    meta = _CATALOGUE_META[catalogue_type]
    search_query = request.args.get("q", "").strip()

    return render_template(
        "advanced_search.html",
        title=f"A.N.A.N.A.S | Recherche avancée — {meta['title_prefix']}",
        meta_description=f"Affinez votre recherche dans le catalogue avec des filtres par étiquettes — {meta['meta']}",
        catalogue_type=catalogue_type,
        tag_categories=tag_data,
        search_query=search_query,
    )


@bp.route("/catalogue/<catalogue_type>/<int:page>/json")
def catalogue_json_view(catalogue_type, page):

    if catalogue_type not in type_map:
        return redirect(url_for("catalogue.catalogue_view", catalogue_type="donnees"))

    try:
        from src.admin.settings import get_setting
        per_page = int(get_setting("catalogue_per_page", "20"))
    except Exception:
        per_page = 20

    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    org_slug = request.args.get("org")
    filter_tag = request.args.getlist("tag") or request.args.get("tag", "")
    filter_category = request.args.get("category", "")
    filter_year = request.args.get("year", "")

    query = _build_filtered_query(catalogue_type, filter_verified, filter_unofficial, filter_format, org_slug, filter_tag=filter_tag, filter_category=filter_category, filter_year=filter_year)
    items, page, total_items, total_pages, page_numbers = _paginate(query, page, per_page)
    result_items = [item.to_dict() for item in items]

    return {
        "items": result_items, "page": page, "per_page": per_page,
        "total_items": total_items, "total_pages": total_pages, "page_numbers": page_numbers,
    }, 200, {"Content-Type": "application/json"}