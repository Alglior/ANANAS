import os
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app import db
from src.shared import login_required, get_current_user
from utils.security import validate_file_magic

bp = Blueprint("upload", __name__)

ALLOWED_EXTENSIONS = {"csv", "shp", "geojson", "gpkg", "json", "xml"}


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
    file = request.files.get("file")
    parent_item_id = request.form.get("parent_item_id")
    chunk_name = request.form.get("chunk_name", "").strip()
    data_format_level = request.form.get("data_format_level", "individual")
    zoom_level = request.form.get("zoom_level", "").strip()

    if not file or not chunk_name:
        return jsonify({"error": "Fichier et nom requis"}), 400

    if data_format_level not in ("pack", "individual"):
        return jsonify({"error": "data_format_level doit être 'pack' ou 'individual'"}), 400

    if not is_allowed_file(file.filename):
        return jsonify({"error": "Format de fichier non autorisé"}), 400

    safe_name = secure_filename(file.filename)
    file_data = file.read()
    magic_ok, magic_msg = validate_file_magic(file_data, ALLOWED_EXTENSIONS)
    if not magic_ok:
        file.seek(0)
        return jsonify({"error": f"Contenu du fichier invalide: {magic_msg}"}), 400

    file.seek(0)
    upload_path = os.path.join("/uploads", str(current_user.id), safe_name)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)

    file_size = os.getsize(upload_path)
    original_format = Path(file.filename).suffix.lstrip(".")

    if parent_item_id:
        item = Item.query.get(parent_item_id)
        if item:
            item.data_format_level = data_format_level

    upload = UserUpload(
        owner_user_id=current_user.id,
        parent_item_id=parent_item_id,
        file_name=safe_name,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        original_format=original_format,
        processing_status="queued",
    )
    db.session.add(upload)

    metadata = {"original_file": safe_name}
    if data_format_level == "individual" and zoom_level:
        metadata["zoom_level"] = zoom_level

    chunk = DataChunk(
        parent_item_id=parent_item_id,
        name=chunk_name[:200],
        owner_user_id=current_user.id,
        upload_status="pending",
        data_url=f"/uploads/{upload.id}/{safe_name}",
        metadata_json=metadata,
    )
    db.session.add(chunk)
    db.session.commit()

    upload.chunk_id = chunk.id
    db.session.commit()

    if parent_item_id:
        db.session.commit()

    return jsonify({"status": "queued", "upload_id": upload.id})


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

    item = Item(
        type=item_type,
        title=title[:300],
        description=description[:2000],
        format_type=format_type[:50] if format_type else None,
        magnet_link=magnet_link[:500],
        author_name=current_user.prenom + " " + current_user.nom,
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
