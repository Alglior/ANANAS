from flask import request, jsonify
from app import db
from src.admin import bp, api_admin_required, login_required, _log_audit, _require_json
from models import HomeSection
from utils.security import sanitize_html


@bp.route("/api/admin/home-sections", methods=["GET"])
@login_required
@api_admin_required
def list_home_sections():
    sections = HomeSection.query.order_by(HomeSection.display_order).all()
    if not sections:
        _seed_default_sections()
        sections = HomeSection.query.order_by(HomeSection.display_order).all()
    return jsonify({"sections": [_serialize(hs) for hs in sections]})


@bp.route("/api/admin/home-sections", methods=["POST"])
@login_required
@api_admin_required
def create_home_section():
    data, error, code = _require_json()
    if error:
        return error, code
    section_type = (data.get("section_type") or "").strip()
    title = (data.get("title") or "").strip()
    if not section_type or not title:
        return jsonify({"error": "section_type et title requis"}), 400
    if HomeSection.query.filter_by(section_type=section_type).first():
        return jsonify({"error": "Un section avec ce type existe déjà"}), 409

    max_order = db.session.query(db.func.max(HomeSection.display_order)).scalar() or 0
    hs = HomeSection(
        section_type=section_type, title=title,
        enabled=data.get("enabled", True), display_order=max_order + 1,
        is_builtin=False,
    )
    db.session.add(hs)
    db.session.commit()
    _log_audit("home_section_create", "home_section", hs.id, {"section_type": section_type, "title": title})
    return jsonify({"status": "created", "section": _serialize(hs)}), 201


@bp.route("/api/admin/home-sections/<int:section_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_home_section(section_id):
    data, error, code = _require_json()
    if error:
        return error, code
    hs = db.session.get(HomeSection, section_id)
    if not hs:
        return jsonify({"error": "Section introuvable"}), 404
    if "title" in data:
        hs.title = sanitize_html(data["title"].strip())
    if "content" in data:
        hs.content = sanitize_html(data["content"])
    if "enabled" in data:
        hs.enabled = bool(data["enabled"])
    if "display_order" in data:
        hs.display_order = int(data["display_order"])
    db.session.commit()
    _log_audit("home_section_update", "home_section", hs.id, data)
    return jsonify({"status": "updated", "section": _serialize(hs)})


@bp.route("/api/admin/home-sections/<int:section_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_home_section(section_id):
    hs = db.session.get(HomeSection, section_id)
    if not hs:
        return jsonify({"error": "Section introuvable"}), 404
    if hs.is_builtin:
        return jsonify({"error": "Impossible de supprimer une section système"}), 400
    db.session.delete(hs)
    db.session.commit()
    _log_audit("home_section_delete", "home_section", hs.id, {"section_type": hs.section_type})
    return jsonify({"status": "deleted"})


@bp.route("/api/admin/home-sections/reorder", methods=["POST"])
@login_required
@api_admin_required
def reorder_home_sections():
    data = _require_json()
    if data is None or "order" not in data:
        return jsonify({"error": "Liste order requise"}), 400
    for idx, section_id in enumerate(data["order"]):
        hs = db.session.get(HomeSection, section_id)
        if hs:
            hs.display_order = idx
    db.session.commit()
    _log_audit("home_section_reorder", "home_section", details={"order": data["order"]})
    return jsonify({"status": "reordered"})


def _serialize(hs):
    return {
        "id": hs.id, "section_type": hs.section_type, "title": hs.title,
        "content": hs.content, "enabled": hs.enabled, "display_order": hs.display_order,
        "is_builtin": hs.is_builtin,
    }


def _seed_default_sections():
    existing = {s.section_type for s in HomeSection.query.all()}
    for i, info in enumerate(HomeSection.BUILTIN_SECTIONS):
        if info["type"] not in existing:
            db.session.add(HomeSection(
                section_type=info["type"], title=info["title"],
                enabled=True, display_order=i, is_builtin=True,
            ))
    db.session.commit()