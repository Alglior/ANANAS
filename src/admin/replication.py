import json
import re

import bleach
import html as html_module

from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _log_audit, _require_json, get_current_user, _CATALOGUES_INFO, CATALOGUE_TYPE_MAP
from utils.security import sanitize_html, validate_external_url
from models import User, Item, ItemGallery, ItemTag, VisualizationLink, DataChunk, PredefinedTag, PredefinedTagCategory, Organization

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5 Mo
MAX_URL_REDIRECTS = 3


def _plain_text(value, default=""):
    """Nettoie un texte en supprimant les balises HTML SANS échapper les entités.

    `sanitize_html` (bleach) transforme « & » en « &amp; » : pour les libellés
    stockés puis rendus avec autoescape (templates), l'encodage doit être conservé
    tel quel. Les balises restent néanmoins supprimées pour la défense en profondeur.
    """
    if value is None:
        return default
    if not isinstance(value, str):
        value = str(value)
    return html_module.unescape(bleach.clean(value, tags=[], strip=True))


def _get_or_create_organization(organization_name, current_user):
    """Retrouve ou crée localement l'organisation portée par l'item distant."""
    name = _plain_text(organization_name).strip()[:100]
    if not name:
        return None
    org = Organization.query.filter_by(name=name).first()
    if org:
        return org.id
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")[:80] or "org"
    base = slug
    i = 2
    while Organization.query.filter_by(slug=slug).first():
        slug = f"{base[:78]}-{i}"
        i += 1
    org = Organization(name=name, slug=slug, created_by=current_user.id, is_active=True)
    db.session.add(org)
    db.session.flush()
    return org.id


def _parse_int_year(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except (ValueError, TypeError):
            return None
    return None


_VERIFICATION_STATUSES = {"verified", "unofficial", "rejected"}


def _parse_verification_status(value):
    """Réplique le statut de vérification distant en le bornant aux valeurs connues."""
    if isinstance(value, str) and value in _VERIFICATION_STATUSES:
        return value
    return "unofficial"


def _is_unsafe_host(hostname):
    """Rejette les hôtes résolvant vers des adresses privées/réservées (anti-SSRF)."""
    import socket
    import ipaddress
    try:
        infos = socket.getaddrinfo(hostname, None)
    except OSError:
        return True
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local or addr.is_multicast or addr.is_unspecified:
                return True
        except ValueError:
            return True
    return False


def _normalize_image_magnets(item_data):
    """Reconstruit une liste normalisée {magnet_link, label} depuis l'export distant.

    Déduplique par lien magnet : un même aimant ne doit produire qu'une seule
    image en galerie (évite les doublons hérités d'un item distant déjà pollué).
    """
    from src.image_cache import normalize_image_magnets
    if not isinstance(item_data.get("image_magnets"), list):
        return []
    return normalize_image_magnets(item_data.get("image_magnets"))


def _fetch_json(url):
    import urllib.request
    import urllib.error
    import ssl
    import socket

    if not validate_external_url(url):
        raise urllib.error.URLError("URL invalide ou non autorisée.")
    from urllib.parse import urlparse
    hostname = urlparse(url).hostname
    if hostname and _is_unsafe_host(hostname):
        raise urllib.error.URLError("Hôte distant non autorisé.")

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "ANANAS-Replicator/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        data = resp.read(MAX_PAYLOAD_SIZE + 1)
        if len(data) > MAX_PAYLOAD_SIZE:
            raise urllib.error.URLError("Réponse trop volumineuse.")
        return json.loads(data.decode("utf-8"))


@bp.route("/api/admin/replication/fetch", methods=["POST"])
@login_required
@api_admin_required
def replication_fetch():

    data, error, code = _require_json()
    if error:
        return error, code
    remote_url = (data.get("url") or "").strip().rstrip("/")
    selected_types = data.get("types", [])

    if not remote_url:
        return jsonify({"error": "URL requise."}), 400
    if not validate_external_url(remote_url):
        return jsonify({"error": "URL distante invalide ou non autorisée."}), 400
    if not selected_types:
        return jsonify({"error": "Sélectionnez au moins un type de catalogue."}), 400

    valid_types = [t for t in selected_types if t in CATALOGUE_TYPE_MAP]
    if not valid_types:
        return jsonify({"error": "Types de catalogue invalides."}), 400

    import datetime as dt

    current_user = get_current_user()
    created = []
    skipped = []
    errors = []
    to_process = []  # (item_id, image_magnets) à traiter après le commit

    def _parse_date(date_str):
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            return dt.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    for cat_type in valid_types:
        item_type = CATALOGUE_TYPE_MAP[cat_type]
        page = 1
        total_pages = 1

        while page <= total_pages:
            json_url = f"{remote_url}/catalogue/{cat_type}/{page}/json"
            try:
                catalog_data = _fetch_json(json_url)
            except Exception as e:
                errors.append(f"Impossible de récupérer {json_url} : {str(e)}")
                break

            total_pages = catalog_data.get("total_pages", 1)
            items = catalog_data.get("items", [])

            for item_data in items:
                magnet = item_data.get("magnet", "")
                title = _plain_text(item_data.get("title", ""))
                if not title:
                    continue

                existing = Item.query.filter_by(magnet_link=magnet, type=item_type).first() if magnet else None

                if existing:
                    skipped.append({"title": title, "type": item_type, "reason": "déjà présent (même aimant)"})
                    continue

                if Item.query.filter_by(title=title, type=item_type).first():
                    skipped.append({"title": title, "type": item_type, "reason": "déjà présent (même titre)"})
                    continue

                image_magnets = _normalize_image_magnets(item_data)
                # L'image distante (vitrée par instance) n'est jamais copiée :
                # le fallback local sert d'attente, puis la 1ère image magnet
                # téléchargée localement la remplace.
                remote_image = "/static/images/logo/ANANAS.png"
                organization_id = _get_or_create_organization(
                    item_data.get("organization_name") or item_data.get("organization"),
                    current_user,
                )

                new_item = Item(
                    type=item_type, title=title,
                    description=_plain_text(item_data.get("description", "")),
                    format_type=_plain_text(item_data.get("format")) if item_data.get("format") else None,
                    magnet_link=magnet,
                    size=item_data.get("size") or None,
                    image_path=remote_image,
                    author_name=_plain_text(item_data.get("author")) if item_data.get("author") else None,
                    organization_id=organization_id,
                    data_format_level=item_data.get("data_format_level", "individual"),
                    license_type=item_data.get("license_type"),
                    pdf_magnet_link=item_data.get("pdf_doc") or item_data.get("pdf_magnet_link"),
                    metadata_json=item_data.get("magnet_links") if isinstance(item_data.get("magnet_links"), list) else None,
                    image_magnets_pending=bool(image_magnets),
                    image_magnets_total=len(image_magnets),
                    image_magnet_links=image_magnets,
                    data_year_start=_parse_int_year(item_data.get("data_year_start")),
                    data_year_end=_parse_int_year(item_data.get("data_year_end")),
                    created_at=_parse_date(item_data.get("created_at")),
                    verification_status=_parse_verification_status(item_data.get("verification_status")),
                    verified_at=_parse_date(item_data.get("verified_at")),
                    verification_notes=_plain_text(item_data.get("verification_notes")) if item_data.get("verification_notes") else None,
                    status="published",
                )
                db.session.add(new_item)
                db.session.flush()

                predefined_names = {pt.name for pt in db.session.query(PredefinedTag.name).distinct().all()}
                for tag_name in item_data.get("tags", []):
                    cleaned = _plain_text(tag_name)
                    if cleaned and cleaned in predefined_names:
                        db.session.add(ItemTag(item_id=new_item.id, tag=cleaned))

                for group in item_data.get("grouped_categories", []):
                    cat_name = _plain_text(group.get("category", ""))
                    if not cat_name:
                        continue
                    cat = PredefinedTagCategory.query.filter_by(name=cat_name).first()
                    if not cat:
                        cat = PredefinedTagCategory(name=cat_name)
                        db.session.add(cat)
                        db.session.flush()
                    for tag_name in group.get("tags", []):
                        tag_name_clean = _plain_text(tag_name)
                        if not PredefinedTag.query.filter_by(category_id=cat.id, name=tag_name_clean).first():
                            db.session.add(PredefinedTag(category_id=cat.id, name=tag_name_clean))

                for gallery_entry in item_data.get("gallery", []):
                    media_type = gallery_entry.get("type")
                    if media_type and media_type != "image":
                        db.session.add(ItemGallery(
                            item_id=new_item.id, media_type=media_type,
                            src=gallery_entry.get("src"),
                            label=_plain_text(gallery_entry.get("label")) if gallery_entry.get("label") else None,
                            data_json=gallery_entry.get("data") if isinstance(gallery_entry.get("data"), dict) else None,
                        ))

                for vl in item_data.get("visualization_links", []):
                    db.session.add(VisualizationLink(
                        parent_item_id=new_item.id, name=_plain_text(vl.get("name", "")),
                        url=sanitize_html(vl.get("url", "")),
                        link_type=vl.get("link_type", "external"),
                        description=_plain_text(vl.get("description")) if vl.get("description") else None,
                        display_order=vl.get("display_order", 0), is_active=vl.get("is_active", True),
                    ))

                for dc in item_data.get("data_chunks", []):
                    db.session.add(DataChunk(
                        parent_item_id=new_item.id, name=_plain_text(dc.get("name", "")),
                        description=_plain_text(dc.get("description")) if dc.get("description") else None,
                        format_type=dc.get("format_type"), magnet_link=dc.get("magnet_link"),
                        data_url=dc.get("data_url"),
                        metadata_json=dc.get("metadata_json") if isinstance(dc.get("metadata_json"), dict) else None,
                        owner_user_id=current_user.id,
                    ))

                if image_magnets:
                    to_process.append((new_item.id, image_magnets))
                created.append({"title": title, "type": item_type, "id": new_item.id})
            page += 1

    db.session.commit()

    for item_id, image_magnets in to_process:
        from src.user_routes import _process_image_magnets_async
        _process_image_magnets_async(item_id, image_magnets)

    _log_audit("replication", "replication", details={
        "url": remote_url, "types": selected_types,
        "created_count": len(created), "skipped_count": len(skipped), "error_count": len(errors),
        "image_process_started": len(to_process),
    })
    return jsonify({
        "status": "completed", "created": created, "skipped": skipped, "errors": errors,
        "created_count": len(created), "skipped_count": len(skipped), "error_count": len(errors),
    })


@bp.route("/api/admin/replication/preview", methods=["POST"])
@login_required
@api_admin_required
def replication_preview():
    data, error, code = _require_json()
    if error:
        return error, code
    remote_url = (data.get("url") or "").strip().rstrip("/")

    if not remote_url:
        return jsonify({"error": "URL requise."}), 400
    if not validate_external_url(remote_url):
        return jsonify({"error": "URL distante invalide ou non autorisée."}), 400
    result = []
    for cat_type, item_type in CATALOGUE_TYPE_MAP.items():
        json_url = f"{remote_url}/catalogue/{cat_type}/1/json"
        try:
            catalog_data = _fetch_json(json_url)
            result.append({
                "type": cat_type,
                "label": next((i["label"] for i in _CATALOGUES_INFO if i["type"] == cat_type), cat_type),
                "total_items": catalog_data.get("total_items", 0), "reachable": True,
            })
        except Exception:
            result.append({
                "type": cat_type,
                "label": next((i["label"] for i in _CATALOGUES_INFO if i["type"] == cat_type), cat_type),
                "total_items": 0, "reachable": False,
            })

    return jsonify({"catalogues": result})