from flask import Blueprint, request, render_template, redirect, url_for
from werkzeug.routing import BaseConverter
from models import Organization
from src.admin import is_catalogue_enabled

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

type_map = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}

bp = Blueprint("catalogue", __name__)


class CatalogueTypeConverter(BaseConverter):
    def to_url(self, value):
        return value

    def to_python(self, value):
        if value not in type_map:
            raise ValueError()
        return value


def _build_filtered_query(catalogue_type, filter_verified=False, filter_unofficial=False, filter_format="", org_slug=None, filter_imod="", filter_tag=None, filter_category=None):
    from models import Item

    item_type = type_map.get(catalogue_type)
    if not item_type:
        return None

    query = Item.query.filter_by(type=item_type).filter(Item.status != "draft")

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
        from models import ItemTag
        from app import db
        sub = db.session.query(ItemTag.item_id).filter(ItemTag.tag == filter_tag).subquery()
        query = query.filter(Item.id.in_(sub))

    if filter_category:
        from models import ItemTag, PredefinedTag, PredefinedTagCategory
        from app import db
        sub = db.session.query(ItemTag.item_id).join(
            PredefinedTag, ItemTag.tag == PredefinedTag.name
        ).join(
            PredefinedTagCategory
        ).filter(PredefinedTagCategory.name == filter_category).subquery()
        query = query.filter(Item.id.in_(sub))

    return query


def _build_catalogue_urls(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, _filter_imod=""):
    base = f"/catalogue/{catalogue}"

    def _build_url(include_verif=False, include_unofficial=False, include_format=None):
        parts = []
        if include_verif:
            parts.append("verified=1")
        elif include_unofficial:
            parts.append("unofficial=1")
        if include_format:
            parts.append(f"format_level={include_format}")
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


def _do_catalogue(catalogue_type, page, per_page=30):
    from models import Item
    catalogue = catalogue_type
    if catalogue not in type_map:
        return redirect(url_for("catalogue.catalogue_index"))

    if not is_catalogue_enabled(catalogue):
        return redirect(url_for("catalogue.catalogue_index"))

    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    filter_imod = request.args.get("imod", "")
    org_slug = request.args.get("org")
    filter_tag = request.args.get("tag", "")
    filter_category = request.args.get("category", "")
    format_param = request.args.get("format", "")

    query = _build_filtered_query(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, filter_imod, filter_tag, filter_category)
    all_items = query.all()

    if filter_imod == "high":
        all_items.sort(key=lambda it: it._compute_imod_score()["score"], reverse=True)
    elif filter_imod == "low":
        all_items.sort(key=lambda it: it._compute_imod_score()["score"])
    else:
        all_items.sort(key=lambda it: it._compute_imod_score()["score"], reverse=True)

    total_items = len(all_items)
    total_pages = max((total_items + per_page - 1) // per_page, 1)

    if page < 1:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}")
        page = 1
    elif page > total_pages:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}?page={total_pages}")
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page
    items_page = all_items[start:end]
    result_items = [item.to_dict(include_details=True) for item in items_page]

    from src.shared import _build_page_numbers
    page_numbers = _build_page_numbers(page, total_pages)

    urls = _build_catalogue_urls(catalogue, filter_verified, filter_unofficial, filter_format, org_slug, filter_imod)
    meta = _CATALOGUE_META[catalogue]

    data = {
        "title": f"A.N.A.N.A.S | {meta['title_prefix']} — Page {page}",
        "meta_description": meta["meta"],
        "catalogue_type": catalogue,
        "filter_verified": filter_verified, "filter_unofficial": filter_unofficial,
        "filter_format": filter_format, "filter_imod": filter_imod, "org_slug": org_slug,
        "filter_tag": filter_tag, "filter_category": filter_category,
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


@bp.route("/catalogue/<catalogue_type>/<int:page>/json")
def catalogue_json_view(catalogue_type, page):
    from models import Item

    if catalogue_type not in type_map:
        return redirect(url_for("catalogue.catalogue_index"))

    per_page = 20
    item_type = type_map[catalogue_type]
    total_items = Item.query.filter_by(type=item_type).count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1

    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    org_slug = request.args.get("org")
    filter_tag = request.args.get("tag", "")
    filter_category = request.args.get("category", "")

    query = _build_filtered_query(catalogue_type, filter_verified, filter_unofficial, filter_format, org_slug, filter_tag=filter_tag, filter_category=filter_category)
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    result_items = [item.to_dict() for item in items]

    from src.shared import _build_page_numbers
    page_numbers = _build_page_numbers(page, total_pages)

    return {
        "items": result_items, "page": page, "per_page": per_page,
        "total_items": total_items, "total_pages": total_pages, "page_numbers": page_numbers,
    }, 200, {"Content-Type": "application/json"}


def register_catalogue(app):
    app.url_map.converters["catalogue_type"] = CatalogueTypeConverter