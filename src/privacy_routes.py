from flask import Blueprint, render_template

bp = Blueprint("privacy", __name__)


@bp.route("/confidentialite")
def privacy_page():
    return render_template(
        "privacy.html",
        title="A.N.A.N.A.S. | Politique de confidentialité",
        meta_description="Politique de confidentialité de la plateforme A.N.A.N.A.S. — traitement des données, cookies et droits RGPD.",
    )