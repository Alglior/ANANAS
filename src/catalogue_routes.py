from flask import Blueprint, request, render_template, redirect, url_for
from werkzeug.routing import BaseConverter
from models import Organization
from src.admin_routes import is_catalogue_enabled, _CATALOGUES_INFO

_CATALOGUE_META = {
    "donnees": {
        "title_prefix": "Catalogue des géodonnées",
        "meta": "Parcourez le catalogue complet des géodonnées A.N.A.N.A.S.",
    },
    "cartes": {
        "title_prefix": "Catalogue des cartes",
        "meta": "Explorez la collection de cartes et produits cartographiques A.N.A.N.A.S.",
    },
    "applications": {
        "title_prefix": "Catalogue d'applications",
        "meta": "Découvrez les applications et services web géospatiaux A.N.A.N.A.S.",
    },
}

type_map = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}

bp = Blueprint("catalogue", __name__)


class CatalogueTypeConverter(BaseConverter):
    def to_url(self, value):
        return value

    def to_python(self, value):
        valid_types = ["donnees", "cartes", "applications"]
        if value not in valid_types:
            raise ValueError()
        return value


def _make_response(data, format_param=""):
    from flask import jsonify as j

    if format_param == "json":
        return j(data)
    return render_template("catalogue.html", **data)


def _do_catalogue(catalogue_type, page, per_page=30):
    catalogue = catalogue_type
    if catalogue not in type_map:
        return redirect(url_for("catalogue.catalogue_index"))

    if not is_catalogue_enabled(catalogue):
        return redirect(url_for("catalogue.catalogue_index"))

    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    org_slug = request.args.get("org")
    format_param = request.args.get("format", "")

    meta = _CATALOGUE_META[catalogue]
    from models import Item, Organization

    item_type = type_map[catalogue]
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

    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    requested_page = page
    if requested_page < 1:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}")
        page = 1
    elif requested_page > total_pages:
        if format_param != "json":
            return redirect(f"/catalogue/{catalogue}?page={total_pages}")
        page = total_pages
    else:
        page = requested_page

    items = query.offset((page - 1) * per_page).limit(per_page).all()
    result_items = [item.to_dict() for item in items]
    from src.shared import _build_page_numbers
    page_numbers = _build_page_numbers(page, total_pages)

    base = "/catalogue/" + catalogue
    # Pre-build all filter URLs combining left+right params
    def _build_url(base, include_verif=False, include_unofficial=False, include_format=None):
        parts = []
        if include_verif:
            parts.append("verified=1")
        elif include_unofficial:
            parts.append("unofficial=1")
        if include_format:
            parts.append("format_level=" + include_format)
        if org_slug:
            parts.append("org=" + org_slug)
        return base + ("?" + "&".join(parts) if parts else "")

    url_all = base
    url_verified = _build_url(base, include_verif=True, include_format=filter_format or None)
    url_unofficial = _build_url(base, include_unofficial=True, include_format=filter_format or None)
    url_pack = _build_url(base, include_verif=filter_verified, include_unofficial=filter_unofficial, include_format="pack")
    url_ind = _build_url(base, include_verif=filter_verified, include_unofficial=filter_unofficial, include_format="individual")

    data = {
        "title": f"A.N.A.N.A.S. | {meta['title_prefix']} — Page {page}",
        "meta_description": meta["meta"],
        "catalogue_type": catalogue,
        "filter_verified": filter_verified,
        "filter_unofficial": filter_unofficial,
        "filter_format": filter_format,
        "org_slug": org_slug,
        "url_all": url_all,
        "url_verified": url_verified,
        "url_unofficial": url_unofficial,
        "url_pack": url_pack,
        "url_ind": url_ind,
        "items": result_items,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }
    json_data = {
        "items": result_items,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }

    if format_param == "json":
        return _make_response(json_data, "json")
    return _make_response(data, "")


# /catalogue route is handled by app.py with endpoint="catalogue" for template compatibility.


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
    from flask import url_for
    from models import Item

    if catalogue_type not in type_map:
        return redirect(url_for("catalogue.catalogue_index"))

    per_page = 20
    item_type = type_map[catalogue_type]
    total_items = Item.query.filter_by(type=item_type).count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1

    catalogue = catalogue_type
    filter_verified = request.args.get("verified") == "1"
    filter_unofficial = request.args.get("unofficial") == "1"
    filter_format = request.args.get("format_level", "")
    org_slug = request.args.get("org")

    meta = _CATALOGUE_META[catalogue]
    base = "/catalogue/" + catalogue
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

    items = query.offset((page - 1) * per_page).limit(per_page).all()
    result_items = [item.to_dict() for item in items]
    from src.shared import _build_page_numbers
    page_numbers = _build_page_numbers(page, total_pages)

    return {
        "items": result_items,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }, 200, {"Content-Type": "application/json"}


def register_catalogue(app):
    app.url_map.converters["catalogue_type"] = CatalogueTypeConverter
