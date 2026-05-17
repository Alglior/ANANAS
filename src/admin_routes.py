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
    if status_filter == "published":
        query = query.filter_by(is_published=True)
    elif status_filter == "unpublished":
        query = query.filter_by(is_published=False)

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
                "is_published": it.is_published,
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


@bp.route("/api/admin/items/<int:item_id>/unpublish", methods=["POST"])
@login_required
def unpublish_item(item_id):
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item = Item.query.get_or_404(item_id)
    item.is_published = False
    db.session.commit()
    _log_audit("item_unpublished", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "is_published": False})


@bp.route("/api/admin/items/<int:item_id>/publish", methods=["POST"])
@login_required
def publish_item(item_id):
    from models import Item

    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({"error": "Non autorisé"}), 403

    item = Item.query.get_or_404(item_id)
    item.is_published = True
    db.session.commit()
    _log_audit("item_published", "item", item_id, {"title": item.title})
    return jsonify({"status": "updated", "item_id": item_id, "is_published": True})


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
