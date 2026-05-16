import re
import string

from flask import Blueprint, request, render_template, jsonify
from app import db
from src.shared import login_required, get_current_user, ITEMS_PER_PAGE

ALLOWED_SLUG_CHARS = set(string.ascii_lowercase + string.digits + "-")

bp = Blueprint("organizations", __name__)


def sanitize_slug(name):
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    if len(slug) > 80:
        slug = slug[:80]
    return slug or "org"


@bp.route("/api/organizations", methods=["POST"])
@login_required
def create_organization():
    from models import Organization, OrganizationMember

    current_user = get_current_user()
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()

    if not name or len(name) < 2 or len(name) > 100:
        return jsonify({"error": "Le nom doit contenir entre 2 et 100 caractères"}), 400

    org = Organization(
        name=name,
        slug=sanitize_slug(name),
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


@bp.route("/api/organizations/<slug>/join", methods=["POST"])
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


@bp.route("/api/organizations/<slug>/leave", methods=["POST"])
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


@bp.route("/api/organizations/<slug>/members/<int:user_id>/role", methods=["POST"])
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


@bp.route("/organizations/<slug>/items")
def organization_items_view(slug):
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
