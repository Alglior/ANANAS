from flask import Blueprint, render_template

bp = Blueprint("tos", __name__)


@bp.route("/conditions-utilisation")
def tos_page():
    return render_template(
        "tos.html",
        title="A.N.A.N.A.S. | Conditions d'utilisation",
        meta_description="Conditions d'utilisation de la plateforme A.N.A.N.A.S. — inscription, contenus, responsabilité et droit applicable.",
    )