import json
import datetime

from flask import request, jsonify, render_template
from app import db
from src.admin import bp, api_admin_required, login_required, require_admin
from src.admin import _log_audit, _require_json
from models import ChangelogVersion, ChangelogSection


def _serialize_version(v):
    return {
        "id": v.id,
        "version": v.version,
        "date": v.date,
        "display_order": v.display_order,
        "is_active": v.is_active,
        "sections": [_serialize_section(s) for s in v.sections],
    }


def _serialize_section(s):
    return {
        "id": s.id,
        "title": s.title,
        "items": json.loads(s.items) if isinstance(s.items, str) else s.items,
        "display_order": s.display_order,
    }


@bp.route("/admin/changelog")
@login_required
@require_admin
def admin_changelog():
    return render_template(
        "admin/changelog.html",
        title="Administration — Changelog",
        meta_description="Gestion du changelog de la plateforme",
    )


@bp.route("/api/admin/changelog", methods=["GET"])
@login_required
@api_admin_required
def list_versions():
    versions = ChangelogVersion.query.order_by(
        ChangelogVersion.display_order.desc(), ChangelogVersion.id.desc()
    ).all()
    return jsonify({"versions": [_serialize_version(v) for v in versions]})


@bp.route("/api/admin/changelog", methods=["POST"])
@login_required
@api_admin_required
def create_version():
    data, error, code = _require_json()
    if error:
        return error, code

    version = (data.get("version") or "").strip()
    if not version:
        return jsonify({"error": "Version est requise."}), 400

    now = datetime.datetime.now()
    months_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    date = f"{months_fr[now.month - 1]} {now.year}"

    max_order = db.session.query(db.func.max(ChangelogVersion.display_order)).scalar() or 0
    v = ChangelogVersion(
        version=version,
        date=date,
        display_order=max_order + 1,
        is_active=True,
    )
    db.session.add(v)
    db.session.flush()

    for section in data.get("sections", []):
        s = ChangelogSection(
            version_id=v.id,
            title=(section.get("title") or "").strip(),
            items=json.dumps(section.get("items", [])),
            display_order=section.get("display_order", 0),
        )
        db.session.add(s)

    db.session.commit()
    _log_audit("changelog_version_created", "changelog_version", v.id, {"version": v.version})
    return jsonify({"status": "created", "version": _serialize_version(v)})


@bp.route("/api/admin/changelog/<int:version_id>", methods=["PUT"])
@login_required
@api_admin_required
def update_version(version_id):
    v = ChangelogVersion.query.get_or_404(version_id)
    data, error, code = _require_json()
    if error:
        return error, code

    if "version" in data:
        v.version = data["version"].strip()
    if "date" in data:
        v.date = data["date"].strip()
    if "display_order" in data:
        v.display_order = int(data["display_order"])
    if "is_active" in data:
        v.is_active = bool(data["is_active"])

    if "sections" in data:
        ChangelogSection.query.filter_by(version_id=v.id).delete()
        for section in data["sections"]:
            s = ChangelogSection(
                version_id=v.id,
                title=(section.get("title") or "").strip(),
                items=json.dumps(section.get("items", [])),
                display_order=section.get("display_order", 0),
            )
            db.session.add(s)

    db.session.commit()
    _log_audit("changelog_version_updated", "changelog_version", v.id, {"version": v.version})
    return jsonify({"status": "updated", "version": _serialize_version(v)})


@bp.route("/api/admin/changelog/<int:version_id>", methods=["DELETE"])
@login_required
@api_admin_required
def delete_version(version_id):
    v = ChangelogVersion.query.get_or_404(version_id)
    db.session.delete(v)
    db.session.commit()
    _log_audit("changelog_version_deleted", "changelog_version", version_id, {"version": v.version})
    return jsonify({"status": "deleted", "id": version_id})
