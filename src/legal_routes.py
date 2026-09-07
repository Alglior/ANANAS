from flask import Blueprint, render_template

bp = Blueprint("legal", __name__)


@bp.route("/mentions-legales")
def legal_page():
    return render_template(
        "legal.html",
        title="A.N.A.N.A.S | Mentions légales",
        meta_description="Mentions légales de la plateforme A.N.A.N.A.S — éditeur, hébergement, propriété intellectuelle et responsabilité.",
    )