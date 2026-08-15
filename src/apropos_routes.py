from flask import Blueprint, render_template

bp = Blueprint("apropos", __name__)


@bp.route("/apropos")
def apropos_page():
    return render_template(
        "apropos.html",
        title="A.N.A.N.A.S | A propos",
        meta_description="Découvrez le projet A.N.A.N.A.S : sa mission, son fonctionnement et les technologies utilisées.",
    )
