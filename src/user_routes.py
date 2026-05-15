import datetime
import os
import re
from pathlib import Path

from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from app import db
from src.shared import login_required, get_current_user
from models import User, Rating, Comment, Item, DataChunk, UserUpload, VisualizationLink
from utils.security import validate_file_magic

bp = Blueprint("users", __name__)

ALLOWED_EXTENSIONS = {"csv", "shp", "geojson", "gpkg", "json", "xml"}


def is_allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@bp.route("/profil")
@login_required
def profil_page():
    current_user = get_current_user()

    rating_count = (
        db.session.query(func.count(Rating.id))
        .filter(Rating.user_id == current_user.id)
        .scalar()
    )

    org_memberships = [m for m in current_user.organizations if m.is_active]

    data_chunks = (
        db.session.query(DataChunk, Item.title.label("parent_title"), Item.type.label("parent_type"))
        .outerjoin(Item, DataChunk.parent_item_id == Item.id)
        .filter(DataChunk.owner_user_id == current_user.id)
        .order_by(DataChunk.created_at.desc())
        .all()
    )

    uploaded_items = (
        db.session.query(Item)
        .filter(Item.author_name.like(f"{current_user.prenom} {current_user.nom}%"))
        .order_by(Item.created_at.desc())
        .all()
    )

    return render_template(
        "users/profil.html",
        title="A.N.A.N.A.S. | Mon profil",
        meta_description="Consultez et modifiez votre profil A.N.A.N.A.S.",
        user=current_user,
        rating_count=rating_count,
        org_memberships=org_memberships,
        data_chunks=data_chunks,
        uploaded_items=uploaded_items,
    )


@bp.route("/upload")
@login_required
def upload_page():
    current_user = get_current_user()

    return render_template(
        "users/upload.html",
        title="A.N.A.N.A.S. | Publier des données",
        meta_description="Publiez et partagez des géodonnées sur A.N.A.N.A.S.",
        current_user=current_user,
    )


@bp.route("/activite")
@login_required
def activite_page():
    current_user = get_current_user()

    ratings_query = (
        db.session.query(Rating, Item.title.label("item_title"), Item.type.label("item_type"))
        .join(Item, Rating.item_id == Item.id)
        .filter(Rating.user_id == current_user.id)
        .order_by(Rating.rating.desc())
        .all()
    )

    comments_query = (
        db.session.query(Comment, Item.title.label("item_title"), Item.type.label("item_type"))
        .join(Item, Comment.item_id == Item.id)
        .filter(Comment.created_at != None)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return render_template(
        "users/activite.html",
        title="A.N.A.N.A.S. | Mon activité",
        meta_description="Consultez votre historique d'activité A.N.A.N.A.S.",
        current_user=current_user,
        ratings=ratings_query,
        comments=comments_query,
    )


@bp.route("/api/users/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json()

    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Utilisateur non trouvé"}), 401

    prenom = data.get("prenom", "").strip()
    nom = data.get("nom", "").strip()
    email = data.get("email", "").strip()

    if not prenom or not nom:
        return jsonify({"error": "Le prénom et le nom sont requis"}), 400

    existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing_user:
        return jsonify({"error": "Cet e-mail est déjà utilisé par un autre compte"}), 400

    current_user.prenom = prenom
    current_user.nom = nom
    current_user.email = email

    db.session.commit()

    return jsonify({
        "message": "Profil mis à jour avec succès",
        "user": {
            "prenom": current_user.prenom,
            "nom": current_user.nom,
            "email": current_user.email,
        },
    })


@bp.route("/api/users/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()

    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Utilisateur non trouvé"}), 401

    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if not current_pw or not new_pw:
        return jsonify({"error": "Mot de passe actuel et nouveau mot de passe requis"}), 400

    if not check_password_hash(current_user.password_hash, current_pw):
        return jsonify({"error": "Mot de passe actuel incorrect"}), 401

    strength_ok, errors = validate_password_strength(new_pw)
    if not strength_ok:
        return jsonify({"error": "Mot de passe trop faible", "details": errors}), 400

    current_user.password_hash = generate_password_hash(new_pw, method="scrypt")
    db.session.commit()

    return jsonify({"message": "Mot de passe modifié avec succès"})


def validate_password_strength(password: str):
    errors = []
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères")
    if not re.search(r"[A-Z]", password):
        errors.append("Le mot de passe doit contenir au moins une majuscule")
    if not re.search(r"[a-z]", password):
        errors.append("Le mot de passe doit contenir au moins une minuscule")
    if not re.search(r"\d", password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    if not re.search(r"[!@#$%^&*()_+\-={}\[\];':\"\\|,.<>/?~`]", password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...)")
    return len(errors) == 0, errors


@bp.route("/api/upload/file", methods=["POST"])
@login_required
def upload_file():
    data_text = request.form.get("data_text", "").strip()
    parent_item_id = request.form.get("parent_item_id")
    zoom_level = request.form.get("zoom_level", "").strip()
    data_format_level = request.form.get("data_format_level", "individual")

    if not data_text:
        return jsonify({"error": "Données requises"}), 400

    if data_format_level not in ("pack", "individual"):
        return jsonify({"error": "data_format_level doit être 'pack' ou 'individual'"}), 400

    current_user = get_current_user()
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
        upload_status="pending",
        size_mb=len(data_text.encode('utf-8')) // (1024 * 1024),
        metadata_json=metadata,
    )
    db.session.add(chunk)
    db.session.commit()

    upload.chunk_id = chunk.id
    db.session.commit()

    if parent_item_id:
        db.session.commit()

    return jsonify({"status": "queued", "upload_id": upload.id, "chunk_id": chunk.id})


@bp.route("/api/upload/item", methods=["POST"])
@login_required
def create_upload_item():
    from models import Item, VisualizationLink, DataChunk

    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or request.form.get("title", "")).strip()
    description = (data.get("description") or request.form.get("description", "")).strip()
    item_type = data.get("type") or request.form.get("type", "geodonnee")
    format_type = data.get("format_type") or request.form.get("format_type", "")
    organization_id = data.get("organization_id") or request.form.get("organization_id", type=int)
    data_format_level = (data.get("data_format_level") or request.form.get("data_format_level", "individual"))
    magnet_link = ((data.get("magnet_link") or request.form.get("magnet_link", "")).strip())

    if not title:
        return jsonify({"error": "Titre requis"}), 400

    if data_format_level not in ("pack", "individual"):
        return jsonify({"error": "data_format_level doit être 'pack' ou 'individual'"}), 400

    item = Item(
        type=item_type,
        title=title[:300],
        description=description[:2000],
        format_type=format_type[:50] if format_type else None,
        magnet_link=magnet_link[:500] if data_format_level == "pack" else "",
        author_name=f"{current_user.prenom} {current_user.nom}",
        organization_id=organization_id if organization_id else None,
        data_format_level=data_format_level,
    )
    db.session.add(item)
    db.session.commit()

    # Link the preview chunk to this item (created by upload_file route)
    preview_chunk = DataChunk.query.filter_by(
        owner_user_id=current_user.id,
        parent_item_id=None,
        upload_status="pending",
    ).order_by(DataChunk.created_at.desc()).first()
    if preview_chunk:
        preview_chunk.parent_item_id = item.id

    # Create chunks for individual format magnet links
    if data_format_level == "individual":
        magnet_links = data.get("magnet_links") or request.form.getlist("magnet_link[]")
        zoom_levels = data.get("zoom_levels") or request.form.getlist("zoom_level[]")
        for i, ml in enumerate(magnet_links):
            ml_val = ml if isinstance(ml, dict) else (ml or "")
            zl_val = zoom_levels[i] if i < len(zoom_levels) else ""
            if isinstance(ml_val, dict):
                mag = ml_val.get("magnet_link", "")
                zlm = ml_val.get("zoom_level", "")
            else:
                mag = ml_val
                zlm = zl_val
            if mag:
                chunk = DataChunk(
                    parent_item_id=item.id,
                    name=f"chunk_{item.id}_{i}",
                    owner_user_id=current_user.id,
                    upload_status="pending",
                    magnet_link=mag[:500],
                    size_mb=1,
                    metadata_json={"zoom_level": zlm},
                )
                db.session.add(chunk)

    # Add viz link if provided in the upload data
    viz_name = data.get("viz_link_name") or request.form.get("viz_link_name", "").strip()
    viz_url = data.get("viz_link_url") or request.form.get("viz_link_url", "").strip()
    from app import validate_external_url
    if viz_name and viz_url and validate_external_url(viz_url):
        link = VisualizationLink(
            parent_item_id=item.id,
            name=viz_name[:200],
            url=viz_url,
            owner_user_id=current_user.id,
            link_type='external',
            display_order=0,
        )
        db.session.add(link)

    db.session.commit()

    return jsonify({"status": "created", "id": item.id})


@bp.route("/api/items/<int:item_id>/viz-links", methods=["POST"])
@login_required
def add_viz_link(item_id):
    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    link_type = data.get("link_type", "external")

    if not name or not url:
        return jsonify({"error": "Nom et URL requis"}), 400

    from app import validate_external_url

    if link_type not in ("external", "internal", "embed", "widget"):
        return jsonify({"error": "Type de lien invalide"}), 400

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
