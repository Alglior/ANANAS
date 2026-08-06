import datetime
import secrets
import string
import unicodedata

from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, limiter
from models import User
from utils.security import sanitize_html
from src.shared import validate_password_strength

bp = Blueprint("auth", __name__)


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def _generate_pseudo(prenom: str, nom: str) -> str:

    base = f"{_normalize(prenom).lower()}-{_normalize(nom).lower().replace(' ', '-')}"
    while True:
        letters = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(2))
        digits = ''.join(secrets.choice(string.digits) for _ in range(4))
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
@limiter.limit("50 per hour")
def connexion_post():
    pseudo = request.form.get("pseudo", "").strip()
    password = request.form.get("password", "")
    recovery_code = request.form.get("recovery_code", "").strip()

    user = User.query.filter_by(pseudo=pseudo).first()

    if not user or not user.is_active or user.banned:
        return render_template("connexion.html", recovery_code_mode=bool(recovery_code), error="banned" if user and (not user.is_active or user.banned) else "Identifiants incorrects"), 401

    authenticated = False

    if recovery_code:
        if user.recovery_codes_hash:
            for i, hashed in enumerate(user.recovery_codes_hash):
                if check_password_hash(hashed, recovery_code):
                    hashed_codes = list(user.recovery_codes_hash)
                    hashed_codes.pop(i)
                    user.recovery_codes_hash = hashed_codes if hashed_codes else None
                    db.session.commit()
                    authenticated = True
                    break
        if not authenticated:
            return render_template("connexion.html", recovery_code_mode=True, error="Code de récupération invalide ou déjà utilisé"), 401
    else:
        if not check_password_hash(user.password_hash, password):
            return render_template("connexion.html", error="Identifiants incorrects"), 401
        authenticated = True

    if authenticated:
        if user.totp_enabled:
            session["pending_2fa_user_id"] = user.id
            session.modified = True
            return redirect(url_for("auth.connexion_2fa_page"))

        session.clear()
        session.pop("_csrf_token", None)
        session["user_id"] = user.id
        session["session_version"] = user.session_version
        session["_auth_time"] = datetime.datetime.now().isoformat()
        session.modified = True
        return redirect(url_for("index.home"))


@bp.route("/inscription")
def inscription_page():
    return render_template(
        "inscription.html",
        title="A.N.A.N.A.S | Inscription",
        meta_description="Créer un compte A.N.A.N.A.S",
    )


@bp.route("/inscription", methods=["POST"])
@limiter.limit("30 per hour")
def inscription_post():
    prenom = sanitize_html(request.form.get("prenom", "").strip())
    nom = sanitize_html(request.form.get("nom", "").strip())
    password = request.form.get("password", "")

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


@bp.route("/connexion/2fa")
def connexion_2fa_page():
    pending_id = session.get("pending_2fa_user_id")
    if not pending_id:
        return redirect(url_for("auth.connexion_page"))

    user = db.session.get(User, pending_id)
    if not user or not user.totp_enabled:
        session.pop("pending_2fa_user_id", None)
        return redirect(url_for("auth.connexion_page"))

    return render_template(
        "connexion_2fa.html",
        title="A.N.A.N.A.S | Double authentification",
        meta_description="Vérification à deux facteurs",
    )


@bp.route("/connexion/2fa", methods=["POST"])
@limiter.limit("100 per hour")
def connexion_2fa_post():
    pending_id = session.get("pending_2fa_user_id")
    if not pending_id:
        return redirect(url_for("auth.connexion_page"))

    import pyotp

    user = db.session.get(User, pending_id)
    if not user or not user.totp_enabled or not user.totp_secret:
        session.pop("pending_2fa_user_id", None)
        return redirect(url_for("auth.connexion_page"))

    code = request.form.get("code", "").strip()
    if not code:
        return render_template("connexion_2fa.html", error="Code requis"), 400

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        return render_template("connexion_2fa.html", error="Code invalide. Vérifiez l'heure de votre appareil."), 401

    session.clear()
    session.pop("_csrf_token", None)
    session["user_id"] = user.id
    session["session_version"] = user.session_version
    session["_auth_time"] = datetime.datetime.now().isoformat()
    session.modified = True
    return redirect(url_for("index.home"))
