import os
import datetime as dt
import json
from functools import wraps

SECRET_FILE = ".secret"

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    session,
    jsonify,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

ITEMS_PER_PAGE = 30


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("connexion_page"))
        from models import User

        current_user = db.session.get(User, session["user_id"])
        if current_user and (current_user.banned or not current_user.is_active):
            session.clear()
            return redirect(url_for("connexion_page", error="banned"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    from models import User

    if "user_id" not in session:
        return None
    return db.session.get(User, session["user_id"])


def get_catalogue_page(total_page=1, per_page=ITEMS_PER_PAGE, catalogue="donnees", filter_verified=False, org_slug=None):
    from models import Item, Organization

    type_map = {
        "donnees": "geodonnee",
        "cartes": "carte",
        "applications": "application"
    }
    item_type = type_map[catalogue]

    query = Item.query.filter_by(type=item_type)
    if org_slug:
        org = Organization.query.filter_by(slug=org_slug).first()
        if org:
            query = query.filter_by(organization_id=org.id)
    if filter_verified:
        query = query.filter_by(verification_status="verified")
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    if total_page > total_pages or total_page < 1:
        return None

    items = query.offset((total_page - 1) * per_page).limit(per_page).all()

    result_items = [item.to_dict() for item in items]
    page_numbers = _build_page_numbers(total_page, total_pages)

    return {
        "items": result_items,
        "page": total_page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "page_numbers": page_numbers,
    }


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


class Config:
    """Configuration de l'application."""

    def __init__(self):
        self.SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")

        # Si aucune clé n'est configurée, lecture du fichier SECRET_FILE
        if not self.SECRET_KEY and os.path.isfile(SECRET_FILE):
            with open(SECRET_FILE, "r") as f:
                for line in f:
                    if line.startswith("FLASK_SECRET_KEY="):
                        _, _, key = line.partition("=")
                        self.SECRET_KEY = key.strip()
                        break

    def validate(self):
        """Valider la clé et garantir sa robustesse."""
        is_production = os.environ.get("FLASK_ENV", "development") == "production"

        # Si aucune clé n'est trouvée ou si elle est trop courte (< 32 chars)
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            if is_production:
                raise ValueError(
                    "CRITICAL: No secret key configured! Set FLASK_SECRET_KEY in your environment or provide a valid .secret file."
                )
            else:
                # En développement, générer une nouvelle clé
                self.SECRET_KEY = _generate_secret_key()


def create_app(app_name="ANANAS"):
    """Implémentation du motif 'usine' (factory) pour l'application."""
    from models import Item, Organization

    app = Flask(__name__, template_folder="templates")

    # Chargement de la configuration
    config = Config()
    config.validate()
    app.config.update(config.__dict__)

    # Activation globale de la protection CSRF (nécessite une clé secrète)
    csrf = CSRFProtect(app)

    # ────────────────────────────────────────────
    #  Database setup
    # ────────────────────────────────────────────
    db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri:
        pg_user = os.environ.get("POSTGRES_USER", "ananas_user")
        pg_pass = os.environ.get("POSTGRES_PASSWORD", "password")
        pg_host = os.environ.get("POSTGRES_HOST", "postgres")
        pg_db = os.environ.get("POSTGRES_DB", "ananas")
        db_uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db=db)

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    # ────────────────────────────────────────────
    #  Security Headers & Cookie Settings
    # ────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com https://unpkg.com; "
            "script-src 'self' https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self' https://unpkg.com https://*.tile.openstreetmap.org"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.context_processor
    def inject_user():
        cu = get_current_user()
        return {"current_user": cu}

    # Configuration des cookies sécurisés
    # Déterminer si on est en production
    is_production = os.environ.get("FLASK_ENV", "development") == "production"
    
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Empêche les scripts JavaScript de lire le cookie de session
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Protection contre les attaques CSRF par cookie
    app.config["SESSION_COOKIE_SECURE"] = is_production  # En production seulement, force HTTPS pour les cookies
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # Les sessions expireront après 1 heure (clé correcte Flask)

    # Définition des routes
    routes = [
        {
            "rule": "/",
            "template": "index.html",
            "title": "A.N.A.N.A.S. | Accueil",
            "meta": "Portail géoservices basé sur des liens magnet et torrents.",
        },
 
        {
            "rule": "/contact",
            "template": "contact.html",
            "title": "A.N.A.N.A.S. | Contact",
            "meta": "Contactez-nous pour toute question ou suggestion.",
        },
    ]

    # Enregistrement dynamique des routes
    for route_cfg in routes:
        rule = route_cfg["rule"]
        endpoint = rule.lstrip("/") or "home"
        _register_view(app, rule, endpoint, route_cfg)

    # Catalogue routes (donnees, cartes, applications)
    _CATALOGUE_META = {
        "donnees": {
            "title_prefix": "Catalogue des géodonnées",
            "meta": "Parcourez le catalogue complet des géodonnées A.N.A.N.A.S.",
        },
        "cartes": {
            "title_prefix": "Catalogue des cartes",
            "meta": "Explorez la collection de cartes et produits cartographiques A.N.A.N.A.S.",
        },
        "applications": {
            "title_prefix": "Catalogue d'applications",
            "meta": "Découvrez les applications et services web géospatiaux A.N.A.N.A.S.",
        },
    }

    type_map = {"donnees": "geodonnee", "cartes": "carte", "applications": "application"}

    def catalogue_view(catalogue="donnees", page=1):
        if catalogue not in type_map:
            return redirect(url_for("catalogue"))

        try:
            page = int(request.args.get("page", page))
        except (ValueError, TypeError):
            page = 1

        if page < 1:
            return redirect(url_for("catalogue", catalogue=catalogue, page=1))

        filter_verified = request.args.get("verified") == "1"
        org_slug = request.args.get("org")
        format_param = request.args.get("format", "")

        meta = _CATALOGUE_META[catalogue]
        data = get_catalogue_page(page, catalogue=catalogue, filter_verified=filter_verified, org_slug=org_slug)
        if data is None:
            return redirect(url_for("catalogue", catalogue=catalogue, page=1))
        if format_param == "json":
            from flask import jsonify
            return jsonify(data)
        return render_template(
            "catalogue.html",
            title=f"A.N.A.N.A.S. | {meta['title_prefix']} — Page {page}",
            meta_description=meta["meta"],
            catalogue_type=catalogue,
            filter_verified=filter_verified,
            org_slug=org_slug,
            **data,
        )

    app.add_url_rule("/catalogue", endpoint="catalogue", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/donnees", endpoint="catalogue_donnees", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/cartes", endpoint="catalogue_cartes", view_func=lambda catalogue="cartes", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/applications", endpoint="catalogue_apps", view_func=lambda catalogue="applications", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/<int:page>", endpoint="catalogue_page", view_func=lambda page=1: catalogue_view(page=page))
    app.add_url_rule("/catalogue/donnees/<int:page>", endpoint="catalogue_donnees_page", view_func=lambda catalogue="donnees", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/cartes/<int:page>", endpoint="catalogue_cartes_page", view_func=lambda catalogue="cartes", page=1: catalogue_view(catalogue=catalogue, page=page))
    app.add_url_rule("/catalogue/applications/<int:page>", endpoint="catalogue_apps_page", view_func=lambda catalogue="applications", page=1: catalogue_view(catalogue=catalogue, page=page))

    # ────────────────────────────────────────────
    #  Favicon (silently ignore requests)
    # ────────────────────────────────────────────
    @app.route("/favicon.ico")
    def favicon_route():
        return "", 204

    # Item detail route
    def item_detail_view(item_id):
        item = Item.query.get_or_404(item_id)
        related_items = Item.query.filter(
            Item.format_type == item.format_type,
            Item.id != item_id,
            Item.is_published == True
        ).limit(3).all()

        img_gallery = [g for g in item.gallery_items if g.media_type == "image"]

        current_user = get_current_user()

        return render_template(
            "item_detail.html",
            title=f"A.N.A.N.A.S. | {item.title}",
            meta_description=item.description[:160],
            item=item.to_dict(),
            related_items=[ri.to_dict() for ri in related_items],
            image_gallery=img_gallery,
            current_user=current_user,
        )

    app.add_url_rule("/catalogue/item/<int:item_id>", endpoint="item_detail", view_func=item_detail_view)

    # Standalone gallery page
    def item_gallery_view(item_id):
        item = Item.query.get_or_404(item_id)
        return render_template(
            "gallery.html",
            title=f"Galerie — {item.title}",
            meta_description="Galerie de " + item.title,
            item=item.to_dict(),
        )

    app.add_url_rule("/catalogue/item/<int:item_id>/gallery", endpoint="item_gallery", view_func=item_gallery_view)

  # ────────────────────────────────────────────
    #  Auth GET routes (connexion / inscription pages)
    # ────────────────────────────────────────────
    @app.route("/connexion")
    def connexion_page():
        return render_template(
            "connexion.html",
            title="A.N.A.N.A.S. | Connexion",
            meta_description="Connectez-vous à votre compte A.N.A.N.A.S.",
        )

    @app.route("/inscription")
    def inscription_page():
        return render_template(
            "inscription.html",
            title="A.N.A.N.A.S. | Inscription",
            meta_description="Créer un compte A.N.A.N.A.S.",
        )

    # ────────────────────────────────────────────
    #  Auth POST handlers (connexion / inscription)
    # ────────────────────────────────────────────
    @app.route("/connexion", methods=["POST"])
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

    @app.route("/inscription", methods=["POST"])
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
            password_hash=generate_password_hash(password),
            is_active=True,
            banned=False,
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("connexion_page"))

    # ────────────────────────────────────────────
    #  Rating endpoint
    # ────────────────────────────────────────────
    @app.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
    def rate_item(item_id):
        from models import Item, Rating

        item = Item.query.get_or_404(item_id)
        rating_value = request.form.get("rating")

        if not rating_value or not rating_value.isdigit():
            return redirect(url_for("item_detail", item_id=item_id))

        rating = int(rating_value)
        existing = Rating.query.filter_by(item_id=item_id).first()
        if existing:
            existing.rating = rating
        else:
            new_rating = Rating(item_id=item_id, rating=rating)
            db.session.add(new_rating)

        # Update average on item
        ratings = Rating.query.filter_by(item_id=item_id).all()
        avg = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
        item.format_type = getattr(item, "_rating_avg", None) or 0  # store avg inline

        db.session.commit()
        return redirect(url_for("item_detail", item_id=item_id))

    # ────────────────────────────────────────────
    #  Comment endpoint
    # ────────────────────────────────────────────
    @app.route("/catalogue/item/<int:item_id>/comment", methods=["POST"])
    def add_comment(item_id):
        from models import Item, Comment

        current_user = get_current_user()
        item = Item.query.get_or_404(item_id)
        author_name = request.form.get("author", "").strip() or (f"{current_user.prenom} {current_user.nom}" if current_user else "")
        content = request.form.get("text", "").strip()

        if not content:
            return redirect(url_for("item_detail", item_id=item_id))

        comment = Comment(
            item_id=item_id,
            author_name=author_name,
            content=content,
        )
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for("item_detail", item_id=item_id))

    # ────────────────────────────────────────────
    #  Verification endpoint (admin/reviewer only)
    # ────────────────────────────────────────────
    @app.route("/api/items/<int:item_id>/verify", methods=["POST"])
    @login_required
    def verify_item(item_id):
        from models import Item

        current_user = get_current_user()
        data = request.get_json(silent=True) or {}
        status = data.get("status", "")

        if status not in ("verified", "unofficial", "rejected"):
            return jsonify({"error": "Statut invalide"}), 400

        item = Item.query.get_or_404(item_id)

        item.verification_status = status
        item.verifier_user_id = current_user.id
        item.verified_at = dt.datetime.now if status == "verified" else None
        item.verification_notes = data.get("notes")

        db.session.commit()

        return jsonify({
            "status": "updated",
            "item_id": item_id,
            "new_status": status,
        })

    # ────────────────────────────────────────────
    #  Organization endpoints
    # ────────────────────────────────────────────
    @app.route("/api/organizations", methods=["POST"])
    @login_required
    def create_organization():
        from models import Organization, OrganizationMember

        current_user = get_current_user()
        data = request.get_json(silent=True) or {}
        name = data.get("name", "")

        if not name:
            return jsonify({"error": "Le nom est requis"}), 400

        org = Organization(
            name=name,
            slug=name.lower().replace(" ", "-"),
            description=data.get("description", ""),
            created_by=current_user.id,
            is_active=True,
        )
        db.session.add(org)
        db.session.flush()

        member = OrganizationMember(
            user_id=current_user.id,
            organization_id=org.id,
            role="owner",
        )
        db.session.add(member)
        db.session.commit()

        return jsonify({"id": org.id, "slug": org.slug})

    @app.route("/api/organizations/<slug>/join", methods=["POST"])
    @login_required
    def join_organization(slug):
        from models import Organization, OrganizationMember

        current_user = get_current_user()
        org = Organization.query.filter_by(slug=slug).first_or_404()

        existing = OrganizationMember.query.filter_by(
            user_id=current_user.id, organization_id=org.id
        ).first()
        if existing:
            return jsonify({"error": "Déjà membre"}), 409

        member = OrganizationMember(
            user_id=current_user.id,
            organization_id=org.id,
            role="member",
        )
        db.session.add(member)
        db.session.commit()

        return jsonify({"status": "joined"})

    @app.route("/api/organizations/<slug>/leave", methods=["POST"])
    @login_required
    def leave_organization(slug):
        from models import Organization, OrganizationMember

        current_user = get_current_user()
        org = Organization.query.filter_by(slug=slug).first_or_404()

        member = OrganizationMember.query.filter_by(
            user_id=current_user.id, organization_id=org.id
        ).first()
        if member and member.role != "owner":
            db.session.delete(member)
            db.session.commit()

        return jsonify({"status": "left"})

    @app.route("/api/organizations/<slug>/members/<int:user_id>/role", methods=["POST"])
    @login_required
    def update_member_role(slug, user_id):
        from models import Organization, OrganizationMember

        current_user = get_current_user()
        org = Organization.query.filter_by(slug=slug).first_or_404()

        member = OrganizationMember.query.filter_by(
            user_id=current_user.id, organization_id=org.id
        ).first()
        if not member or member.role not in ("admin", "owner"):
            return jsonify({"error": "Non autorisé"}), 403

        data = request.get_json(silent=True) or {}
        target_member = OrganizationMember.query.filter_by(
            user_id=user_id, organization_id=org.id
        ).first_or_404()

        target_member.role = data.get("role", "member")
        db.session.commit()

        return jsonify({"status": "updated", "role": data.get("role")})

    # ────────────────────────────────────────────
    #  Organization detail page
    # ────────────────────────────────────────────
    def organization_detail_view(slug):
        from models import Organization, Item

        org = Organization.query.filter_by(slug=slug).first_or_404()
        items = (
            Item.query.filter_by(organization_id=org.id, is_published=True)
            .limit(ITEMS_PER_PAGE)
            .all()
        )
        return render_template(
            "organization_detail.html",
            title=f"{org.name} — A.N.A.N.A.S.",
            meta_description=org.description or org.name,
            org=org,
            items=[i.to_dict() for i in items],
        )

    @app.route("/organizations/<slug>/items")
    def organization_items(slug):
        from models import Organization, Item

        org = Organization.query.filter_by(slug=slug).first_or_404()
        filter_verified = request.args.get("verified") == "1"
        items = (
            Item.query.filter_by(organization_id=org.id, is_published=True)
        )
        if filter_verified:
            items = items.filter_by(verification_status="verified")
        items = items.limit(ITEMS_PER_PAGE).all()
        return render_template(
            "organization_detail.html",
            title=f"{org.name} — A.N.A.N.A.S. | Données",
            meta_description=org.description or org.name,
            org=org,
            items=[i.to_dict() for i in items],
        )

    app.add_url_rule(
        "/organizations/<slug>", endpoint="organization_detail", view_func=organization_detail_view
    )

    # ────────────────────────────────────────────
    #  Ban / Unban endpoints
    # ────────────────────────────────────────────
    @app.route("/api/users/<int:user_id>/ban", methods=["POST"])
    @login_required
    def ban_user(user_id):
        from models import User

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        target_user = User.query.get_or_404(user_id)
        data = request.get_json(silent=True) or {}
        action = data.get("action", "")

        if action not in ("ban", "unban"):
            return jsonify({"error": "Action invalide"}), 400

        target_user.banned = (action == "ban")
        db.session.commit()

        return jsonify({
            "status": "updated",
            "user_id": user_id,
            "action": action,
        })

    @app.route("/api/users/banned", methods=["GET"])
    @login_required
    def list_banned_users():
        from models import User

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        banned = User.query.filter_by(banned=True).all()
        return jsonify([
            {
                "id": u.id,
                "prenom": u.prenom,
                "nom": u.nom,
                "email": u.email,
                "created_at": u.created_at.isoformat() if hasattr(u, "created_at") else None,
                "banned": u.banned,
            }
            for u in banned
        ])

    # ────────────────────────────────────────────
    #  Report system endpoints
    # ────────────────────────────────────────────
    @app.route("/api/reports", methods=["POST"])
    @login_required
    def create_report():
        from models import User, Item, Report

        current_user = get_current_user()
        data = request.get_json(silent=True) or {}

        target_type = data.get("target_type")
        target_id = data.get("target_id")
        reason = data.get("reason")
        description = data.get("description", "")

        if not target_type or not target_id or not reason:
            return jsonify({"error": "target_type, target_id et reason sont requis"}), 400

        if reason not in ("spam", "fake_data", "other"):
            return jsonify({"error": "Raison invalide"}), 400

        report = Report(
            reporter_id=current_user.id,
            report_type=f"item_{target_type}" if target_type != "user" else "user",
            reason=reason,
            description=description,
            status="pending",
        )

        if target_type == "user":
            reported_user = db.session.get(User, target_id)
            if not reported_user:
                return jsonify({"error": "Utilisateur introuvable"}), 404
            if reported_user.id == current_user.id:
                return jsonify({"error": "Impossible de se signaler soi-même"}), 400
            report.reported_user_id = reported_user.id
        else:
            item_type_map = {"geodonnee": "geodonnee", "carte": "carte", "application": "application"}
            if target_type not in item_type_map:
                return jsonify({"error": "Type de contenu invalide"}), 400
            item = Item.query.filter_by(id=target_id, type=item_type_map[target_type]).first()
            if not item:
                return jsonify({"error": "Contenu introuvable"}), 404
            report.target_item_id = target_id

        db.session.add(report)
        db.session.commit()

        return jsonify({"status": "created", "report_id": report.id})

    @app.route("/api/admin/reports", methods=["GET"])
    @login_required
    def list_reports():
        from models import Report

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        status_filter = request.args.get("status", "all")
        report_type = request.args.get("type", "all")

        query = Report.query
        if status_filter != "all":
            query = query.filter_by(status=status_filter)
        if report_type != "all":
            query = query.filter_by(report_type=report_type)

        reports = query.order_by(Report.created_at.desc()).all()
        return jsonify([
            {
                "id": r.id,
                "reporter": {"id": r.reporter.id, "name": str(r.reporter)} if r.reporter else None,
                "reported_user": {"id": r.reported_user.id, "name": str(r.reported_user)} if r.reported_user else None,
                "target_item_id": r.target_item_id,
                "report_type": r.report_type,
                "reason": r.reason,
                "description": r.description,
                "status": r.status,
                "reviewed_by": {"id": r.reviewed_by.id, "name": str(r.reviewed_by)} if r.reviewed_by else None,
                "reviewed_at": r.reviewed_at.isoformat() if hasattr(r, "reviewed_at") and r.reviewed_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ])

    @app.route("/api/admin/reports/<int:report_id>/resolve", methods=["POST"])
    @login_required
    def resolve_report(report_id):
        from models import Report

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        report = Report.query.get_or_404(report_id)
        data = request.get_json(silent=True) or {}
        new_status = data.get("status", "")

        if new_status not in ("resolved", "dismissed"):
            return jsonify({"error": "Statut invalide"}), 400

        report.status = new_status
        report.reviewed_by = current_user.id
        report.reviewed_at = dt.datetime.now()

        db.session.commit()

        return jsonify({"status": "updated", "report_id": report.id})

    # ────────────────────────────────────────────
    #  Admin pages
    # ────────────────────────────────────────────
    @app.route("/admin/users")
    @login_required
    def admin_users():
        from models import User

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        users = User.query.all()
        return render_template(
            "admin/users.html",
            title="Administration — Utilisateurs",
            meta_description="Liste des utilisateurs",
            users=users,
        )

    @app.route("/admin/reports")
    @login_required
    def admin_reports():
        from models import Report

        current_user = get_current_user()
        if not hasattr(current_user, "is_admin"):
            return jsonify({"error": "Non autorisé"}), 403

        status_filter = request.args.get("status", "all")
        report_type = request.args.get("type", "all")

        query = Report.query
        if status_filter != "all":
            query = query.filter_by(status=status_filter)
        if report_type != "all":
            query = query.filter_by(report_type=report_type)

        reports = query.order_by(Report.created_at.desc()).all()
        pending_count = Report.query.filter_by(status="pending").count()

        return render_template(
            "admin/reports.html",
            title="Administration — Signalements",
            meta_description="Liste des signalements",
            reports=reports,
            status=status_filter,
            pending_count=pending_count,
        )

    # ────────────────────────────────────────────
    #  Logout route
    # ────────────────────────────────────────────
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    return app


def _register_view(app: Flask, rule: str, endpoint: str, cfg: dict):
    """Enregistrer une fonction de vue avec un nom d'extrémité (endpoint) unique."""

    def view_func():
        return render_template(
            cfg["template"],
            title=cfg["title"],
            meta_description=cfg["meta"],
        )

    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)


# ────────────────────────────────────────────
#  Local dev runner
# ────────────────────────────────────────────
if __name__ == "__main__":
    # En production, la clé secrète est généralement configurée via des variables d'environnement.
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    app = create_app()
    app.run(debug=debug_mode)
