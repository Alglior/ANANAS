import datetime
import os
import re
from pathlib import Path

from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from app import db, limiter
from src.shared import login_required, get_current_user, user_owns_item_or_admin
from models import User, Rating, Comment, Item, DataChunk, UserUpload, VisualizationLink, OrganizationMember
from utils.security import sanitize_html, validate_magnet_link

ALLOWED_ITEM_TYPES = {"geodonnee", "carte", "application"}

bp = Blueprint("users", __name__)

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
        .filter(Item.author_name == f"{current_user.prenom} {current_user.nom}")
        .order_by(Item.created_at.desc())
        .all()
    )

    return render_template(
        "users/profil.html",
        title="A.N.A.N.A.S. | Mon profil",
        meta_description="Consultez et modifiez votre profil A.N.A.N.A.S.",
        user=current_user,
        current_user=current_user,
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
        .filter(Comment.user_id == current_user.id)
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
@limiter.limit("10 per hour")
def update_profile():
    data = request.get_json()

    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Utilisateur non trouvé"}), 401

    prenom = sanitize_html(data.get("prenom", "").strip())
    nom = sanitize_html(data.get("nom", "").strip())
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
@limiter.limit("3 per hour")
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


@bp.route("/api/items/<int:item_id>/viz-links", methods=["POST"])
@login_required
def add_viz_link(item_id):
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


@bp.route("/api/upload/file", methods=["POST"])
@login_required
def upload_file():
    current_user = get_current_user()
    data_text = request.form.get("data_text", "").strip()
    title = request.form.get("title", "").strip()
    item_type = request.form.get("type", "geodonnee").strip()
    format_type = request.form.get("format_type", "").strip()
    description = request.form.get("description", "").strip()
    data_format_level = request.form.get("data_format_level", "individual").strip()
    organization_id = request.form.get("organization_id", "").strip()

    if not data_text:
        return jsonify({"error": "Les données sont requises"}), 400
    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    if item_type not in ALLOWED_ITEM_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400

    org_id = int(organization_id) if organization_id and organization_id.isdigit() else None
    if org_id:
        membership = OrganizationMember.query.filter_by(
            user_id=current_user.id,
            organization_id=org_id,
            is_active=True,
        ).first()
        if not membership:
            return jsonify({"error": "Organisation non autorisée"}), 403

    chunk = DataChunk(
        parent_item_id=None,
        name=title,
        owner_user_id=current_user.id,
        description=description or None,
        format_type=format_type or None,
        data_url=data_text[:10000] if len(data_text) <= 10000 else data_text[:5000],
        upload_status="uploaded",
        organization_id=org_id,
    )
    db.session.add(chunk)
    db.session.flush()

    upload_record = UserUpload(
        owner_user_id=current_user.id,
        chunk_id=chunk.id,
        file_name=title,
        file_size_bytes=len(data_text.encode('utf-8')),
        mime_type="text/plain",
        original_format=format_type or None,
        processing_status="queued",
        organization_id=org_id,
    )
    db.session.add(upload_record)
    db.session.commit()

    return jsonify({
        "status": "uploaded",
        "chunk_id": chunk.id,
        "upload_id": upload_record.id,
    })


@bp.route("/api/upload/item", methods=["POST"])
@login_required
def create_upload_item():
    current_user = get_current_user()

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    item_type = data.get("type", "geodonnee").strip()
    format_type = data.get("format_type", "").strip()
    description = data.get("description", "").strip()
    data_format_level = data.get("data_format_level", "individual").strip()
    organization_id = data.get("organization_id", "").strip()

    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    if item_type not in ALLOWED_ITEM_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400

    org_id = int(organization_id) if organization_id and str(organization_id).isdigit() else None
    if org_id:
        membership = OrganizationMember.query.filter_by(
            user_id=current_user.id,
            organization_id=org_id,
            is_active=True,
        ).first()
        if not membership:
            return jsonify({"error": "Organisation non autorisée"}), 403

    item = Item(
        type=item_type,
        title=title,
        description=description or "",
        format_type=format_type or None,
        magnet_link="",
        owner_user_id=current_user.id,
        author_name=f"{current_user.prenom} {current_user.nom}",
           organization_id=org_id,
            verification_status="unofficial",
        data_format_level=data_format_level,
    )
    db.session.add(item)
    db.session.flush()

    viz_link_name = data.get("viz_link_name", "").strip()
    viz_link_url = data.get("viz_link_url", "").strip()
    if viz_link_name and viz_link_url:
        from app import validate_external_url
        if not validate_external_url(viz_link_url):
            return jsonify({"error": "URL invalide ou non sécurisée"}), 400
        link = VisualizationLink(
            parent_item_id=item.id,
            name=viz_link_name[:200],
            url=viz_link_url,
            owner_user_id=current_user.id,
            link_type=data.get("link_type", "external"),
        )
        db.session.add(link)

    if data_format_level == "pack":
        magnet = data.get("magnet_link", "").strip()
        if magnet:
            if not validate_magnet_link(magnet):
                return jsonify({"error": "Lien magnet invalide"}), 400
            item.magnet_link = magnet
    else:
        magnet_links = data.get("magnet_links", [])
        if magnet_links:
            links_json = [
                {
                    "magnet_link": ml.get("magnet_link", ""),
                    "zoom_level": ml.get("zoom_level", ""),
                }
                for ml in magnet_links
                if validate_magnet_link(ml.get("magnet_link", ""))
            ]
            item.metadata_json = links_json

    db.session.commit()

    return jsonify({"status": "created", "id": item.id})
