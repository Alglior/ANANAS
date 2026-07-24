import datetime as dt

from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from app import db
from src.shared import login_required, get_current_user, _build_page_numbers, ITEMS_PER_PAGE
from utils.security import sanitize_html

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


def _get_audit_entries(entries=None):
    from models import AdminAudit, User

    if entries is None:
        entries = (
            AdminAudit.query
            .order_by(AdminAudit.created_at.desc())
            .limit(500)
            .all()
        )
    result = []
    for e in entries:
        result.append({
            "id": e.id,
            "admin": {"id": e.admin_user_id, "name": str(e.admin)} if e.admin else None,
            "action_type": e.action_type,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "details": e.details or {},
            "created_at": e.created_at.isoformat() if hasattr(e, "created_at") and e.created_at else None,
        })
    return result


@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
def ban_user(user_id):
    from models import User

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    target_user = User.query.get_or_404(user_id)
    if target_user.id == current_user.id:
        return jsonify({"error": "Action interdite"}), 403

    if request.is_json and request.content_type == "application/json":
        data = request.get_json(silent=True) or {}
    else:
        data = request.form
    action = data.get("action", "")

    if action not in ("ban", "unban"):
        return jsonify({"error": "Action invalide"}), 400

    target_user.banned = (action == "ban")
    db.session.commit()
    _log_audit("ban" if action == "ban" else "unban", "user", user_id, {"email": target_user.email})

    return jsonify({
        "status": "updated",
        "user_id": user_id,
        "action": action,
    })


@bp.route("/api/users/banned", methods=["GET"])
@login_required
def list_banned_users():
    from models import User

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    banned = User.query.filter_by(banned=True).all()
    return jsonify([
        {
            "id": u.id,
            "prenom": u.prenom,
            "nom": u.nom,
            "email": u.email,
            "created_at": u.created_at.isoformat() if hasattr(u, "created_at") else None,
            "banned": u.banned,
        }
        for u in banned
    ])


@bp.route("/api/reports", methods=["POST"])
@login_required
def create_report():
    from models import User, Item, Report

    current_user = get_current_user()
    data = request.get_json(silent=True) or {}

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
        reason=reason,
        description=description,
        status="pending",
    )

    if target_type == "user":
        reported_user = db.session.get(User, target_id)
        if not reported_user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        if reported_user.id == current_user.id:
            return jsonify({"error": "Impossible de se signaler soi-même"}), 400
        report.reported_user_id = reported_user.id
    else:
        item_type_map = {"geodonnee": "geodonnee", "carte": "carte", "application": "application"}
        if target_type not in item_type_map:
            return jsonify({"error": "Type de contenu invalide"}), 400
        item = Item.query.filter_by(id=target_id, type=item_type_map[target_type]).first()
        if not item:
            return jsonify({"error": "Contenu introuvable"}), 404
        full_name = f"{current_user.prenom} {current_user.nom}"
        if item.author_name and item.author_name == full_name:
            return jsonify({"error": "Impossible de signaler son propre contenu"}), 400
        report.target_item_id = target_id

    db.session.add(report)
    db.session.commit()

    return jsonify({"status": "created", "report_id": report.id})


@bp.route("/api/admin/reports", methods=["GET"])
@login_required
def list_reports():
    from models import Report

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    status_filter = request.args.get("status", "all")
    report_type = request.args.get("type", "all")
    page = int(request.args.get("page", 1))
    per_page = 30

    query = Report.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if report_type != "all":
        query = query.filter_by(report_type=report_type)

    total_items = query.count()
    per_page = per_page or 30
    paginated_reports = query.order_by(Report.created_at.desc()).limit(per_page).offset((page - 1) * per_page).all()
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
    page_numbers = _build_page_numbers(page, total_pages)
    return jsonify({
        "reports": [
            {
                "id": r.id,
                "reporter": {"id": r.reporter.id, "name": str(r.reporter)} if r.reporter else None,
                "reported_user": {"id": r.reported_user.id, "name": str(r.reported_user)} if r.reported_user else None,
                "target_item_id": r.target_item_id,
                "report_type": r.report_type,
                "reason": r.reason,
                "description": r.description,
                "status": r.status,
                "reviewed_by": {"id": r.reviewer.id, "name": str(r.reviewer)} if r.reviewer else None,
                "reviewed_at": r.reviewed_at.isoformat() if hasattr(r, "reviewed_at") and r.reviewed_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in paginated_reports
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page_numbers": page_numbers,
    })


@bp.route("/api/admin/reports/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    from models import Report

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    report = Report.query.get_or_404(report_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")

    if new_status not in ("resolved", "dismissed"):
        return jsonify({"error": "Statut invalide"}), 400

    report.status = new_status
    report.reviewed_by = current_user.id
    report.reviewed_at = dt.datetime.now()

    db.session.commit()
    _log_audit(new_status, "report", report_id, {"reason": report.reason, "description": report.description})

    return jsonify({"status": "updated", "report_id": report.id})


@bp.route("/admin/users")
@bp.route("/admin/users/<int:page>")
@login_required
@require_admin
def admin_users(page=None):
    from models import User

    if page is not None and (page < 1 or page > 9999):
        return redirect(url_for("admin.admin_users"))
    p = request.args.get("page", 1, type=int)
    if page is not None:
        p = int(page)
    else:
        p = min(max(p, 1), 9999)
    query = User.query.order_by(User.id)
    total_items = query.count()
    total_pages = max((total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE, 1)
    p = min(max(p, 1), total_pages) or 1
    users = query.offset((p - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
    page_numbers = _build_page_numbers(p, total_pages)
    return render_template(
        "admin/users.html",
        title="Administration — Utilisateurs",
        meta_description="Liste des utilisateurs",
        users=users,
        page=p,
        total_pages=total_pages,
        page_numbers=page_numbers,
        total_items=total_items,
    )


@bp.route("/admin/reports")
@login_required
@require_admin
def admin_reports():
    return render_template(
        "admin/reports.html",
        title="Administration — Signalements",
        meta_description="Liste des signalements",
    )


@bp.route("/api/admin/comments", methods=["GET"])
@login_required
def list_comments():
    from models import Comment

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item_id = request.args.get("item_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", ITEMS_PER_PAGE, type=int)

    query = Comment.query
    if item_id:
        query = query.filter_by(item_id=item_id)

    # Support since filter for recent/old filtering
    since_param = request.args.get("since")
    if since_param:
        try:
            since_date = dt.datetime.fromisoformat(since_param)
            query = query.filter(Comment.created_at >= since_date)
        except (ValueError, TypeError):
            pass

    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1

    paginated_comments = query.order_by(Comment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    page_numbers = _build_page_numbers(page, total_pages)

    return jsonify({
        "comments": [
            {
                "id": c.id,
                "item_id": c.item_id,
                "author_name": c.author_name,
                "content": c.content,
                "created_at": c.created_at.isoformat() if hasattr(c, "created_at") and c.created_at else None,
                "item_title": c.item.title if c.item else None,
                "item_type": c.item.type if c.item else None,
            }
            for c in paginated_comments
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page_numbers": page_numbers,
    })


@bp.route("/api/admin/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    from models import Comment

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    comment = Comment.query.get_or_404(comment_id)
    item_title = comment.item.title if comment.item else None
    db.session.delete(comment)
    db.session.commit()
    _log_audit("comment_deleted", "comment", comment_id, {"item_title": item_title, "content_preview": (comment.content[:80] if comment.content else "")})
    return jsonify({"status": "deleted", "comment_id": comment_id})


@bp.route("/api/admin/items", methods=["GET"])
@login_required
def list_items():
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item_type = request.args.get("type", "all")
    status_filter = request.args.get("status", "all")
    page = int(request.args.get("page", 1))
    per_page = 30

    query = Item.query
    if item_type != "all":
        query = query.filter_by(type=item_type)

    total_items = query.count()
    paginated = query.order_by(Item.created_at.desc()).limit(per_page).offset((page - 1) * per_page).all()
    page_numbers = _build_page_numbers(page, (total_items + per_page - 1) // per_page)
    return jsonify({
        "items": [
            {
                "id": it.id,
                "type": it.type,
                "title": it.title,
                "description": it.description[:100],
                "author_name": it.author_name,
                "verification_status": it.verification_status,
                "created_at": it.created_at.isoformat() if hasattr(it, "created_at") and it.created_at else None,
                "comment_count": len(it.comments),
            }
            for it in paginated
        ],
        "page": page,
        "total_pages": ((total_items + per_page - 1) // per_page),
        "total_items": total_items,
        "page_numbers": page_numbers,
    })


@bp.route("/api/admin/items/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item = Item.query.get_or_404(item_id)
    title = item.title
    type_name = item.type
    db.session.delete(item)
    db.session.commit()
    _log_audit("item_deleted", "item", item_id, {"title": title, "type": type_name})
    return jsonify({"status": "deleted", "item_id": item_id, "title": title})


@bp.route("/api/admin/items/<int:item_id>/verify", methods=["POST"])
@login_required
def verify_item(item_id):
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item = Item.query.get_or_404(item_id)
    item.verification_status = 'verified'
    item.verifier_user_id = current_user.id
    item.verified_at = db.func.now()
    db.session.commit()
    _log_audit("item_verified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "verified"})


@bp.route("/api/admin/items/<int:item_id>/unverify", methods=["POST"])
@login_required
def unverify_item(item_id):
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item = Item.query.get_or_404(item_id)
    item.verification_status = 'unofficial'
    item.verifier_user_id = None
    item.verified_at = None
    db.session.commit()
    _log_audit("item_unverified", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "verification_status": "unofficial"})


@bp.route("/api/admin/audit")
@login_required
def admin_audit_log():
    """API endpoint for fetching audit log entries."""
    from models import AdminAudit

    if not get_current_user() or not get_current_user().is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = 50
    query = AdminAudit.query.order_by(AdminAudit.created_at.desc())
    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1
    paginated_entries = query.offset((page - 1) * per_page).limit(per_page).all()
    entries = _get_audit_entries(paginated_entries)
    return jsonify({
        "entries": entries,
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
    })


@bp.route("/admin/audit")
@login_required
@require_admin
def admin_audit():
    return render_template(
        "admin/audit.html",
        title="Administration — Journal d'audits",
        meta_description="Journal des actions administratives",
    )


@bp.route("/admin/moderation")
@login_required
@require_admin
def admin_moderation():
    return render_template(
        "admin/moderation.html",
        title="Administration — Modération",
        meta_description="Modération des contenus et commentaires",
    )


@bp.route("/admin/contact-messages")
@login_required
@require_admin
def admin_contact_messages():
    return render_template(
        "admin/contact_messages.html",
        title="Administration — Messages de contact",
        meta_description="Messages reçus via la page contact",
    )


@bp.route("/api/admin/contact-messages", methods=["GET"])
@login_required
def list_contact_messages():
    from models import ContactMessage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = 30
    status_filter = request.args.get("status", "all")

    query = ContactMessage.query
    if status_filter == "unread":
        query = query.filter_by(is_read=False)
    elif status_filter == "read":
        query = query.filter_by(is_read=True)

    total_items = query.count()
    total_pages = max((total_items + per_page - 1) // per_page, 1)
    page = min(max(page, 1), total_pages) or 1

    paginated = query.order_by(ContactMessage.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    page_numbers = _build_page_numbers(page, total_pages)

    return jsonify({
        "messages": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "subject": m.subject,
                "message": m.message,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat() if hasattr(m, "created_at") and m.created_at else None,
            }
            for m in paginated
        ],
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page_numbers": page_numbers,
    })


@bp.route("/api/admin/contact-messages/<int:msg_id>/read", methods=["POST"])
@login_required
def mark_contact_message_read(msg_id):
    from models import ContactMessage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    msg = ContactMessage.query.get_or_404(msg_id)
    data = request.get_json(silent=True) or {}
    is_read = data.get("is_read", True)
    msg.is_read = bool(is_read)
    db.session.commit()

    return jsonify({"status": "updated", "id": msg.id, "is_read": msg.is_read})


@bp.route("/api/admin/contact-messages/<int:msg_id>", methods=["DELETE"])
@login_required
def delete_contact_message(msg_id):
    from models import ContactMessage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    _log_audit("contact_message_deleted", "contact_message", msg_id, {"name": msg.name, "subject": msg.subject})

    return jsonify({"status": "deleted", "id": msg_id})


@bp.route("/admin/mirrors")
@login_required
@require_admin
def admin_mirrors():
    return render_template(
        "admin/mirrors.html",
        title="Administration — Sites miroirs",
        meta_description="Gestion des sites miroirs",
    )


@bp.route("/api/admin/mirrors", methods=["GET"])
@login_required
def list_mirrors():
    from models import MirrorSite

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    mirrors = MirrorSite.query.order_by(MirrorSite.display_order, MirrorSite.id).all()
    return jsonify({
        "mirrors": [
            {
                "id": m.id,
                "name": m.name,
                "url": m.url,
                "description": m.description,
                "display_order": m.display_order,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if hasattr(m, "created_at") and m.created_at else None,
            }
            for m in mirrors
        ],
    })


@bp.route("/api/admin/mirrors", methods=["POST"])
@login_required
def create_mirror():
    from models import MirrorSite

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    description = (data.get("description") or "").strip()

    if not name or not url or not description:
        return jsonify({"error": "Tous les champs sont requis."}), 400

    if len(name) > 200 or len(url) > 500 or len(description) > 500:
        return jsonify({"error": "Champs trop longs."}), 400

    max_order = db.session.query(db.func.max(MirrorSite.display_order)).scalar() or 0
    mirror = MirrorSite(
        name=sanitize_html(name),
        url=sanitize_html(url),
        description=sanitize_html(description),
        display_order=max_order + 1,
        is_active=True,
    )
    db.session.add(mirror)
    db.session.commit()
    _log_audit("mirror_created", "mirror", mirror.id, {"name": mirror.name, "url": mirror.url})

    return jsonify({"status": "created", "mirror": {
        "id": mirror.id,
        "name": mirror.name,
        "url": mirror.url,
        "description": mirror.description,
        "display_order": mirror.display_order,
        "is_active": mirror.is_active,
    }})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["PUT"])
@login_required
def update_mirror(mirror_id):
    from models import MirrorSite

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    mirror = MirrorSite.query.get_or_404(mirror_id)
    data = request.get_json(silent=True) or {}

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

    return jsonify({"status": "updated", "mirror": {
        "id": mirror.id,
        "name": mirror.name,
        "url": mirror.url,
        "description": mirror.description,
        "display_order": mirror.display_order,
        "is_active": mirror.is_active,
    }})


@bp.route("/api/admin/mirrors/<int:mirror_id>", methods=["DELETE"])
@login_required
def delete_mirror(mirror_id):
    from models import MirrorSite

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    mirror = MirrorSite.query.get_or_404(mirror_id)
    name = mirror.name
    db.session.delete(mirror)
    db.session.commit()
    _log_audit("mirror_deleted", "mirror", mirror_id, {"name": name})

    return jsonify({"status": "deleted", "id": mirror_id})


@bp.route("/admin/featured")
@login_required
@require_admin
def admin_featured():
    return render_template(
        "admin/featured.html",
        title="Administration — Données en avant",
        meta_description="Gestion des données mises en avant sur la page d'accueil",
    )


@bp.route("/api/admin/featured", methods=["GET"])
@login_required
def list_featured():
    from models import FeaturedItem

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    featured = FeaturedItem.query.order_by(FeaturedItem.display_order, FeaturedItem.id).all()
    return jsonify({
        "featured": [
            {
                "id": f.id,
                "item_id": f.item_id,
                "item_title": f.item.title if f.item else None,
                "item_type": f.item.type if f.item else None,
                "item_format": f.item.format_type if f.item else None,
                "item_description": f.item.description[:100] if f.item else None,
                "display_order": f.display_order,
                "is_active": f.is_active,
            }
            for f in featured
        ],
    })


@bp.route("/api/admin/items/search", methods=["GET"])
@login_required
def search_items():
    """Search items for autocomplete in featured item selector."""
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    q = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 20))

    query = Item.query.filter(Item.status == "published")
    if q:
        query = query.filter(Item.title.ilike(f"%{q}%"))

    items = query.order_by(Item.title).limit(limit).all()
    return jsonify({
        "items": [
            {
                "id": it.id,
                "title": it.title,
                "type": it.type,
                "format_type": it.format_type,
                "description": it.description[:100] if it.description else "",
            }
            for it in items
        ],
    })


@bp.route("/api/admin/featured", methods=["POST"])
@login_required
def create_featured():
    from models import FeaturedItem, Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id requis."}), 400

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item introuvable."}), 404

    existing = FeaturedItem.query.filter_by(item_id=item_id).first()
    if existing:
        return jsonify({"error": "Cet item est déjà mis en avant."}), 409

    max_order = db.session.query(db.func.max(FeaturedItem.display_order)).scalar() or 0
    featured = FeaturedItem(
        item_id=item_id,
        display_order=max_order + 1,
        is_active=True,
    )
    db.session.add(featured)
    db.session.commit()
    _log_audit("featured_created", "featured", featured.id, {"item_id": item_id, "title": item.title})

    return jsonify({"status": "created", "featured": {
        "id": featured.id,
        "item_id": featured.item_id,
        "item_title": item.title,
        "item_type": item.type,
        "item_format": item.format_type,
        "item_description": item.description[:100] if item.description else "",
        "display_order": featured.display_order,
        "is_active": featured.is_active,
    }})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["PUT"])
@login_required
def update_featured(featured_id):
    from models import FeaturedItem

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    featured = FeaturedItem.query.get_or_404(featured_id)
    data = request.get_json(silent=True) or {}

    if "display_order" in data:
        featured.display_order = int(data["display_order"])
    if "is_active" in data:
        featured.is_active = bool(data["is_active"])

    db.session.commit()
    _log_audit("featured_updated", "featured", featured_id, {"item_id": featured.item_id})

    return jsonify({"status": "updated", "featured": {
        "id": featured.id,
        "item_id": featured.item_id,
        "item_title": featured.item.title if featured.item else None,
        "display_order": featured.display_order,
        "is_active": featured.is_active,
    }})


@bp.route("/api/admin/featured/<int:featured_id>", methods=["DELETE"])
@login_required
def delete_featured(featured_id):
    from models import FeaturedItem

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    featured = FeaturedItem.query.get_or_404(featured_id)
    title = featured.item.title if featured.item else None
    db.session.delete(featured)
    db.session.commit()
    _log_audit("featured_deleted", "featured", featured_id, {"title": title})

    return jsonify({"status": "deleted", "id": featured_id})


@bp.route("/admin/geopackages")
@login_required
@require_admin
def admin_geopackages():
    return render_template(
        "admin/geopackages.html",
        title="Administration — GeoPackages",
        meta_description="Gestion des packs GeoPackage affichés sur la page d'accueil",
    )


@bp.route("/api/admin/geopackages", methods=["GET"])
@login_required
def list_geopackages():
    from models import GeoPackage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    packages = GeoPackage.query.order_by(GeoPackage.display_order, GeoPackage.id).all()
    return jsonify({
        "packages": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "format_info": p.format_info,
                "link_url": p.link_url,
                "display_order": p.display_order,
                "is_active": p.is_active,
            }
            for p in packages
        ],
    })


@bp.route("/api/admin/geopackages", methods=["POST"])
@login_required
def create_geopackage():
    from models import GeoPackage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    data = request.get_json(silent=True) or {}
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
        title=sanitize_html(title),
        description=sanitize_html(description),
        format_info=sanitize_html(format_info),
        link_url=sanitize_html(link_url),
        display_order=max_order + 1,
        is_active=True,
    )
    db.session.add(pkg)
    db.session.commit()
    _log_audit("geopackage_created", "geopackage", pkg.id, {"title": pkg.title})

    return jsonify({"status": "created", "package": {
        "id": pkg.id, "title": pkg.title, "description": pkg.description,
        "format_info": pkg.format_info, "link_url": pkg.link_url,
        "display_order": pkg.display_order, "is_active": pkg.is_active,
    }})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["PUT"])
@login_required
def update_geopackage(pkg_id):
    from models import GeoPackage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    pkg = GeoPackage.query.get_or_404(pkg_id)
    data = request.get_json(silent=True) or {}

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

    return jsonify({"status": "updated", "package": {
        "id": pkg.id, "title": pkg.title, "description": pkg.description,
        "format_info": pkg.format_info, "link_url": pkg.link_url,
        "display_order": pkg.display_order, "is_active": pkg.is_active,
    }})


@bp.route("/api/admin/geopackages/<int:pkg_id>", methods=["DELETE"])
@login_required
def delete_geopackage(pkg_id):
    from models import GeoPackage

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    pkg = GeoPackage.query.get_or_404(pkg_id)
    title = pkg.title
    db.session.delete(pkg)
    db.session.commit()
    _log_audit("geopackage_deleted", "geopackage", pkg_id, {"title": title})

    return jsonify({"status": "deleted", "id": pkg_id})
