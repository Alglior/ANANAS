import datetime
import random
import string
import unicodedata

from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, limiter
from utils.security import sanitize_html
from src.shared import validate_password_strength

bp = Blueprint("auth", __name__)


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def _generate_pseudo(prenom: str, nom: str) -> str:
    from models import User

    base = f"{_normalize(prenom).lower()}-{_normalize(nom).lower().replace(' ', '-')}"
    while True:
        letters = ''.join(random.choices(string.ascii_lowercase, k=2))
        digits = ''.join(random.choices(string.digits, k=4))
        pseudo = f"{base}#{letters}{digits}"
        if not User.query.filter_by(pseudo=pseudo).first():
            return pseudo


@bp.route("/connexion")
def connexion_page():
    pseudo = request.args.get("pseudo", "")
    return render_template(
        "connexion.html",
        title="A.N.A.N.A.S | Connexion",
        meta_description="Connectez-vous à votre compte A.N.A.N.A.S",
        pseudo=pseudo,
    )


@bp.route("/connexion", methods=["POST"])
@limiter.limit("5 per hour")
def connexion_post():
    pseudo = request.form.get("pseudo", "").strip()
    password = request.form.get("password", "")

    from models import User

    user = User.query.filter_by(pseudo=pseudo).first()
    if user and check_password_hash(user.password_hash, password) and user.is_active and not user.banned:
        session.clear()
        session.pop("_csrf_token", None)
        session["user_id"] = user.id
        session["session_version"] = user.session_version
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
    password = request.form.get("password", "")

    from models import User

    strength_ok, strength_errors = validate_password_strength(password)
    if not strength_ok:
        return render_template("inscription.html", form_errors=strength_errors, password=password, prenom=prenom, nom=nom), 400

    user_hash = generate_password_hash(password, method="scrypt")

    user = User(
        prenom=prenom,
        nom=nom,
        pseudo=_generate_pseudo(prenom, nom),
        password_hash=user_hash,
        is_active=True,
        banned=False,
    )
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("auth.connexion_page", pseudo=user.pseudo))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index.home"))
