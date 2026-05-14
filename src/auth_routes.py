from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

bp = Blueprint("auth", __name__)


@bp.route("/connexion")
def connexion_page():
    return render_template(
        "connexion.html",
        title="A.N.A.N.A.S. | Connexion",
        meta_description="Connectez-vous à votre compte A.N.A.N.A.S.",
    )


@bp.route("/inscription")
def inscription_page():
    return render_template(
        "inscription.html",
        title="A.N.A.N.A.S. | Inscription",
        meta_description="Créer un compte A.N.A.N.A.S.",
    )


@bp.route("/connexion", methods=["POST"])
def connexion_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    from models import User

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
        session["user_id"] = user.id
        return redirect(url_for("home"))

    if user and (not user.is_active or user.banned):
        return render_template("connexion.html", error="banned"), 401

    return render_template("connexion.html", error="Identifiants incorrects"), 401


@bp.route("/inscription", methods=["POST"])
def inscription_post():
    prenom = request.form.get("prenom", "").strip()
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    from models import User

    if User.query.filter_by(email=email).first():
        return render_template(
            "inscription.html", error="Un compte avec cet e-mail existe déjà"
        ), 400

    user = User(
        prenom=prenom,
        nom=nom,
        email=email,
        password_hash=generate_password_hash(password, method="scrypt"),
        is_active=True,
        banned=False,
    )
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("auth.connexion_page"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
