import datetime as dt
import os

from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from app import db
from src.shared import login_required, get_current_user, _build_page_numbers
from models import CatalogueConfig

_CATALOGUES_INFO = [
    {"type": "donnees", "label": "Géodonnées"},
    {"type": "cartes", "label": "Cartes"},
    {"type": "applications", "label": "Applications"},
]

_DEFAULT_CATALOGUES = {"donnees": True, "cartes": True, "applications": True}


def get_catalogues_status():
    rows = CatalogueConfig.query.all()
    if not rows:
        return dict(_DEFAULT_CATALOGUES)
    return {row.catalogue_type: row.enabled for row in rows}


def _save_catalogues_status(data):
    for ctype, enabled in data.items():
        row = CatalogueConfig.query.filter_by(catalogue_type=ctype).first()
        if row:
            row.enabled = bool(enabled)
        else:
            db.session.add(CatalogueConfig(catalogue_type=ctype, enabled=bool(enabled)))
    db.session.commit()


def is_catalogue_enabled(catalogue_type):
    row = CatalogueConfig.query.filter_by(catalogue_type=catalogue_type).first()
    if row is None:
        return _DEFAULT_CATALOGUES.get(catalogue_type, True)
    return row.enabled


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
                title="Accès refusé — A.N.A.N.A.S",
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
    if not request.is_json:
        return None
    return request.get_json(silent=True) or {}


def _serialize_user(u):
    return {
        "id": u.id, "prenom": u.prenom, "nom": u.nom, "pseudo": u.pseudo, "email": u.email,
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


def _serialize_simple_file(f):
    return {
        "id": f.id, "item_id": f.item_id,
        "item_title": f.item.title if f.item else None,
        "item_type": f.item.type if f.item else None,
        "item_format": f.item.format_type if f.item else None,
        "item_description": f.item.description[:100] if f.item else None,
        "display_order": f.display_order, "is_active": f.is_active,
    }


import src.admin.users
import src.admin.reports
import src.admin.pages
import src.admin.content
import src.admin.audit
import src.admin.contact
import src.admin.mirrors
import src.admin.featured
import src.admin.geopackages
import src.admin.catalogues
import src.admin.replication
import src.admin.backup
import src.admin.tags
import src.admin.simple_files