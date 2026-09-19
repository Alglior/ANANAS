import os
from pathlib import Path

import mistune

from flask import Blueprint, render_template


bp = Blueprint("changelog", __name__)


@bp.route("/feuille-de-route")
def roadmap_page():
    roadmap_path = Path(os.path.dirname(os.path.dirname(__file__))) / "ROADMAP.md"
    content = ""
    if roadmap_path.exists():
        content = roadmap_path.read_text(encoding="utf-8")
    html_content = mistune.html(content)
    return render_template(
        "roadmap.html",
        title="A.N.A.N.A.S | Feuille de route",
        meta_description="Feuille de route du projet A.N.A.N.A.S : évolutions prévues et visions à long terme.",
        roadmap_html=html_content,
    )


@bp.route("/changelog")
def changelog_page():
    changelog_path = Path(os.path.dirname(os.path.dirname(__file__))) / "CHANGELOG.md"
    content = ""
    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    html_content = mistune.html(content)
    return render_template(
        "changelog.html",
        title="A.N.A.N.A.S | Mise à jour",
        meta_description="Historique des mises à jour et évolutions de la plateforme A.N.A.N.A.S.",
        changelog_html=html_content,
    )