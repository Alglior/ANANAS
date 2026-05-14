import datetime as dt

from flask import Blueprint, request, render_template, jsonify
from app import db
from src.shared import login_required, get_current_user

bp = Blueprint("admin", __name__)


@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
def ban_user(user_id):
    from models import User

    current_user = get_current_user()
    if not hasattr(current_user, "is_admin"):
        return jsonify({"error": "Non autorisé"}), 403

    target_user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")

    if action not in ("ban", "unban"):
        return jsonify({"error": "Action invalide"}), 400

    target_user.banned = (action == "ban")
    db.session.commit()

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
    if not hasattr(current_user, "is_admin"):
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
    description = data.get("description", "")

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
        report.target_item_id = target_id

    db.session.add(report)
    db.session.commit()

    return jsonify({"status": "created", "report_id": report.id})


@bp.route("/api/admin/reports", methods=["GET"])
@login_required
def list_reports():
    from models import Report

    current_user = get_current_user()
    if not hasattr(current_user, "is_admin"):
        return jsonify({"error": "Non autorisé"}), 403

    status_filter = request.args.get("status", "all")
    report_type = request.args.get("type", "all")

    query = Report.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if report_type != "all":
        query = query.filter_by(report_type=report_type)

    reports = query.order_by(Report.created_at.desc()).all()
    return jsonify([
        {
            "id": r.id,
            "reporter": {"id": r.reporter.id, "name": str(r.reporter)} if r.reporter else None,
            "reported_user": {"id": r.reported_user.id, "name": str(r.reported_user)} if r.reported_user else None,
            "target_item_id": r.target_item_id,
            "report_type": r.report_type,
            "reason": r.reason,
            "description": r.description,
            "status": r.status,
            "reviewed_by": {"id": r.reviewed_by.id, "name": str(r.reviewed_by)} if r.reviewed_by else None,
            "reviewed_at": r.reviewed_at.isoformat() if hasattr(r, "reviewed_at") and r.reviewed_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ])


@bp.route("/api/admin/reports/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    from models import Report

    current_user = get_current_user()
    if not hasattr(current_user, "is_admin"):
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

    return jsonify({"status": "updated", "report_id": report.id})


@bp.route("/admin/users")
@login_required
def admin_users():
    from models import User

    current_user = get_current_user()
    if not hasattr(current_user, "is_admin"):
        return jsonify({"error": "Non autorisé"}), 403

    users = User.query.all()
    return render_template(
        "admin/users.html",
        title="Administration — Utilisateurs",
        meta_description="Liste des utilisateurs",
        users=users,
    )


@bp.route("/admin/reports")
@login_required
def admin_reports():
    from models import Report

    current_user = get_current_user()
    if not hasattr(current_user, "is_admin"):
        return jsonify({"error": "Non autorisé"}), 403

    status_filter = request.args.get("status", "all")
    report_type = request.args.get("type", "all")

    query = Report.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if report_type != "all":
        query = query.filter_by(report_type=report_type)

    reports = query.order_by(Report.created_at.desc()).all()
    pending_count = Report.query.filter_by(status="pending").count()

    return render_template(
        "admin/reports.html",
        title="Administration — Signalements",
        meta_description="Liste des signalements",
        reports=reports,
        status=status_filter,
        pending_count=pending_count,
    )
