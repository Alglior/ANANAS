import re
import string

from flask import Blueprint, request, render_template, jsonify
from app import db
from src.shared import login_required, get_current_user, ITEMS_PER_PAGE, _paginate

ALLOWED_SLUG_CHARS = set(string.ascii_lowercase + string.digits + "-")
ALLOWED_MEMBER_ROLES = {"member", "moderator", "editor", "admin", "owner"}

bp = Blueprint("organizations", __name__)


def sanitize_slug(name):
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    if len(slug) > 80:
        slug = slug[:80]
    return slug or "org"


def _get_org(slug):
    from models import Organization
    return Organization.query.filter_by(slug=slug).first_or_404()


def _get_member(user_id, org):
    from models import OrganizationMember
    return OrganizationMember.query.filter_by(
        user_id=user_id, organization_id=org.id
    ).first()


def _require_permission(slug, permission):
    """Résout org + membre courant et vérifie la permission. Renvoie (org, member) ou une réponse d'erreur."""
    current_user = get_current_user()
    org = _get_org(slug)
    member = _get_member(current_user.id, org)
    if not member or not member.has_permission(permission):
        return None, None, jsonify({"error": "Non autorisé"}), 403
    return org, member, None, None


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
    from models import OrganizationMember

    current_user = get_current_user()
    org = _get_org(slug)

    existing = _get_member(current_user.id, org)
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
    current_user = get_current_user()
    org = _get_org(slug)

    member = _get_member(current_user.id, org)
    if member and member.role != "owner":
        db.session.delete(member)
        db.session.commit()

    return jsonify({"status": "left"})


@bp.route("/api/organizations/<slug>/members/<int:user_id>/role", methods=["POST"])
@login_required
def update_member_role(slug, user_id):
    from models import OrganizationMember

    org, member, error, code = _require_permission(slug, "manage_roles")
    if error:
        return error, code

    data = request.get_json(silent=True) or {}
    target_member = OrganizationMember.query.filter_by(
        user_id=user_id, organization_id=org.id
    ).first_or_404()

    if target_member.role == "owner":
        return jsonify({"error": "Impossible de modifier le rôle du propriétaire"}), 403

    custom_role_id = data.get("custom_role_id")
    if custom_role_id is not None:
        from models import OrganizationRole
        custom_role = OrganizationRole.query.filter_by(
            id=custom_role_id, organization_id=org.id
        ).first()
        if not custom_role:
            return jsonify({"error": "Rôle personnalisé introuvable"}), 404
        target_member.role = "member"
        target_member.custom_role_id = custom_role.id
    else:
        role = data.get("role", "member")
        if role not in ALLOWED_MEMBER_ROLES:
            return jsonify({"error": "Rôle invalide"}), 400
        target_member.role = role
        target_member.custom_role_id = None
    db.session.commit()

    return jsonify({"status": "updated", "role": target_member.role})


@bp.route("/api/organizations/<slug>/members/<int:user_id>", methods=["DELETE"])
@login_required
def remove_member(slug, user_id):
    from models import OrganizationMember

    org, member, error, code = _require_permission(slug, "remove_members")
    if error:
        return error, code

    target_member = OrganizationMember.query.filter_by(
        user_id=user_id, organization_id=org.id
    ).first_or_404()

    if target_member.role == "owner":
        return jsonify({"error": "Impossible de retirer le propriétaire"}), 403
    if target_member.role in ("admin",) and not member.has_permission("manage_roles"):
        return jsonify({"error": "Non autorisé"}), 403

    db.session.delete(target_member)
    db.session.commit()

    return jsonify({"status": "removed"})


@bp.route("/api/organizations/<slug>/invite", methods=["POST"])
@login_required
def invite_member(slug):
    from models import OrganizationMember, User

    org, member, error, code = _require_permission(slug, "invite_members")
    if error:
        return error, code

    data = request.get_json(silent=True) or {}
    pseudo = data.get("pseudo", "").strip().lower()
    if not pseudo:
        return jsonify({"error": "Pseudo requis"}), 400

    invited_user = User.query.filter_by(pseudo=pseudo).first()
    if not invited_user:
        return jsonify({"error": "Aucun utilisateur trouvé avec ce pseudo"}), 404

    existing = OrganizationMember.query.filter_by(
        user_id=invited_user.id, organization_id=org.id
    ).first()
    if existing:
        return jsonify({"error": "Cet utilisateur est déjà membre"}), 409

    new_member = OrganizationMember(
        user_id=invited_user.id,
        organization_id=org.id,
        role="member",
    )
    db.session.add(new_member)
    db.session.commit()

    return jsonify({"status": "invited", "name": f"{invited_user.prenom} {invited_user.nom}"})


@bp.route("/api/organizations/<slug>/roles", methods=["GET"])
@login_required
def list_roles(slug):
    from models import OrganizationRole

    org, member, error, code = _require_permission(slug, "manage_roles")
    if error:
        return error, code

    roles = OrganizationRole.query.filter_by(organization_id=org.id).all()
    return jsonify([
        {"id": r.id, "name": r.name, "permissions": r.permissions or []}
        for r in roles
    ])


@bp.route("/api/organizations/<slug>/roles", methods=["POST"])
@login_required
def create_role(slug):
    from models import OrganizationRole

    org, member, error, code = _require_permission(slug, "manage_roles")
    if error:
        return error, code

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name or len(name) < 2 or len(name) > 50:
        return jsonify({"error": "Le nom du rôle doit contenir entre 2 et 50 caractères"}), 400

    existing = OrganizationRole.query.filter_by(
        organization_id=org.id, name=name
    ).first()
    if existing:
        return jsonify({"error": "Un rôle avec ce nom existe déjà"}), 409

    permissions = data.get("permissions", [])
    if not isinstance(permissions, list):
        permissions = []
    valid_perms = [p[0] for p in OrganizationMember.ALL_PERMISSIONS]
    permissions = [p for p in permissions if p in valid_perms]

    role = OrganizationRole(
        organization_id=org.id,
        name=name,
        permissions=permissions,
    )
    db.session.add(role)
    db.session.commit()

    return jsonify({"id": role.id, "name": role.name, "permissions": permissions})


@bp.route("/api/organizations/<slug>/roles/<int:role_id>", methods=["PUT"])
@login_required
def update_role(slug, role_id):
    from models import OrganizationRole

    org, member, error, code = _require_permission(slug, "manage_roles")
    if error:
        return error, code

    role = OrganizationRole.query.filter_by(
        id=role_id, organization_id=org.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if name and len(name) >= 2:
        role.name = name

    permissions = data.get("permissions")
    if isinstance(permissions, list):
        valid_perms = [p[0] for p in OrganizationMember.ALL_PERMISSIONS]
        role.permissions = [p for p in permissions if p in valid_perms]

    db.session.commit()
    return jsonify({"id": role.id, "name": role.name, "permissions": role.permissions})


@bp.route("/api/organizations/<slug>/roles/<int:role_id>", methods=["DELETE"])
@login_required
def delete_role(slug, role_id):
    from models import OrganizationRole

    org, member, error, code = _require_permission(slug, "manage_roles")
    if error:
        return error, code

    role = OrganizationRole.query.filter_by(
        id=role_id, organization_id=org.id
    ).first_or_404()

    OrganizationMember.query.filter_by(custom_role_id=role.id).update(
        {"custom_role_id": None}
    )
    db.session.delete(role)
    db.session.commit()
    return jsonify({"status": "deleted"})


@bp.route("/organizations")
@bp.route("/organizations/<int:page>")
def organization_list_view(page=1):
    from models import Organization

    if "page" in request.args:
        page = request.args.get("page", 1, type=int)
    query = Organization.query.filter_by(is_active=True).order_by(
        Organization.created_at.desc()
    )
    orgs, page, total, total_pages, page_numbers = _paginate(query, page, per_page=ITEMS_PER_PAGE)

    return render_template(
        "organization_list.html",
        title="Toutes les organisations — A.N.A.N.A.S",
        meta_description="Parcourez toutes les organisations de la plateforme.",
        organizations=orgs,
        page=page,
        total_pages=total_pages,
        page_numbers=page_numbers,
    )


@bp.route("/organizations/<slug>/items")
def organization_items_view(slug):
    from models import Organization, Item

    org = Organization.query.filter_by(slug=slug).first_or_404()
    filter_verified = request.args.get("verified") == "1"
    items = (
        Item.query.filter_by(organization_id=org.id)
    )
    if filter_verified:
        items = items.filter_by(verification_status="verified")
    items = items.limit(ITEMS_PER_PAGE).all()
    return render_template(
        "organization_detail.html",
        title=f"{org.name} — A.N.A.N.A.S | Données",
        meta_description=org.description or org.name,
        org=org,
        items=[i.to_dict() for i in items],
    )


@bp.route("/organizations/<slug>")
def organization_detail_view(slug):
    from models import Organization, Item

    org = Organization.query.filter_by(slug=slug).first_or_404()
    items = (
        Item.query.filter_by(organization_id=org.id)
        .limit(ITEMS_PER_PAGE)
        .all()
    )
    return render_template(
        "organization_detail.html",
        title=f"{org.name} — A.N.A.N.A.S",
        meta_description=org.description or org.name,
        org=org,
        items=[i.to_dict() for i in items],
    )


@bp.route("/api/organizations/<slug>", methods=["DELETE"])
@login_required
def delete_organization(slug):
    org, member, error, code = _require_permission(slug, "delete_org")
    if error:
        return jsonify({"error": "Vous n'avez pas la permission de supprimer l'organisation"}), 403

    db.session.delete(org)
    db.session.commit()
    return jsonify({"status": "deleted"})
