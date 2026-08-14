import datetime as dt

from flask import request, jsonify, render_template
from app import db
from src.admin import bp, api_admin_required, require_admin, login_required
from src.admin import get_current_user, _serialize_user, _log_audit, _paginate
from src.shared import ITEMS_PER_PAGE
from models import User


@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
@api_admin_required
def ban_user(user_id):

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
    user.session_version += 1
    db.session.commit()
    _log_audit("ban", "user", user.id, {"pseudo": user.pseudo, "duration": "permanent"})
    return jsonify({"status": "updated", "user_id": user.id, "action": "ban"})


def _do_unban(user):
    user.banned = False
    user.is_active = True
    db.session.commit()
    _log_audit("unban", "user", user.id, {"pseudo": user.pseudo})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unban"})


def _do_tempban(user, duration):
    try:
        hours = int(duration)
    except (TypeError, ValueError):
        return jsonify({"error": "Durée invalide"}), 400
    ban_until = dt.datetime.now() + dt.timedelta(hours=hours)
    user.banned = True
    user.is_active = False
    user.session_version += 1
    db.session.commit()
    _log_audit("tempban", "user", user.id, {"pseudo": user.pseudo, "duration_hours": hours, "ban_until": ban_until.isoformat()})
    return jsonify({"status": "updated", "user_id": user.id, "action": "tempban", "ban_until": ban_until.isoformat()})


def _do_mute(user, duration):
    try:
        hours = int(duration)
    except (TypeError, ValueError):
        return jsonify({"error": "Durée invalide"}), 400
    user.muted_until = dt.datetime.now() + dt.timedelta(hours=hours)
    db.session.commit()
    _log_audit("mute", "user", user.id, {"pseudo": user.pseudo, "duration_hours": hours, "muted_until": user.muted_until.isoformat()})
    return jsonify({"status": "updated", "user_id": user.id, "action": "mute", "muted_until": user.muted_until.isoformat()})


def _do_unmute(user):
    user.muted_until = None
    db.session.commit()
    _log_audit("unmute", "user", user.id, {"pseudo": user.pseudo})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unmute"})


def _do_warn(user, data):
    reason = data.get("reason", "")
    user.warned = True
    user.warnings = (user.warnings or "") + f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}] {reason}\n"
    db.session.commit()
    _log_audit("warn", "user", user.id, {"pseudo": user.pseudo, "reason": reason})
    return jsonify({"status": "updated", "user_id": user.id, "action": "warn"})


def _do_unwarn(user):
    user.warned = False
    user.warnings = None
    db.session.commit()
    _log_audit("unwarn", "user", user.id, {"pseudo": user.pseudo})
    return jsonify({"status": "updated", "user_id": user.id, "action": "unwarn"})


def _do_kick(user):
    db.session.commit()
    _log_audit("kick", "user", user.id, {"pseudo": user.pseudo})
    return jsonify({"status": "updated", "user_id": user.id, "action": "kick"})


@bp.route("/api/users/banned", methods=["GET"])
@login_required
@api_admin_required
def list_banned_users():
    banned = User.query.filter_by(banned=True).all()
    return jsonify([_serialize_user(u) for u in banned])


@bp.route("/admin/users")
@bp.route("/admin/users/<int:page>")
@login_required
@require_admin
def admin_users(page=None):
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