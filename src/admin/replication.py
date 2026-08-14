import json

from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _log_audit, _get_json_data, get_current_user, _CATALOGUES_INFO, CATALOGUE_TYPE_MAP
from utils.security import sanitize_html, validate_external_url
from models import User, Item, ItemGallery, ItemTag, PredefinedTag, PredefinedTagCategory


@bp.route("/api/admin/replication/fetch", methods=["POST"])
@login_required
@api_admin_required
def replication_fetch():

    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
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

    import urllib.request
    import urllib.error
    import ssl
    import datetime as dt

    ctx = ssl.create_default_context()
    current_user = get_current_user()
    created = []
    skipped = []
    errors = []

    def _fetch_json(url):
        req = urllib.request.Request(url, headers={"User-Agent": "ANANAS-Replicator/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))

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
                title = item_data.get("title", "")
                if not title:
                    continue

                existing = Item.query.filter_by(magnet_link=magnet, type=item_type).first() if magnet else None

                if existing:
                    skipped.append({"title": title, "type": item_type, "reason": "déjà présent (même aimant)"})
                    continue

                if Item.query.filter_by(title=title, type=item_type).first():
                    skipped.append({"title": title, "type": item_type, "reason": "déjà présent (même titre)"})
                    continue

                new_item = Item(
                    type=item_type, title=sanitize_html(title),
                    description=sanitize_html(item_data.get("description", "")),
                    format_type=item_data.get("format"), magnet_link=magnet,
                    image_path=item_data.get("image", "/static/images/logo/ANANAS.png"),
                    author_name=sanitize_html(item_data.get("author")) if item_data.get("author") else None,
                    data_format_level=item_data.get("data_format_level", "individual"),
                    license_type=item_data.get("license_type"),
                    pdf_magnet_link=item_data.get("pdf_doc") or item_data.get("pdf_magnet_link"),
                    metadata_json=item_data.get("magnet_links") if isinstance(item_data.get("magnet_links"), list) else None,
                    image_magnets_pending=item_data.get("image_magnets_pending", False),
                    image_magnets_total=item_data.get("image_magnets_total", 0),
                    image_magnet_links=item_data.get("image_magnets") if isinstance(item_data.get("image_magnets"), list) else None,
                    created_at=_parse_date(item_data.get("created_at")),
                    verification_status="unofficial", status="published",
                )
                db.session.add(new_item)
                db.session.flush()

                for tag_name in item_data.get("tags", []):
                    db.session.add(ItemTag(item_id=new_item.id, tag=sanitize_html(tag_name)))

                for group in item_data.get("grouped_categories", []):
                    cat_name = sanitize_html(group.get("category", ""))
                    if not cat_name:
                        continue
                    cat = PredefinedTagCategory.query.filter_by(name=cat_name).first()
                    if not cat:
                        cat = PredefinedTagCategory(name=cat_name)
                        db.session.add(cat)
                        db.session.flush()
                    for tag_name in group.get("tags", []):
                        tag_name_clean = sanitize_html(tag_name)
                        if not PredefinedTag.query.filter_by(category_id=cat.id, name=tag_name_clean).first():
                            db.session.add(PredefinedTag(category_id=cat.id, name=tag_name_clean))

                for gallery_entry in item_data.get("gallery", []):
                    media_type = gallery_entry.get("type")
                    if media_type:
                        db.session.add(ItemGallery(
                            item_id=new_item.id, media_type=media_type,
                            src=gallery_entry.get("src"),
                            label=sanitize_html(gallery_entry.get("label")) if gallery_entry.get("label") else None,
                            data_json=gallery_entry.get("data") if isinstance(gallery_entry.get("data"), dict) else None,
                        ))

                for vl in item_data.get("visualization_links", []):
                    db.session.add(VisualizationLink(
                        parent_item_id=new_item.id, name=sanitize_html(vl.get("name", "")),
                        url=sanitize_html(vl.get("url", "")),
                        link_type=vl.get("link_type", "external"),
                        description=sanitize_html(vl.get("description")) if vl.get("description") else None,
                        display_order=vl.get("display_order", 0), is_active=vl.get("is_active", True),
                    ))

                for dc in item_data.get("data_chunks", []):
                    db.session.add(DataChunk(
                        parent_item_id=new_item.id, name=sanitize_html(dc.get("name", "")),
                        description=sanitize_html(dc.get("description")) if dc.get("description") else None,
                        format_type=dc.get("format_type"), magnet_link=dc.get("magnet_link"),
                        data_url=dc.get("data_url"),
                        metadata_json=dc.get("metadata_json") if isinstance(dc.get("metadata_json"), dict) else None,
                        owner_user_id=current_user.id,
                    ))

                created.append({"title": title, "type": item_type, "id": new_item.id})
            page += 1

    db.session.commit()
    _log_audit("replication", "replication", details={
        "url": remote_url, "types": selected_types,
        "created_count": len(created), "skipped_count": len(skipped), "error_count": len(errors),
    })
    return jsonify({
        "status": "completed", "created": created, "skipped": skipped, "errors": errors,
        "created_count": len(created), "skipped_count": len(skipped), "error_count": len(errors),
    })


@bp.route("/api/admin/replication/preview", methods=["POST"])
@login_required
@api_admin_required
def replication_preview():
    data = _get_json_data()
    if data is None:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    remote_url = (data.get("url") or "").strip().rstrip("/")

    if not remote_url:
        return jsonify({"error": "URL requise."}), 400
    if not validate_external_url(remote_url):
        return jsonify({"error": "URL distante invalide ou non autorisée."}), 400
    import urllib.request
    import urllib.error
    import ssl

    ctx = ssl.create_default_context()
    result = []
    for cat_type, item_type in CATALOGUE_TYPE_MAP.items():
        json_url = f"{remote_url}/catalogue/{cat_type}/1/json"
        try:
            req = urllib.request.Request(json_url, headers={"User-Agent": "ANANAS-Replicator/1.0"})
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                catalog_data = json.loads(resp.read().decode("utf-8"))
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