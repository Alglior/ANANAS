import os
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app import db
from src.shared import login_required, get_current_user, user_owns_item_or_admin
from utils.security import sanitize_html, validate_file_magic

bp = Blueprint("upload", __name__)

ALLOWED_EXTENSIONS = {"csv", "shp", "geojson", "json", "xml"}



def is_allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@bp.route("/api/upload/chunk", methods=["POST"])
@login_required
def upload_chunk():
    from models import DataChunk, UserUpload, Item

    current_user = get_current_user()
    data_text = request.form.get("data_text", "").strip()
    parent_item_id = request.form.get("parent_item_id")
    data_format_level = request.form.get("data_format_level", "individual")
    zoom_level = request.form.get("zoom_level", "").strip()

    if not data_text:
        return jsonify({"error": "Données requises"}), 400

    if data_format_level not in ("pack", "individual"):
        return jsonify({"error": "data_format_level doit être 'pack' ou 'individual'"}), 400

    lines = [line for line in data_text.split('\n')[:50] if line.strip()]

    metadata = {
        "preview_rows": lines,
        "column_count": len(lines[0].split(',')) if lines else 0,
        "zoom_level": zoom_level,
    }

    upload = UserUpload(
        owner_user_id=current_user.id,
        parent_item_id=parent_item_id,
        file_name="preview",
        file_size_bytes=len(data_text.encode('utf-8')),
        mime_type="text/csv",
        original_format="csv",
        processing_status="queued",
    )
    db.session.add(upload)
    db.session.flush()

    chunk = DataChunk(
        parent_item_id=parent_item_id,
        name=f"chunk_{upload.id}",
        owner_user_id=current_user.id,
        metadata_json=metadata,
    )
    db.session.add(chunk)
    db.session.commit()

    upload.chunk_id = chunk.id
    db.session.commit()

    return jsonify({"status": "queued", "upload_id": upload.id, "chunk_id": chunk.id})


@bp.route("/api/items", methods=["POST"])
@login_required
def create_item():
    from models import Item

    current_user = get_current_user()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    item_type = request.form.get("type", "geodonnee")
    format_type = request.form.get("format_type", "")
    magnet_link = request.form.get("magnet_link", "")
    data_format_level = request.form.get("data_format_level", "individual")
    organization_id = request.form.get("organization_id", type=int)

    if not title or not magnet_link:
        return jsonify({"error": "Titre et lien magnet requis"}), 400

    if data_format_level not in ("pack", "individual"):
        return jsonify({"error": "data_format_level doit être 'pack' ou 'individual'"}), 400

    from models import OrganizationMember, Organization
    if organization_id:
        org = db.session.get(Organization, organization_id)
        if not org:
            return jsonify({"error": "Organisation introuvable"}), 404
        if not current_user.is_admin:
            membership = OrganizationMember.query.filter_by(
                user_id=current_user.id, organization_id=organization_id
            ).first()
            if not membership or not membership.is_active:
                return jsonify({"error": "Non autorisé à publier dans cette organisation"}), 403

    item = Item(
        type=item_type,
        title=title[:300],
        description=description[:2000],
        format_type=format_type[:50] if format_type else None,
        magnet_link=magnet_link[:500],
        author_name=sanitize_html(current_user.prenom + " " + current_user.nom),
        organization_id=organization_id if organization_id else None,
        data_format_level=data_format_level,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "created", "id": item.id})


@bp.route("/api/items/<int:item_id>/viz-links", methods=["POST"])
@login_required
def add_viz_link(item_id):
    from models import Item, VisualizationLink

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    if not user_owns_item_or_admin(current_user, item):
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    link_type = data.get("link_type", "external")

    if not name or not url:
        return jsonify({"error": "Nom et URL requis"}), 400

    if link_type not in ("external", "internal", "embed", "widget"):
        return jsonify({"error": "Type de lien invalide"}), 400

    from app import validate_external_url

    if not validate_external_url(url):
        return jsonify({"error": "URL invalide ou non sécurisée"}), 400

    link = VisualizationLink(
        parent_item_id=item_id,
        name=name[:200],
        url=url,
        owner_user_id=current_user.id,
        link_type=link_type,
        display_order=data.get("display_order", 0),
    )
    db.session.add(link)
    db.session.commit()

    return jsonify({"status": "created", "id": link.id})
