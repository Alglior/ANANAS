from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required
from src.admin import _serialize_contact_message, _log_audit, _paginate, _get_json_data


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