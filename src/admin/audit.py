from flask import request, jsonify
from src.admin import bp, api_admin_required, login_required, _paginate


@bp.route("/api/admin/audit")
@login_required
@api_admin_required
def admin_audit_log():

    page = request.args.get("page", 1, type=int)
    paginated, page, total_pages, total_items, _ = _paginate(
        AdminAudit.query.order_by(AdminAudit.created_at.desc()), page, 50
    )
    entries = _get_audit_entries(paginated)
    return jsonify({"entries": entries, "page": page, "total_pages": total_pages, "total_items": total_items})


def _get_audit_entries(entries=None):
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