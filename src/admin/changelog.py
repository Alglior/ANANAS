import os
from pathlib import Path

import mistune

from flask import render_template
from src.admin import bp, login_required, require_admin


@bp.route("/admin/changelog")
@login_required
@require_admin
def admin_changelog():
    changelog_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "CHANGELOG.md"
    content = ""
    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    html_content = mistune.html(content)
    return render_template(
        "admin/changelog.html",
        title="Administration — Mise à jour",
        meta_description="Historique des mises à jour de la plateforme",
        changelog_html=html_content,
    )