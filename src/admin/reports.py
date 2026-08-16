import datetime as dt

from flask import request, jsonify
from app import db
from src.admin import bp, login_required, api_admin_required
from src.admin import get_current_user, _serialize_report, _log_audit, _paginate, _require_json
from utils.security import sanitize_html
from models import Report, User, Item


@bp.route("/api/reports", methods=["POST"])
@login_required
def create_report():

    current_user = get_current_user()
    data, error, code = _require_json()
    if error:
        return error, code

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

    report = Report.query.get_or_404(report_id)
    data, error, code = _require_json()
    if error:
        return error, code
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