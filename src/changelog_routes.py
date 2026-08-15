import json

from flask import Blueprint, render_template

from app import db
from models import ChangelogVersion

bp = Blueprint("changelog", __name__)


@bp.route("/changelog")
def changelog_page():
    versions_db = (
        ChangelogVersion.query
        .filter_by(is_active=True)
        .order_by(ChangelogVersion.display_order.desc(), ChangelogVersion.id.desc())
        .all()
    )

    versions = []
    for v in versions_db:
        sections = []
        for s in v.sections:
            items = json.loads(s.items) if isinstance(s.items, str) else s.items
            sections.append({"title": s.title, "entries": items})
        versions.append({"version": v.version, "date": v.date, "sections": sections})

    return render_template(
        "changelog.html",
        title="A.N.A.N.A.S | Changelog",
        meta_description="Historique des mises à jour et évolutions de la plateforme A.N.A.N.A.S.",
        versions=versions,
    )
