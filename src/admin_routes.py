import datetime as dt
import json
import os

from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from app import db
from src.shared import login_required, get_current_user, _build_page_numbers, ITEMS_PER_PAGE
from utils.security import sanitize_html

CATALOGUES_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "catalogues_config.json")

_CATALOGUES_INFO = [
    {"type": "donnees", "label": "Géodonnées"},
    {"type": "cartes", "label": "Cartes"},
    {"type": "applications", "label": "Applications"},
]


def get_catalogues_status():
    try:
        with open(CATALOGUES_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"donnees": True, "cartes": True, "applications": True}


def _save_catalogues_status(data):
    os.makedirs(os.path.dirname(CATALOGUES_CONFIG_PATH), exist_ok=True)
    with open(CATALOGUES_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def is_catalogue_enabled(catalogue_type):
    status = get_catalogues_status()
    return status.get(catalogue_type, True)


bp = Blueprint("admin", __name__)


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for("auth.connexion_page"))
        if not current_user.is_admin:
            return render_template(
                "error.html",
                title="Accès refusé — A.N.A.N.A.S.",
                meta_description="Vous n'avez pas accès à cette page.",
                message="Accès non autorisé. Vous devez être administrateur.",
                code=403,
            ), 403
        return f(*args, **kwargs)
    return decorated


def api_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return jsonify({"error": "Non autorisé"}), 403
        return f(*args, **kwargs)
    return decorated


def _log_audit(action_type, target_type=None, target_id=None, details=None):
    from models import AdminAudit
    current_user = get_current_user()
    audit = AdminAudit(
        admin_user_id=current_user.id if current_user else None,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    db.session.add(audit)
    db.session.commit()


def _paginate(query, page=1, per_page=30):
    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    page_numbers = _build_page_numbers(page, total_pages)
    return items, page, total_pages, total_items, page_numbers


def _get_json_data():
    return request.get_json(silent=True) or {}


def _serialize_user(u):
    return {
        "id": u.id, "prenom": u.prenom, "nom": u.nom, "email": u.email,
        "created_at": u.created_at.isoformat() if hasattr(u, "created_at") else None,
        "banned": u.banned,
    }


def _serialize_report(r):
    return {
        "id": r.id,
        "reporter": {"id": r.reporter.id, "name": str(r.reporter)} if r.reporter else None,
        "reported_user": {"id": r.reported_user.id, "name": str(r.reported_user)} if r.reported_user else None,
        "target_item_id": r.target_item_id,
        "report_type": r.report_type, "reason": r.reason, "description": r.description,
        "status": r.status,
        "reviewed_by": {"id": r.reviewer.id, "name": str(r.reviewer)} if r.reviewer else None,
        "reviewed_at": r.reviewed_at.isoformat() if hasattr(r, "reviewed_at") and r.reviewed_at else None,
        "created_at": r.created_at.isoformat(),
    }


def _serialize_comment(c):
    return {
        "id": c.id, "item_id": c.item_id, "author_name": c.author_name,
        "content": c.content,
        "created_at": c.created_at.isoformat() if hasattr(c, "created_at") and c.created_at else None,
        "item_title": c.item.title if c.item else None,
        "item_type": c.item.type if c.item else None,
    }


def _serialize_item(it):
    return {
        "id": it.id, "type": it.type, "title": it.title,
        "description": it.description[:100], "author_name": it.author_name,
        "verification_status": it.verification_status,
        "created_at": it.created_at.isoformat() if hasattr(it, "created_at") and it.created_at else None,
        "comment_count": len(it.comments),
    }


def _serialize_mirror(m):
    return {
        "id": m.id, "name": m.name, "url": m.url, "description": m.description,
        "display_order": m.display_order, "is_active": m.is_active,
        "created_at": m.created_at.isoformat() if hasattr(m, "created_at") and m.created_at else None,
    }


def _serialize_featured(f):
    return {
        "id": f.id, "item_id": f.item_id,
        "item_title": f.item.title if f.item else None,
        "item_type": f.item.type if f.item else None,
        "item_format": f.item.format_type if f.item else None,
        "item_description": f.item.description[:100] if f.item else None,
        "display_order": f.display_order, "is_active": f.is_active,
    }


def _serialize_contact_message(m):
    return {
        "id": m.id, "name": m.name, "email": m.email, "subject": m.subject,
        "message": m.message, "is_read": m.is_read,
        "created_at": m.created_at.isoformat() if hasattr(m, "created_at") and m.created_at else None,
    }


def _serialize_geopackage(p):
    return {
        "id": p.id, "title": p.title, "description": p.description,
        "format_info": p.format_info, "link_url": p.link_url,
        "display_order": p.display_order, "is_active": p.is_active,
    }


# --- User management ---

@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
@api_admin_required
def ban_user(user_id):
    from models import User

    target_user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    if target_user.id == current_user.id:
        return jsonify({"error": "Action interdite"}), 403

    data = request.get_json(silent=True) or {} if request.is_json and request.content_type == "application/json" else request.form
    action = data.get("action", "")
    duration = data.get("duration")

    actions = {
        "ban": lambda: _do_ban(target_user),
        "unban": lambda: _do_unban(target_user),
        "tempban": lambda: _do_tempban(target_user, duration),
        "mute": lambda: _do_mute(target_user, duration),
        "unmute": lambda: _do_unmute(target_user),
        "warn": lambda: _do_warn(target_user, data),
        "unwarn": lambda: _do_unwarn(target_user),
        "kick": lambda: _do_kick(target_user),
    }

    handler = actions.get(action)
    if not handler:
        return jsonify({"error": "Action invalide"}), 400
    return handler()


def _do_ban(user):
    user.banned = True
    user.is_active = False
    db.session.commit()
    _log_audit("ban", "user", user.id, {"email": user.email, "duration": "permanent"})
    return jsonify({"status": "updated", "user_id": user.id, "action": "ban"})


def _do_unban(user):
    user.banned = False
    user.is_active = True
    db.session.commit()
    _log_audit("unban", "user", user.id, {"email": user.email})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unban"})


def _do_tempban(user, duration):
    try:
        hours = int(duration)
    except (TypeError, ValueError):
        return jsonify({"error": "Durée invalide"}), 400
    ban_until = dt.datetime.now() + dt.timedelta(hours=hours)
    user.banned = True
    user.is_active = False
    db.session.commit()
    _log_audit("tempban", "user", user.id, {"email": user.email, "duration_hours": hours, "ban_until": ban_until.isoformat()})
    return jsonify({"status": "updated", "user_id": user.id, "action": "tempban", "ban_until": ban_until.isoformat()})


def _do_mute(user, duration):
    try:
        hours = int(duration)
    except (TypeError, ValueError):
        return jsonify({"error": "Durée invalide"}), 400
    user.muted_until = dt.datetime.now() + dt.timedelta(hours=hours)
    db.session.commit()
    _log_audit("mute", "user", user.id, {"email": user.email, "duration_hours": hours, "muted_until": user.muted_until.isoformat()})
    return jsonify({"status": "updated", "user_id": user.id, "action": "mute", "muted_until": user.muted_until.isoformat()})


def _do_unmute(user):
    user.muted_until = None
    db.session.commit()
    _log_audit("unmute", "user", user.id, {"email": user.email})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unmute"})


def _do_warn(user, data):
    reason = data.get("reason", "")
    user.warned = True
    user.warnings = (user.warnings or "") + f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}] {reason}\n"
    db.session.commit()
    _log_audit("warn", "user", user.id, {"email": user.email, "reason": reason})
    return jsonify({"status": "updated", "user_id": user.id, "action": "warn"})


def _do_unwarn(user):
    user.warned = False
    user.warnings = None
    db.session.commit()
    _log_audit("unwarn", "user", user.id, {"email": user.email})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unwarn"})


def _do_kick(user):
    db.session.commit()
    _log_audit("kick", "user", user.id, {"email": user.email})
    return jsonify({"status": "updated", "user_id": user.id, "action": "kick"})


@bp.route("/api/users/banned", methods=["GET"])
@login_required
@api_admin_required
def list_banned_users():
    from models import User
    banned = User.query.filter_by(banned=True).all()
    return jsonify([_serialize_user(u) for u in banned])


# --- Reports ---

@bp.route("/api/reports", methods=["POST"])
@login_required
def create_report():
    from models import User, Item, Report

    current_user = get_current_user()
    data = _get_json_data()

    target_type = data.get("target_type")
    target_id = data.get("target_id")
    reason = data.get("reason")
    description = sanitize_html(data.get("description", ""))

    if not target_type or not target_id or not reason:
        return jsonify({"error": "target_type, target_id et reason sont requis"}), 400
    if reason not in ("spam", "fake_data", "other"):
        return jsonify({"error": "Raison invalide"}), 400

    report = Report(
        reporter_id=current_user.id,
        report_type=f"item_{target_type}" if target_type != "user" else "user",
        reason=reason, description=description, status="pending",
    )

    if target_type == "user":
        reported_user = db.session.get(User, target_id)
        if not reported_user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        if reported_user.id == current_user.id:
            return jsonify({"error": "Impossible de se signaler soi-même"}), 400
        report.reported_user_id = reported_user.id
    else:
        if target_type not in {"geodonnee", "carte", "application"}:
            return jsonify({"error": "Type de contenu invalide"}), 400
        item = Item.query.filter_by(id=target_id, type=target_type).first()
        if not item:
            return jsonify({"error": "Contenu introuvable"}), 404
        if item.author_name == f"{current_user.prenom} {current_user.nom}":
            return jsonify({"error": "Impossible de signaler son propre contenu"}), 400
        report.target_item_id = target_id

    db.session.add(report)
    db.session.commit()
    return jsonify({"status": "created", "report_id": report.id})


@bp.route("/api/admin/reports", methods=["GET"])
@login_required
@api_admin_required
def list_reports():
    from models import Report

    status_filter = request.args.get("status", "all")
    report_type = request.args.get("type", "all")
    page = int(request.args.get("page", 1))

    query = Report.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if report_type != "all":
        query = query.filter_by(report_type=report_type)

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(Report.created_at.desc()), page
    )
    return jsonify({
        "reports": [_serialize_report(r) for r in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/reports/<int:report_id>/resolve", methods=["POST"])
@login_required
@api_admin_required
def resolve_report(report_id):
    from models import Report

    report = Report.query.get_or_404(report_id)
    data = _get_json_data()
    new_status = data.get("status", "")

    if new_status not in ("resolved", "dismissed"):
        return jsonify({"error": "Statut invalide"}), 400

    current_user = get_current_user()
    report.status = new_status
    report.reviewed_by = current_user.id
    report.reviewed_at = dt.datetime.now()
    db.session.commit()
    _log_audit(new_status, "report", report_id, {"reason": report.reason, "description": report.description})
    return jsonify({"status": "updated", "report_id": report.id})


# --- Admin pages ---

@bp.route("/admin/users")
@bp.route("/admin/users/<int:page>")
@login_required
@require_admin
def admin_users(page=None):
    from models import User
    p = request.args.get("page", 1, type=int) if page is None else page
    p = min(max(p, 1), 9999)
    query = User.query.order_by(User.id)
    paginated, p, total_pages, total_items, page_numbers = _paginate(query, p, ITEMS_PER_PAGE)
    return render_template(
        "admin/users.html",
        title="Administration — Utilisateurs", meta_description="Liste des utilisateurs",
        users=paginated, page=p, total_pages=total_pages,
        page_numbers=page_numbers, total_items=total_items, now=dt.datetime.now(),
    )


@bp.route("/admin/reports")
@login_required
@require_admin
def admin_reports():
    return render_template("admin/reports.html", title="Administration — Signalements", meta_description="Liste des signalements")


@bp.route("/admin/moderation")
@login_required
@require_admin
def admin_moderation():
    return render_template("admin/moderation.html", title="Administration — Modération", meta_description="Modération des contenus et commentaires")


@bp.route("/admin/audit")
@login_required
@require_admin
def admin_audit():
    return render_template("admin/audit.html", title="Administration — Journal d'audits", meta_description="Journal des actions administratives")


@bp.route("/admin/contact-messages")
@login_required
@require_admin
def admin_contact_messages():
    return render_template("admin/contact_messages.html", title="Administration — Messages de contact", meta_description="Messages reçus via la page contact")


@bp.route("/admin/mirrors")
@login_required
@require_admin
def admin_mirrors():
    return render_template("admin/mirrors.html", title="Administration — Sites miroirs", meta_description="Gestion des sites miroirs")


@bp.route("/admin/featured")
@login_required
@require_admin
def admin_featured():
    return render_template("admin/featured.html", title="Administration — Données en avant", meta_description="Gestion des données mises en avant")


@bp.route("/admin/geopackages")
@login_required
@require_admin
def admin_geopackages():
    return render_template("admin/geopackages.html", title="Administration — GeoPackages", meta_description="Gestion des packs GeoPackage")


@bp.route("/admin/catalogues")
@login_required
@require_admin
def admin_catalogues():
    status = get_catalogues_status()
    catalogues = [{"type": info["type"], "label": info["label"], "active": status.get(info["type"], True)} for info in _CATALOGUES_INFO]
    return render_template("admin/catalogues.html", title="Administration — Catalogues", meta_description="Activer ou désactiver les catalogues", catalogues=catalogues)


@bp.route("/admin/replication")
@login_required
@require_admin
def admin_replication():
    return render_template("admin/replication.html", title="Administration — Réplication", meta_description="Répliquer des catalogues depuis une instance distante")


@bp.route("/admin/accueil")
@login_required
@require_admin
def admin_home():
    return render_template("admin/home.html", title="Administration — Accueil", meta_description="Gestion de la page d'accueil")


# --- Comments ---

@bp.route("/api/admin/comments", methods=["GET"])
@login_required
@api_admin_required
def list_comments():
    from models import Comment

    item_id = request.args.get("item_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", ITEMS_PER_PAGE, type=int)

    query = Comment.query
    if item_id:
        query = query.filter_by(item_id=item_id)

    since_param = request.args.get("since")
    if since_param:
        try:
            query = query.filter(Comment.created_at >= dt.datetime.fromisoformat(since_param))
        except (ValueError, TypeError):
            pass

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(Comment.created_at.desc()), page, per_page
    )
    return jsonify({
        "comments": [_serialize_comment(c) for c in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/comments/<int:comment_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_comment(comment_id):
    from models import Comment

    comment = Comment.query.get_or_404(comment_id)
    item_title = comment.item.title if comment.item else None
    db.session.delete(comment)
    db.session.commit()
    _log_audit("comment_deleted", "comment", comment_id, {"item_title": item_title, "content_preview": (comment.content[:80] if comment.content else "")})
    return jsonify({"status": "deleted", "comment_id": comment_id})


# --- Items ---

@bp.route("/api/admin/items", methods=["GET"])
@login_required
@api_admin_required
def list_items():
    from models import Item

    item_type = request.args.get("type", "all")
    page = int(request.args.get("page", 1))

    query = Item.query
    if item_type != "all":
        query = query.filter_by(type=item_type)

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(Item.created_at.desc()), page
    )
    return jsonify({
        "items": [_serialize_item(it) for it in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/items/<int:item_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_item(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    title = item.title
    type_name = item.type
    db.session.delete(item)
    db.session.commit()
    _log_audit("item_deleted", "item", item_id, {"title": title, "type": type_name})
    return jsonify({"status": "deleted", "item_id": item_id, "title": title})


@bp.route("/api/admin/items/<int:item_id>/verify", methods=["POST"])
@login_required
@api_admin_required
def verify_item(item_id):
    from models import Item

    current_user = get_current_user()
    item = Item.query.get_or_404(item_id)
    item.verification_status = 'verified'
    item.verifier_user_id = current_user.id
    item.verified_at = db.func.now()
    db.session.commit()
    _log_audit("item_verified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "verified"})


@bp.route("/api/admin/items/<int:item_id>/unverify", methods=["POST"])
@login_required
@api_admin_required
def unverify_item(item_id):
    from models import Item

    item = Item.query.get_or_404(item_id)
    item.verification_status = 'unofficial'
    item.verifier_user_id = None
    item.verified_at = None
    db.session.commit()
    _log_audit("item_unverified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "unofficial"})


# --- Audit ---

@bp.route("/api/admin/audit")
@login_required
@api_admin_required
def admin_audit_log():
    from models import AdminAudit

    page = request.args.get("page", 1, type=int)
    paginated, page, total_pages, total_items, _ = _paginate(
        AdminAudit.query.order_by(AdminAudit.created_at.desc()), page, 50
    )
    entries = _get_audit_entries(paginated)
    return jsonify({"entries": entries, "page": page, "total_pages": total_pages, "total_items": total_items})


def _get_audit_entries(entries=None):
    from models import AdminAudit, User
    if entries is None:
        entries = AdminAudit.query.order_by(AdminAudit.created_at.desc()).limit(500).all()
    result = []
    for e in entries:
        result.append({
            "id": e.id,
            "admin": {"id": e.admin_user_id, "name": str(e.admin)} if e.admin else None,
            "action_type": e.action_type, "target_type": e.target_type,
            "target_id": e.target_id, "details": e.details or {},
            "created_at": e.created_at.isoformat() if hasattr(e, "created_at") and e.created_at else None,
        })
    return result


# --- Contact Messages ---

@bp.route("/api/admin/contact-messages", methods=["GET"])
@login_required
@api_admin_required
def list_contact_messages():
    from models import ContactMessage

    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "all")

    query = ContactMessage.query
    if status_filter == "unread":
        query = query.filter_by(is_read=False)
    elif status_filter == "read":
        query = query.filter_by(is_read=True)

    paginated, page, total_pages, total_items, page_numbers = _paginate(
        query.order_by(ContactMessage.created_at.desc()), page
    )
    return jsonify({
        "messages": [_serialize_contact_message(m) for m in paginated],
        "page": page, "total_pages": total_pages,
        "total_items": total_items, "page_numbers": page_numbers,
    })


@bp.route("/api/admin/contact-messages/<int:msg_id>/read", methods=["POST"])
@login_required
@api_admin_required
def mark_contact_message_read(msg_id):
    from models import ContactMessage

    msg = ContactMessage.query.get_or_404(msg_id)
    data = _get_json_data()
    msg.is_read = bool(data.get("is_read", True))
    db.session.commit()
    return jsonify({"status": "updated", "id": msg.id, "is_read": msg.is_read})


@bp.route("/api/admin/contact-messages/<int:msg_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_contact_message(msg_id):
    from models import ContactMessage

    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    _log_audit("contact_message_deleted", "contact_message", msg_id, {"name": msg.name, "subject": msg.subject})
    return jsonify({"status": "deleted", "id": msg_id})


# --- Mirrors CRUD ---

@bp.route("/api/admin/mirrors", methods=["GET"])
@login_required
@api_admin_required
def list_mirrors():
    from models import MirrorSite

    mirrors = MirrorSite.query.order_by(MirrorSite.display_order, MirrorSite.id).all()
    return jsonify({"mirrors": [_serialize_mirror(m) for m in mirrors]})


@bp.route("/api/admin/mirrors", methods=["POST"])
@login_required
@api_admin_required
def create_mirror():
    from models import MirrorSite

    data = _get_json_data()
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    description = (data.get("description") or "").strip()

    if not name or not url or not description:
        return jsonify({"error": "Tous les champs sont requis."}), 400
    if len(name) > 200 or len(url) > 500 or len(description) > 500:
        return jsonify({"error": "Champs trop longs."}), 400

    max_order = db.session.query(db.func.max(MirrorSite.display_order)).scalar() or 0
    mirror = MirrorSite(
        name=sanitize_html(name), url=sanitize_html(url),
        description=sanitize_html(description),
        display_order=max_order + 1, is_active=True,
    )
    db.session.add(mirror)
    db.session.commit()
    _log_audit("mirror_created", "mirror", mirror.id, {"name": mirror.name, "url": mirror.url})
    return jsonify({"status": "created", "mirror": _serialize_mirror(mirror)})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_mirror(mirror_id):
    from models import MirrorSite

    mirror = MirrorSite.query.get_or_404(mirror_id)
    data = _get_json_data()

    if "name" in data:
        mirror.name = sanitize_html(data["name"].strip())
    if "url" in data:
        mirror.url = sanitize_html(data["url"].strip())
    if "description" in data:
        mirror.description = sanitize_html(data["description"].strip())
    if "display_order" in data:
        mirror.display_order = int(data["display_order"])
    if "is_active" in data:
        mirror.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("mirror_updated", "mirror", mirror_id, {"name": mirror.name})
    return jsonify({"status": "updated", "mirror": _serialize_mirror(mirror)})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_mirror(mirror_id):
    from models import MirrorSite

    mirror = MirrorSite.query.get_or_404(mirror_id)
    db.session.delete(mirror)
    db.session.commit()
    _log_audit("mirror_deleted", "mirror", mirror_id, {"name": mirror.name})
    return jsonify({"status": "deleted", "id": mirror_id})


# --- Featured Items CRUD ---

@bp.route("/api/admin/featured", methods=["GET"])
@login_required
@api_admin_required
def list_featured():
    from models import FeaturedItem

    featured = FeaturedItem.query.order_by(FeaturedItem.display_order, FeaturedItem.id).all()
    return jsonify({"featured": [_serialize_featured(f) for f in featured]})


@bp.route("/api/admin/items/search", methods=["GET"])
@login_required
@api_admin_required
def search_items():
    from models import Item

    q = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 20))

    query = Item.query.filter(Item.status == "published")
    if q:
        query = query.filter(Item.title.ilike(f"%{q}%"))

    items = query.order_by(Item.title).limit(limit).all()
    return jsonify({
        "items": [
            {"id": it.id, "title": it.title, "type": it.type,
             "format_type": it.format_type, "description": it.description[:100] if it.description else ""}
            for it in items
        ],
    })


@bp.route("/api/admin/featured", methods=["POST"])
@login_required
@api_admin_required
def create_featured():
    from models import FeaturedItem, Item

    data = _get_json_data()
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id requis."}), 400
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item introuvable."}), 404
    if FeaturedItem.query.filter_by(item_id=item_id).first():
        return jsonify({"error": "Cet item est déjà mis en avant."}), 409

    max_order = db.session.query(db.func.max(FeaturedItem.display_order)).scalar() or 0
    featured = FeaturedItem(item_id=item_id, display_order=max_order + 1, is_active=True)
    db.session.add(featured)
    db.session.commit()
    _log_audit("featured_created", "featured", featured.id, {"item_id": item_id, "title": item.title})

    return jsonify({"status": "created", "featured": _serialize_featured(featured)})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_featured(featured_id):
    from models import FeaturedItem

    featured = FeaturedItem.query.get_or_404(featured_id)
    data = _get_json_data()

    if "display_order" in data:
        featured.display_order = int(data["display_order"])
    if "is_active" in data:
        featured.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("featured_updated", "featured", featured_id, {"item_id": featured.item_id})
    return jsonify({"status": "updated", "featured": _serialize_featured(featured)})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_featured(featured_id):
    from models import FeaturedItem

    featured = FeaturedItem.query.get_or_404(featured_id)
    db.session.delete(featured)
    db.session.commit()
    _log_audit("featured_deleted", "featured", featured_id, {"title": featured.item.title if featured.item else None})
    return jsonify({"status": "deleted", "id": featured_id})


# --- GeoPackages CRUD ---

@bp.route("/api/admin/geopackages", methods=["GET"])
@login_required
@api_admin_required
def list_geopackages():
    from models import GeoPackage

    packages = GeoPackage.query.order_by(GeoPackage.display_order, GeoPackage.id).all()
    return jsonify({"packages": [_serialize_geopackage(p) for p in packages]})


@bp.route("/api/admin/geopackages", methods=["POST"])
@login_required
@api_admin_required
def create_geopackage():
    from models import GeoPackage

    data = _get_json_data()
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    format_info = (data.get("format_info") or "").strip()
    link_url = (data.get("link_url") or "").strip()

    if not title or not description or not format_info or not link_url:
        return jsonify({"error": "Tous les champs sont requis."}), 400
    if len(title) > 200 or len(description) > 500 or len(format_info) > 200 or len(link_url) > 500:
        return jsonify({"error": "Champs trop longs."}), 400

    max_order = db.session.query(db.func.max(GeoPackage.display_order)).scalar() or 0
    pkg = GeoPackage(
        title=sanitize_html(title), description=sanitize_html(description),
        format_info=sanitize_html(format_info), link_url=sanitize_html(link_url),
        display_order=max_order + 1, is_active=True,
    )
    db.session.add(pkg)
    db.session.commit()
    _log_audit("geopackage_created", "geopackage", pkg.id, {"title": pkg.title})
    return jsonify({"status": "created", "package": _serialize_geopackage(pkg)})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_geopackage(pkg_id):
    from models import GeoPackage

    pkg = GeoPackage.query.get_or_404(pkg_id)
    data = _get_json_data()

    if "title" in data:
        pkg.title = sanitize_html(data["title"].strip())
    if "description" in data:
        pkg.description = sanitize_html(data["description"].strip())
    if "format_info" in data:
        pkg.format_info = sanitize_html(data["format_info"].strip())
    if "link_url" in data:
        pkg.link_url = sanitize_html(data["link_url"].strip())
    if "display_order" in data:
        pkg.display_order = int(data["display_order"])
    if "is_active" in data:
        pkg.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("geopackage_updated", "geopackage", pkg_id, {"title": pkg.title})
    return jsonify({"status": "updated", "package": _serialize_geopackage(pkg)})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_geopackage(pkg_id):
    from models import GeoPackage

    pkg = GeoPackage.query.get_or_404(pkg_id)
    db.session.delete(pkg)
    db.session.commit()
    _log_audit("geopackage_deleted", "geopackage", pkg_id, {"title": pkg.title})
    return jsonify({"status": "deleted", "id": pkg_id})


# --- Catalogues toggle ---

@bp.route("/api/admin/catalogues/<catalogue_type>/toggle", methods=["POST"])
@login_required
@api_admin_required
def toggle_catalogue(catalogue_type):
    valid_types = [info["type"] for info in _CATALOGUES_INFO]
    if catalogue_type not in valid_types:
        return jsonify({"error": "Type de catalogue invalide"}), 400

    data = _get_json_data()
    active = data.get("active", True)

    status = get_catalogues_status()
    status[catalogue_type] = bool(active)
    _save_catalogues_status(status)

    _log_audit(
        "catalogue_toggle" if not active else "catalogue_enable",
        "catalogue", target_type=catalogue_type,
        details={"catalogue": catalogue_type, "active": bool(active)},
    )
    return jsonify({"status": "updated", "catalogue": catalogue_type, "active": bool(active)})


# --- Replication ---

@bp.route("/api/admin/replication/fetch", methods=["POST"])
@login_required
@api_admin_required
def replication_fetch():
    from models import Item, ItemTag, ItemGallery, DataChunk, VisualizationLink

    data = _get_json_data()
    remote_url = (data.get("url") or "").strip().rstrip("/")
    selected_types = data.get("types", [])

    if not remote_url:
        return jsonify({"error": "URL requise."}), 400
    if not selected_types:
        return jsonify({"error": "Sélectionnez au moins un type de catalogue."}), 400

    type_map_r = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}
    valid_types = [t for t in selected_types if t in type_map_r]
    if not valid_types:
        return jsonify({"error": "Types de catalogue invalides."}), 400

    import urllib.request
    import urllib.error
    import ssl

    ctx = ssl.create_default_context()
    current_user = get_current_user()
    created = []
    skipped = []
    errors = []

    def _fetch_json(url):
        req = urllib.request.Request(url, headers={"User-Agent": "ANANAS-Replicator/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))

    for cat_type in valid_types:
        item_type = type_map_r[cat_type]
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
                    verification_status="unofficial", status="published",
                )
                db.session.add(new_item)
                db.session.flush()

                for tag_name in item_data.get("tags", []):
                    db.session.add(ItemTag(item_id=new_item.id, tag=sanitize_html(tag_name)))

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
    remote_url = (data.get("url") or "").strip().rstrip("/")

    if not remote_url:
        return jsonify({"error": "URL requise."}), 400

    import urllib.request
    import urllib.error
    import ssl

    ctx = ssl.create_default_context()
    type_map_r = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}
    result = []

    for cat_type, item_type in type_map_r.items():
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