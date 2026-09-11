import datetime
import io
import logging
import os
import secrets
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, request, render_template, session, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from app import db, limiter
from src.shared import login_required, get_current_user, user_owns_item_or_admin, ITEMS_PER_PAGE, validate_password_strength, _paginate, ALLOWED_ITEM_TYPES, ITEM_TYPE_LABELS, user_belongs_to_org, ITEM_STATUS_DRAFT, ITEM_STATUS_PUBLISHED, ITEM_STATUS_TRASHED
from src.admin import is_catalogue_enabled
from models import User, Rating, Comment, Item, DataChunk, UserUpload, VisualizationLink, ItemGallery, ItemTag, PredefinedTagCategory, Report
from utils.security import sanitize_html, validate_magnet_link, validate_external_url

logger = logging.getLogger(__name__)

_image_processing_executor = ThreadPoolExecutor(max_workers=8)

bp = Blueprint("users", __name__)


@bp.route("/profile/<int:user_id>")
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    comment_count = db.session.query(func.count(Comment.id)).filter(Comment.user_id == user_id).scalar()
    publication_count = Item.query.filter_by(owner_user_id=user_id, status=ITEM_STATUS_PUBLISHED).count()
    return render_template(
        "users/public_profile.html",
        title=f"A.N.A.N.A.S | {user.prenom} {user.nom}",
        meta_description=f"Profil de {user.prenom} {user.nom}",
        profile_user=user,
        comment_count=comment_count,
        publication_count=publication_count,
        current_user=get_current_user(),
    )


@bp.route("/api/users/profile", methods=["PUT"])
@login_required
def update_profile():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    prenom = data.get("prenom", "").strip()
    nom = data.get("nom", "").strip()

    if not prenom or not nom:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    current_user.prenom = prenom
    current_user.nom = nom
    db.session.commit()
    return jsonify({"status": "updated"})


@bp.route("/api/users/change-password", methods=["POST"])
@login_required
@limiter.limit("50 per hour")
def change_password():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({"error": "Mot de passe actuel incorrect"}), 400

    valid, errors = validate_password_strength(new_password)
    if not valid:
        return jsonify({"error": "Mot de passe invalide", "details": errors}), 400

    current_user.password_hash = generate_password_hash(new_password, method="scrypt")
    current_user.session_version += 1
    db.session.commit()
    session.clear()
    return jsonify({"status": "updated"})


@bp.route("/api/users/generate-recovery-codes", methods=["POST"])
@login_required
@limiter.limit("30 per hour")
def generate_recovery_codes():
    current_user = get_current_user()

    codes = []
    for _ in range(10):
        code = secrets.token_hex(16)
        code = "-".join([code[i:i+4] for i in range(0, len(code), 4)])
        codes.append(code)

    hashed_codes = [generate_password_hash(c, method="scrypt") for c in codes]
    current_user.recovery_codes_hash = hashed_codes
    db.session.commit()

    return jsonify({"codes": codes})


@bp.route("/api/users/2fa/setup", methods=["POST"])
@login_required
def setup_2fa():
    import pyotp
    import qrcode

    current_user = get_current_user()

    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    db.session.commit()

    issuer = "A.N.A.N.A.S"
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.pseudo,
        issuer_name=issuer,
    )

    qr = qrcode.make(uri, box_size=6)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = b64encode(buf.getvalue()).decode()

    return jsonify({
        "secret": secret,
        "qr_data_uri": f"data:image/png;base64,{qr_b64}",
        "uri": uri,
    })


@bp.route("/api/users/2fa/enable", methods=["POST"])
@login_required
def enable_2fa():
    import pyotp

    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()

    if not current_user.totp_secret:
        return jsonify({"error": "Aucune clé secrète configurée. Commencez par configurer la 2FA."}), 400

    if not code:
        return jsonify({"error": "Code requis"}), 400

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(code, valid_window=1):
        return jsonify({"error": "Code invalide. Vérifiez l'heure de votre appareil et réessayez."}), 400

    current_user.totp_enabled = True
    db.session.commit()

    return jsonify({"status": "enabled"})


@bp.route("/api/users/2fa/disable", methods=["POST"])
@login_required
def disable_2fa():
    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    password = data.get("password", "").strip()

    if not check_password_hash(current_user.password_hash, password):
        return jsonify({"error": "Mot de passe incorrect"}), 400

    if current_user.totp_enabled and current_user.totp_secret and code:
        import pyotp
        totp = pyotp.TOTP(current_user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return jsonify({"error": "Code 2FA invalide"}), 400

    current_user.totp_secret = None
    current_user.totp_enabled = False
    db.session.commit()

    return jsonify({"status": "disabled"})


@bp.route("/api/users/avatar", methods=["POST"])
@login_required
def upload_avatar():
    current_user = get_current_user()
    if "avatar" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    file = request.files["avatar"]
    if not file.filename:
        return jsonify({"error": "Fichier invalide"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        return jsonify({"error": "Format d'image non supporté (png, jpg, webp)"}), 400

    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 Mo
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_AVATAR_SIZE:
        return jsonify({"error": "Image trop volumineuse (5 Mo maximum)"}), 400

    header = file.read(16)
    file.seek(0)
    is_valid_image = False
    if ext in (".jpg", ".jpeg") and header[:3] in (b"\xff\xd8\xff",):
        is_valid_image = True
    elif ext == ".png" and header[:8] == b"\x89PNG\r\n\x1a\n":
        is_valid_image = True
    elif ext == ".webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        is_valid_image = True
    if not is_valid_image:
        return jsonify({"error": "Le fichier n'est pas une image valide"}), 400

    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(f"avatar_{current_user.id}_{secrets.token_hex(8)}{ext}")
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    current_user.avatar_path = f"/static/uploads/avatars/{filename}"
    db.session.commit()
    return jsonify({"status": "updated", "avatar_path": current_user.avatar_path})


@bp.route("/compte")
@login_required
def compte_page():
    current_user = get_current_user()

    rating_count = db.session.query(func.count(Rating.id)).filter(Rating.user_id == current_user.id).scalar()
    comment_count = db.session.query(func.count(Comment.id)).filter(Comment.user_id == current_user.id).scalar()
    publication_count = Item.query.filter_by(owner_user_id=current_user.id, status=ITEM_STATUS_PUBLISHED).count()
    org_memberships = [m for m in current_user.organizations if m.is_active]
    org_count = len(org_memberships)

    per_page = ITEMS_PER_PAGE
    page = request.args.get("page", 1, type=int)
    pub_page = request.args.get("pub_page", 1, type=int)
    draft_page = request.args.get("draft_page", 1, type=int)
    trash_page = request.args.get("trash_page", 1, type=int)
    active_tab = request.args.get("tab", "infos")
    if active_tab not in ("infos", "securite", "activite", "organisations"):
        active_tab = "infos"

    ratings_query = db.session.query(Rating, Item.title.label("item_title"), Item.type.label("item_type")).join(Item, Rating.item_id == Item.id).filter(Rating.user_id == current_user.id).order_by(Rating.rating.desc())
    ratings, ratings_page, total_ratings, ratings_max_page, ratings_page_numbers = _paginate(ratings_query, page, per_page)

    comments_query = db.session.query(Comment, Item.title.label("item_title"), Item.type.label("item_type")).join(Item, Comment.item_id == Item.id).filter(Comment.user_id == current_user.id).order_by(Comment.created_at.desc())
    comments, comments_page, total_comments, comments_max_page, comments_page_numbers = _paginate(comments_query, page, per_page)

    publications_query = Item.query.filter(Item.owner_user_id == current_user.id, Item.status == ITEM_STATUS_PUBLISHED).order_by(Item.created_at.desc())
    publications, publications_page, total_publications, publications_max_page, publications_page_numbers = _paginate(publications_query, pub_page, per_page)

    drafts_query = Item.query.filter(Item.owner_user_id == current_user.id, Item.status == ITEM_STATUS_DRAFT).order_by(Item.created_at.desc())
    drafts, drafts_page, total_drafts, drafts_max_page, drafts_page_numbers = _paginate(drafts_query, draft_page, per_page)

    trashed_query = Item.query.filter(Item.owner_user_id == current_user.id, Item.status == ITEM_STATUS_TRASHED).order_by(Item.deleted_at.desc())
    trashed, trash_page_num, total_trash, trash_max_page, trash_page_numbers = _paginate(trashed_query, trash_page, per_page)

    data_chunks = db.session.query(DataChunk, Item.title.label("parent_title"), Item.type.label("parent_type")).outerjoin(Item, DataChunk.parent_item_id == Item.id).filter(DataChunk.owner_user_id == current_user.id).order_by(DataChunk.created_at.desc()).limit(10).all()

    return render_template(
        "users/compte.html",
        title="A.N.A.N.A.S | Mon compte",
        meta_description="Gérez votre compte A.N.A.N.A.S",
        user=current_user,
        current_user=current_user,
        rating_count=rating_count,
        comment_count=comment_count,
        publication_count=publication_count,
        active_tab=active_tab,
        ratings=ratings, ratings_page=ratings_page,
        ratings_total_pages=ratings_max_page, ratings_total=total_ratings,
        ratings_page_numbers=ratings_page_numbers,
        comments=comments, comments_page=comments_page,
        comments_total_pages=comments_max_page, comments_total=total_comments,
        comments_page_numbers=comments_page_numbers,
        publications=publications, publications_page=publications_page,
        publications_total_pages=publications_max_page, publications_total=total_publications,
        publications_page_numbers=publications_page_numbers,
        drafts=drafts, drafts_page=drafts_page,
        drafts_total_pages=drafts_max_page, drafts_total=total_drafts,
        drafts_page_numbers=drafts_page_numbers,
        trashed=trashed, trash_page=trash_page_num,
        trash_total_pages=trash_max_page, trash_total=total_trash,
        trash_page_numbers=trash_page_numbers,
        org_memberships=org_memberships,
        org_count=org_count,
        data_chunks=data_chunks,
    )


@bp.route("/upload")
@login_required
def upload_page():
    current_user = get_current_user()

    draft_page = request.args.get("draft_page", 1, type=int)
    trash_page = request.args.get("trash_page", 1, type=int)
    publications_page = request.args.get("publications_page", 1, type=int)

    drafts_query = Item.query.filter_by(
        owner_user_id=current_user.id, status=ITEM_STATUS_DRAFT,
    ).order_by(Item.created_at.desc())

    trashed_query = Item.query.filter_by(
        owner_user_id=current_user.id, status=ITEM_STATUS_TRASHED,
    ).order_by(Item.deleted_at.desc())

    drafts, draft_page, total_drafts, max_draft_page, draft_page_numbers = _paginate(drafts_query, draft_page, ITEMS_PER_PAGE)
    trashed, trash_page, total_trash, max_trash_page, trash_page_numbers = _paginate(trashed_query, trash_page, ITEMS_PER_PAGE)

    publications_query = Item.query.filter_by(
        owner_user_id=current_user.id, status=ITEM_STATUS_PUBLISHED,
    ).order_by(Item.created_at.desc())

    publications, publications_page, total_publications, max_publications_page, publications_page_numbers = _paginate(publications_query, publications_page, ITEMS_PER_PAGE)

    edit_id = request.args.get("edit", "")
    edit_data = None
    if edit_id and edit_id.isdigit():
        draft = Item.query.filter_by(
            id=int(edit_id), owner_user_id=current_user.id,
        ).filter(Item.status.in_([ITEM_STATUS_DRAFT, ITEM_STATUS_PUBLISHED])).first()
        if draft:
            edit_data = draft.to_dict()

    return render_template(
        "users/upload.html",
        title="A.N.A.N.A.S | Publier des données",
        meta_description="Publiez et partagez des géodonnées sur A.N.A.N.A.S",
        current_user=current_user,
        drafts=drafts, trashed=trashed, publications=publications,
        publications_page=publications_page,
        publications_total_pages=max_publications_page,
        publications_total=total_publications,
        publications_page_numbers=publications_page_numbers,
        draft_page=draft_page, draft_total_pages=max_draft_page,
        draft_total=total_drafts, draft_page_numbers=draft_page_numbers,
        trash_page=trash_page, trash_total_pages=max_trash_page,
        trash_total=total_trash, trash_page_numbers=trash_page_numbers,
        edit_data=edit_data,
        is_catalogue_enabled=is_catalogue_enabled,
        predefined_tags=_get_predefined_tags(),
    )


def _get_predefined_tags():
    categories = PredefinedTagCategory.query.order_by(PredefinedTagCategory.display_order).all()
    return {
        "categories": [
            {
                "name": cat.name,
                "tags": [t.name for t in cat.tags]
            }
            for cat in categories
        ]
    }


def _parse_item_data(data):
    title = data.get("title", "").strip()
    item_type = data.get("type", "geodonnee").strip()
    format_type = data.get("format_type", "").strip()
    description = data.get("description", "").strip()
    data_format_level = data.get("data_format_level", "individual").strip()
    organization_id = data.get("organization_id", "").strip()
    license_type = data.get("license_type", "").strip() or None
    custom_license_text = data.get("custom_license_text", "").strip() or None
    if license_type == "other" and custom_license_text:
        license_type = custom_license_text
    elif license_type == "other":
        license_type = None
    pdf_magnet_link = data.get("pdf_magnet_link", "").strip() or None
    status = data.get("status", ITEM_STATUS_PUBLISHED).strip()
    if status not in (ITEM_STATUS_PUBLISHED, ITEM_STATUS_DRAFT):
        status = ITEM_STATUS_PUBLISHED
    return title, item_type, format_type, description, data_format_level, organization_id, license_type, pdf_magnet_link, status


def _process_tags(item, tags):
    existing = {t.tag for t in item.tags}
    new_tags = set()
    for t in (tags or []):
        tag = sanitize_html(t.strip()[:50])
        if tag:
            new_tags.add(tag)
    to_add = new_tags - existing
    to_remove = [t for t in item.tags if t.tag not in new_tags]
    for t in to_remove:
        db.session.delete(t)
    for tag in to_add:
        db.session.add(ItemTag(item_id=item.id, tag=tag))


def _check_org_membership(current_user, organization_id):
    org_id = int(organization_id) if organization_id and str(organization_id).isdigit() else None
    if org_id and not user_belongs_to_org(current_user.id, org_id):
        return None, jsonify({"error": "Organisation non autorisée"}), 403
    return org_id, None, None


def _link_chunk(current_user, chunk_id, item_id):
    if not chunk_id:
        return
    try:
        chunk_id_int = int(chunk_id)
    except (TypeError, ValueError):
        return
    chunk = DataChunk.query.filter_by(id=chunk_id_int, owner_user_id=current_user.id).first()
    if chunk:
        chunk.parent_item_id = item_id
        upload_row = UserUpload.query.filter_by(chunk_id=chunk.id, owner_user_id=current_user.id).first()
        if upload_row:
            upload_row.parent_item_id = item_id


def _create_viz_link(data, item_id):
    viz_link_name = data.get("viz_link_name", "").strip()
    viz_link_url = data.get("viz_link_url", "").strip()
    if viz_link_name and viz_link_url:
        if not validate_external_url(viz_link_url):
            return jsonify({"error": "URL invalide ou non sécurisée"}), 400
        db.session.add(VisualizationLink(
            parent_item_id=item_id, name=viz_link_name[:200], url=viz_link_url,
            owner_user_id=get_current_user().id, link_type=data.get("link_type", "external"),
        ))
    return None


def _process_magnets(item, data_format_level, data):
    if data_format_level in ("simple", "pack"):
        magnet = data.get("magnet_link", "").strip()
        if magnet:
            if not validate_magnet_link(magnet):
                return jsonify({"error": "Lien magnet invalide"}), 400
            item.magnet_link = magnet
            zoom_meta = {}
            if data_format_level == "pack":
                zoom_levels = data.get("zoom_levels", [])
                if zoom_levels:
                    zoom_meta["zoom_levels"] = zoom_levels
            elif data_format_level == "simple":
                zoom_level = data.get("zoom_level", "")
                if zoom_level:
                    zoom_meta["zoom_levels"] = [zoom_level]
            if zoom_meta:
                item.metadata_json = zoom_meta
    else:
        magnet_links = data.get("magnet_links", [])
        if magnet_links:
            item.metadata_json = [
                {"magnet_link": ml.get("magnet_link", ""), "zoom_level": ml.get("zoom_level", "")}
                for ml in magnet_links if validate_magnet_link(ml.get("magnet_link", ""))
            ]
    return None


def _process_image_magnets_async(item_id, image_magnets):
    if not image_magnets:
        return
    _item_id = item_id
    _image_magnets = list(image_magnets)

    def _process_images():
        try:
            from app import create_app
            _app = create_app()
            with _app.app_context():
                from src.image_cache import process_image_magnets
                process_image_magnets(_item_id, _image_magnets)
        except Exception:
            logger.exception("Image processing failed for item %s", _item_id)

    _image_processing_executor.submit(_process_images)


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

    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    if item_type not in ALLOWED_ITEM_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400

    org_id = int(organization_id) if organization_id and organization_id.isdigit() else None
    if org_id and not user_belongs_to_org(current_user.id, org_id):
        return jsonify({"error": "Organisation non autorisée"}), 403

    lines = [line.strip() for line in data_text.splitlines() if line.strip()]
    preview_lines = lines[:50]
    delimiter = "\t" if preview_lines and ("\t" in preview_lines[0] and "," not in preview_lines[0]) else ","
    preview_rows = []
    column_count = 0
    for line in preview_lines:
        cells = [c.strip() for c in line.split(delimiter)]
        preview_rows.append(cells)
        column_count = max(column_count, len(cells))

    chunk = DataChunk(
        parent_item_id=None,
        name=title,
        owner_user_id=current_user.id,
        description=description or None,
        format_type=format_type or None,
        data_url=None,
        metadata_json={
            "preview_rows": preview_rows,
            "column_count": column_count,
            "delimiter": delimiter,
        },
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


def _apply_item_payload(current_user, item, data, is_new=False):
    """Applique un payload item (création ou mise à jour) partagé entre create/update."""
    title, item_type, format_type, description, data_format_level, organization_id, license_type, pdf_magnet_link, status = _parse_item_data(data)
    chunk_id = data.get("chunk_id")

    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    if item_type not in ALLOWED_ITEM_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400

    org_id, error, code = _check_org_membership(current_user, organization_id)
    if error:
        return error, code

    if is_new:
        item.type = item_type
        item.author_name = f"{current_user.prenom} {current_user.nom}"
        item.owner_user_id = current_user.id
        item.magnet_link = ""
        item.verification_status = "unofficial"

    item.title = title
    item.description = description or ""
    item.format_type = format_type or None
    item.organization_id = org_id
    item.data_format_level = data_format_level
    item.license_type = license_type or None
    item.pdf_magnet_link = pdf_magnet_link if validate_magnet_link(pdf_magnet_link) else None
    item.status = status

    _link_chunk(current_user, chunk_id, item.id)
    err = _create_viz_link(data, item.id)
    if err:
        return err
    _process_tags(item, data.get("tags", []))

    err = _process_magnets(item, data_format_level, data)
    if err:
        return err
    image_magnets = data.get("image_magnets", [])
    if image_magnets:
        item.image_magnet_links = image_magnets
        if not is_new:
            ItemGallery.query.filter_by(item_id=item.id, media_type="image").delete()
            item.image_magnets_pending = True
            item.image_magnets_total = len(image_magnets)
        elif status != ITEM_STATUS_DRAFT:
            item.image_magnets_pending = True
            item.image_magnets_total = len(image_magnets)
    elif not is_new:
        item.image_magnets_pending = False
        item.image_magnets_total = 0
    _process_image_magnets_async(item.id, image_magnets)
    return None


@bp.route("/api/upload/item", methods=["POST"])
@login_required
def create_upload_item():
    current_user = get_current_user()

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    item_type = data.get("type", "geodonnee").strip()
    if item_type not in ALLOWED_ITEM_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400

    item = Item(type=item_type, title=title, description=data.get("description", "").strip() or "", magnet_link="")
    db.session.add(item)
    db.session.flush()

    err = _apply_item_payload(current_user, item, data, is_new=True)
    if err:
        db.session.rollback()
        return err

    item.refresh_imod_cache()
    db.session.commit()
    return jsonify({"status": "created", "id": item.id})


@bp.route("/api/upload/item/<int:item_id>", methods=["PUT"])
@login_required
def update_draft_item(item_id):
    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    if not user_owns_item_or_admin(current_user, item):
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
    err = _apply_item_payload(current_user, item, data, is_new=False)
    if err:
        db.session.rollback()
        return err

    item.refresh_imod_cache()
    db.session.commit()
    return jsonify({"status": "updated", "id": item.id})


@bp.route("/brouillons")
@login_required
def brouillons_page():
    current_user = get_current_user()
    drafts = Item.query.filter_by(
        owner_user_id=current_user.id,
        status=ITEM_STATUS_DRAFT,
    ).order_by(Item.created_at.desc()).all()
    return render_template(
        "users/brouillons.html",
        title="A.N.A.N.A.S | Mes brouillons",
        drafts=drafts,
        current_user=current_user,
    )


@bp.route("/api/upload/drafts/all", methods=["DELETE"])
@login_required
def delete_all_drafts():
    current_user = get_current_user()
    now = datetime.datetime.now()
    try:
        Item.query.filter_by(
            owner_user_id=current_user.id,
            status=ITEM_STATUS_DRAFT,
        ).update({"status": ITEM_STATUS_TRASHED, "deleted_at": now})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to bulk-delete drafts")
        return jsonify({"error": "Erreur lors de la suppression"}), 500
    return jsonify({"status": "trashed"})


@bp.route("/api/upload/item/<int:item_id>", methods=["DELETE"])
@login_required
def delete_draft_item(item_id):
    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    if not user_owns_item_or_admin(current_user, item):
        return jsonify({"error": "Non autorisé"}), 403

    if item.status not in (ITEM_STATUS_DRAFT, ITEM_STATUS_PUBLISHED):
        return jsonify({"error": "Seuls les brouillons et publications peuvent être supprimés"}), 400

    item.status = ITEM_STATUS_TRASHED
    item.deleted_at = datetime.datetime.now()
    db.session.commit()
    return jsonify({"status": "trashed"})


@bp.route("/api/upload/item/<int:item_id>/restore", methods=["POST"])
@login_required
def restore_draft_item(item_id):
    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    if not user_owns_item_or_admin(current_user, item):
        return jsonify({"error": "Non autorisé"}), 403

    if item.status != ITEM_STATUS_TRASHED:
        return jsonify({"error": "Seuls les éléments dans la corbeille peuvent être restaurés"}), 400

    item.status = ITEM_STATUS_DRAFT
    item.deleted_at = None
    db.session.commit()
    return jsonify({"status": "restored"})


@bp.route("/api/upload/trash/all", methods=["DELETE"])
@login_required
def purge_all_trash():
    current_user = get_current_user()
    trashed_items = Item.query.filter_by(
        owner_user_id=current_user.id,
        status=ITEM_STATUS_TRASHED,
    ).all()

    if not trashed_items:
        return jsonify({"error": "Aucun élément dans la corbeille"}), 400

    try:
        ids = [item.id for item in trashed_items]
        UserUpload.query.filter(UserUpload.parent_item_id.in_(ids)).update({"chunk_id": None, "published_item_id": None})
        DataChunk.query.filter(DataChunk.parent_item_id.in_(ids)).delete()
        UserUpload.query.filter(UserUpload.parent_item_id.in_(ids)).delete()
        Report.query.filter(Report.target_item_id.in_(ids)).delete()
        VisualizationLink.query.filter(VisualizationLink.parent_item_id.in_(ids)).delete()
        Rating.query.filter(Rating.item_id.in_(ids)).delete()
        Comment.query.filter(Comment.item_id.in_(ids)).delete()
        ItemTag.query.filter(ItemTag.item_id.in_(ids)).delete()
        ItemGallery.query.filter(ItemGallery.item_id.in_(ids)).delete()

        for item in trashed_items:
            db.session.delete(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to bulk-purge trash")
        return jsonify({"error": "Erreur lors de la suppression"}), 500
    return jsonify({"status": "deleted", "count": len(trashed_items)})


@bp.route("/api/upload/item/<int:item_id>/purge", methods=["DELETE"])
@login_required
def purge_draft_item(item_id):
    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)

    if not user_owns_item_or_admin(current_user, item):
        return jsonify({"error": "Non autorisé"}), 403

    if item.status != ITEM_STATUS_TRASHED:
        return jsonify({"error": "Non autorisé"}), 403

    try:
        UserUpload.query.filter_by(parent_item_id=item.id).update({"chunk_id": None, "published_item_id": None})
        DataChunk.query.filter_by(parent_item_id=item.id).delete()
        UserUpload.query.filter_by(parent_item_id=item.id).delete()
        Report.query.filter_by(target_item_id=item.id).delete()
        VisualizationLink.query.filter_by(parent_item_id=item.id).delete()
        Rating.query.filter_by(item_id=item.id).delete()
        Comment.query.filter_by(item_id=item.id).delete()
        ItemTag.query.filter_by(item_id=item.id).delete()
        ItemGallery.query.filter_by(item_id=item.id).delete()

        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Failed to purge item %s", item_id)
        return jsonify({"error": "Erreur lors de la suppression"}), 500
    return jsonify({"status": "deleted"})


@bp.route("/api/upload/drafts")
@login_required
def list_drafts():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)

    query = Item.query.filter_by(
        owner_user_id=current_user.id,
        status=ITEM_STATUS_DRAFT,
    ).order_by(Item.created_at.desc())

    items, page, total, total_pages, page_numbers = _paginate(query, page, ITEMS_PER_PAGE)

    return jsonify({
        "drafts": [
            {
                "id": d.id,
                "title": d.title,
                "created_at": d.created_at.strftime("%d/%m/%Y %H:%M") if d.created_at else "",
                "status": d.status,
            }
            for d in items
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total,
        "page_numbers": page_numbers,
    })


@bp.route("/api/upload/trash")
@login_required
def list_trash():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)

    query = Item.query.filter_by(
        owner_user_id=current_user.id,
        status=ITEM_STATUS_TRASHED,
    ).order_by(Item.deleted_at.desc())

    items, page, total, total_pages, page_numbers = _paginate(query, page, ITEMS_PER_PAGE)

    return jsonify({
        "trashed": [
            {
                "id": t.id,
                "title": t.title,
                "deleted_at": t.deleted_at.strftime("%d/%m/%Y %H:%M") if t.deleted_at else "",
                "status": t.status,
            }
            for t in items
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total,
        "page_numbers": page_numbers,
    })


@bp.route("/api/upload/publications")
@login_required
def list_publications():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)

    query = Item.query.filter_by(
        owner_user_id=current_user.id,
        status=ITEM_STATUS_PUBLISHED,
    ).order_by(Item.created_at.desc())

    items, page, total, total_pages, page_numbers = _paginate(query, page, ITEMS_PER_PAGE)

    return jsonify({
        "publications": [
            {
                "id": p.id,
                "title": p.title,
                "type": p.type,
                "type_label": ITEM_TYPE_LABELS.get(p.type, p.type),
                "created_at": p.created_at.strftime("%d/%m/%Y") if p.created_at else "",
            }
            for p in items
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total,
        "page_numbers": page_numbers,
    })
