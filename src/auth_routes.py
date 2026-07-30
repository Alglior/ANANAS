import datetime

from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, limiter
from utils.security import sanitize_html
from src.shared import validate_password_strength

bp = Blueprint("auth", __name__)


@bp.route("/connexion")
def connexion_page():
    return render_template(
        "connexion.html",
        title="A.N.A.N.A.S | Connexion",
        meta_description="Connectez-vous à votre compte A.N.A.N.A.S",
    )


@bp.route("/connexion", methods=["POST"])
@limiter.limit("5 per hour")
def connexion_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    from models import User

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
        session.clear()
        session.pop("_csrf_token", None)
        session["user_id"] = user.id
        session["_auth_time"] = datetime.datetime.now().isoformat()
        session.modified = True
        return redirect(url_for("index.home"))

    if user and (not user.is_active or user.banned):
        return render_template("connexion.html", error="banned"), 401

    return render_template("connexion.html", error="Identifiants incorrects"), 401


@bp.route("/inscription")
def inscription_page():
    return render_template(
        "inscription.html",
        title="A.N.A.N.A.S | Inscription",
        meta_description="Créer un compte A.N.A.N.A.S",
    )


@bp.route("/inscription", methods=["POST"])
@limiter.limit("3 per hour")
def inscription_post():
    prenom = sanitize_html(request.form.get("prenom", "").strip())
    nom = sanitize_html(request.form.get("nom", "").strip())
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    from models import User

    strength_ok, strength_errors = validate_password_strength(password)
    if not strength_ok:
        return render_template("inscription.html", form_errors=strength_errors, password=password, email=email, prenom=prenom, nom=nom), 400

    user_hash = generate_password_hash(password, method="scrypt")
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        form_errors = ["Désolé, cet email est déjà utilisé."]
        return render_template("inscription.html", form_errors=form_errors, password=password, email=email, prenom=prenom, nom=nom)

    user = User(
        prenom=prenom,
        nom=nom,
        email=email,
        password_hash=user_hash,
        is_active=True,
        banned=False,
    )
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("auth.connexion_page"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index.home"))
