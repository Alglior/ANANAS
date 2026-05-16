import re

from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from utils.security import sanitize_html

bp = Blueprint("auth", __name__)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    errors = []
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères")
    if not re.search(r"[A-Z]", password):
        errors.append("Le mot de passe doit contenir au moins une majuscule")
    if not re.search(r"[a-z]", password):
        errors.append("Le mot de passe doit contenir au moins une minuscule")
    if not re.search(r"\d", password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    if not re.search(r"[!@#$%^&*()_+\-={}\[\];':\"\\|,.<>/?~`]", password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...)")
    return len(errors) == 0, errors


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


@bp.route("/inscription", methods=["POST"])
def inscription_post():
    prenom = sanitize_html(request.form.get("prenom", "").strip())
    nom = sanitize_html(request.form.get("nom", "").strip())
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    from models import User

    strength_ok, strength_errors = validate_password_strength(password)
    if not strength_ok:
        return render_template("inscription.html", form_errors=strength_errors, password=password, email=email, prenom=prenom, nom=nom), 400

    if User.query.filter_by(email=email).first():
        return redirect(url_for("auth.connexion_page"))

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
