import os
import re
from functools import wraps
from secrets import token_hex

from flask import url_for, redirect, session


SECRET_FILE = ".secret"
ITEMS_PER_PAGE = 30

CATALOGUE_TYPES = ("donnees", "cartes", "applications")
ITEM_TYPE_MAP = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}
ALLOWED_ITEM_TYPES = set(ITEM_TYPE_MAP.values())
ITEM_TYPE_LABELS = {"geodonnee": "Géodonnée", "carte": "Carte", "application": "Application"}


def get_items_per_page():
    try:
        from src.admin.settings import get_setting
        return int(get_setting("items_per_page", "30"))
    except Exception:
        return 30


def _paginate(query, page=1, per_page=None):
    """Applique une pagination SQL à une query et renvoie (items, page, total, total_pages, page_numbers)."""
    if per_page is None:
        per_page = get_items_per_page()
    total = query.count()
    total_pages = max((total + per_page - 1) // per_page, 1) if total else 1
    page = max(1, min(page or 1, total_pages))
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return items, page, total, total_pages, _build_page_numbers(page, total_pages)


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


def _get_db():
    from app import db
    return db


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.connexion_page"))
        from models import User

        db = _get_db()
        current_user = db.session.get(User, session["user_id"])
        if current_user and (current_user.banned or not current_user.is_active):
            session.clear()
            return redirect(url_for("auth.connexion_page", error="banned"))
        if current_user and session.get("session_version", -1) != current_user.session_version:
            session.clear()
            return redirect(url_for("auth.connexion_page", error="session_expired"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    from models import User

    if "user_id" not in session:
        return None
    db = _get_db()
    user = db.session.get(User, session["user_id"])
    if user and session.get("session_version", -1) != user.session_version:
        session.clear()
        return None
    return user


def _build_page_numbers(current, total):
    if total <= 7:
        return list(range(1, total + 1))

    pages = []
    if current <= 4:
        pages.extend([1, 2, 3, 4])
        pages.append("...")
        pages.append(total)
    elif current > (total - 5):
        pages.append(1)
        pages.append("...")
        pages.extend(range(total - 3, total + 1))
    else:
        pages.append(1)
        pages.append("...")
        pages.extend(range(current - 1, current + 2))
        pages.append("...")
        pages.append(total)
    return pages


def user_owns_item_or_admin(current_user, item):
    if not current_user or not item:
        return False
    from models import OrganizationMember

    if getattr(current_user, "is_admin", False):
        return True
    if getattr(item, "owner_user_id", None) == current_user.id:
        return True
    if getattr(item, "organization_id", None):
        membership = OrganizationMember.query.filter_by(
            user_id=current_user.id, organization_id=item.organization_id
        ).first()
        if membership and membership.is_active:
            return True
    return False


def _generate_secret_key():
    return token_hex(32)


class Config:
    """Configuration de l'application."""

    def __init__(self):
        self.SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")

        if not self.SECRET_KEY and os.path.isfile(SECRET_FILE):
            with open(SECRET_FILE, "r") as f:
                for line in f:
                    if line.startswith("FLASK_SECRET_KEY="):
                        _, _, key = line.partition("=")
                        self.SECRET_KEY = key.strip()
                        break

    def validate(self):
        is_production = os.environ.get("FLASK_ENV", "development") == "production"

        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            if is_production:
                raise ValueError(
                    "CRITICAL: No secret key configured! Set FLASK_SECRET_KEY in your environment or provide a valid .secret file."
                )
            else:
                self.SECRET_KEY = _generate_secret_key()
