import datetime

from app import db
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from utils.security import sanitize_gallery_data, sanitize_value, validate_external_url, validate_magnet_link


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class Item(db.Model, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    format_type: Mapped[str | None]
    magnet_link: Mapped[str]
    image_path: Mapped[str] = mapped_column(default="/static/images/logo/ANANAS.png")
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    author_name: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    verification_status: Mapped[str] = mapped_column(default="unofficial")
    data_format_level: Mapped[str] = mapped_column(default="individual")
    pdf_magnet_link: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="published")
    deleted_at: Mapped[datetime.datetime | None]
    license_type: Mapped[str | None] = mapped_column(default=None)
    image_magnets_pending: Mapped[bool] = mapped_column(default=False)
    image_magnets_total: Mapped[int] = mapped_column(default=0)
    image_magnet_links: Mapped[list | None] = mapped_column(JSON, server_default="[]", nullable=True)
    metadata_json: Mapped[list | None] = mapped_column(JSON, server_default="[]", nullable=True)
    verifier_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime.datetime | None]
    verification_notes: Mapped[str | None]

    tags = relationship("ItemTag", back_populates="item", cascade="all, delete-orphan")
    gallery_items = relationship("ItemGallery", back_populates="item", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="item", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="item", cascade="all, delete-orphan")
    verifier = relationship("User", foreign_keys=[verifier_user_id])
    organization = relationship("Organization")

    CATALOGUE_MAP = {
        "geodonnee": "/catalogue/donnees",
        "carte": "/catalogue/cartes",
        "application": "/catalogue/applications",
    }

    def to_dict(self, include_details=False):
        result = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "description": self.description,
            "format_type": self.format_type,
            "format": self.format_type,
            "magnet": self.magnet_link if validate_magnet_link(self.magnet_link) else "",
            "magnet_link": self.magnet_link if validate_magnet_link(self.magnet_link) else "",
            "magnet_links": self.metadata_json if isinstance(self.metadata_json, list) else [],
            "image": self.image_path,
            "author": self.author_name,
            "organization_id": self.organization_id,
            "organization_name": self.organization.name if self.organization else None,
            "organization_slug": self.organization.slug if self.organization else None,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "tags": [t.tag for t in self.tags],
            "gallery": self._build_gallery_dict(),
            "pdf_doc": self.pdf_magnet_link if self.pdf_magnet_link and validate_magnet_link(self.pdf_magnet_link) else "",
            "pdf_magnet_link": self.pdf_magnet_link if self.pdf_magnet_link and validate_magnet_link(self.pdf_magnet_link) else "",
            "verification_status": self.verification_status,
            "is_official_verified": self.verification_status == "verified",
            "verifier_nom": f"{self.verifier.prenom} {self.verifier.nom}" if (self.verifier and getattr(self.verifier, "prenom", None)) else None,
            "verified_at": self.verified_at.strftime("%Y-%m-%d") if self.verified_at else None,
            "verification_notes": self.verification_notes,
            "catalogue_link": self.CATALOGUE_MAP.get(self.type, "/catalogue"),
            "report_type": self.type,
            "rating": self._get_rating_avg(),
            "review_count": len(self.ratings),
            "license_type": self.license_type,
            "data_format_level": self.data_format_level,
            "status": self.status,
            "download_levels": self._get_download_levels(),
            "image_magnets_pending": self.image_magnets_pending,
            "image_magnets_total": self.image_magnets_total,
            "image_magnets": self._get_image_magnets(),
            "visualization_links": [vl.to_dict() for vl in self.visualization_links],
        }
        if include_details:
            result["data_chunks"] = [c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=self.id).all()]
        return result

    def _get_rating_avg(self):
        ratings = [r.rating for r in self.ratings if r.rating is not None]
        if not ratings:
            return 0
        return sum(ratings) / len(ratings)

    def _get_download_levels(self):
        if self.data_format_level != "individual":
            return None
        return [
            {"name": c.name, "magnet": c.magnet_link}
            for c in DataChunk.query.filter_by(parent_item_id=self.id).all()
            if validate_magnet_link(c.magnet_link or "")
        ]

    def _build_gallery_dict(self):
        result = []
        for g in self.gallery_items:
            entry = {"type": g.media_type, "label": sanitize_value(g.label) if isinstance(g.label, str) else g.label}
            if g.src:
                entry["src"] = sanitize_value(g.src) if isinstance(g.src, str) else g.src
            if g.data_json:
                self._add_gallery_data(entry, g)
            result.append(entry)
        return result

    def _get_image_magnets(self):
        magnets = []
        for g in self.gallery_items:
            if g.media_type == "image" and isinstance(g.data_json, dict):
                magnet = g.data_json.get("magnet_link", "")
                if magnet:
                    magnets.append({"magnet_link": magnet, "label": g.label or ""})
        if not magnets and isinstance(self.image_magnet_links, list):
            magnets = list(self.image_magnet_links)
        return magnets

    @staticmethod
    def _add_gallery_data(entry, g):
        if isinstance(g.data_json, dict):
            rows = g.data_json.get("rows", [])
            metrics = g.data_json.get("metrics", [])
            if g.media_type == "csv" and rows:
                entry["data"] = sanitize_gallery_data(rows) if isinstance(rows, list) else []
            elif g.media_type == "dashboard" and metrics:
                entry["metrics"] = _sanitize_metrics(metrics) if isinstance(metrics, list) else []
            else:
                clean_dict = {}
                for k, v in g.data_json.items():
                    sk = sanitize_value(str(k))
                    clean_dict[sk] = sanitize_gallery_data(v) if isinstance(v, list) else (sanitize_value(v) if isinstance(v, str) else v)
                entry["data"] = clean_dict


def _sanitize_metrics(metrics):
    sanitized = []
    for m in metrics:
        if isinstance(m, dict):
            clean_m = {}
            for k, v in m.items():
                sk = sanitize_value(str(k))
                clean_m[sk] = sanitize_value(v) if isinstance(v, str) else v
            sanitized.append(clean_m)
        elif isinstance(m, (str, int, float)):
            sanitized.append(sanitize_value(m) if isinstance(m, str) else m)
    return sanitized


class ItemTag(db.Model):
    __tablename__ = "item_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    tag: Mapped[str]

    item = relationship("Item", back_populates="tags")


class ItemGallery(db.Model):
    __tablename__ = "item_gallery"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    media_type: Mapped[str]
    src: Mapped[str | None]
    data_json: Mapped[dict | None] = mapped_column(JSON, server_default="{}")
    label: Mapped[str | None]

    item = relationship("Item", back_populates="gallery_items")


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    prenom: Mapped[str]
    nom: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    avatar_path: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    muted_until: Mapped[datetime.datetime | None]
    warned: Mapped[bool] = mapped_column(default=False)
    warnings: Mapped[str | None]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    organizations = relationship("OrganizationMember", back_populates="user")


class Organization(db.Model, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    logo_url: Mapped[str | None]
    website_url: Mapped[str | None]
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)

    creator = relationship("User", foreign_keys=[created_by])
    organization_members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class OrganizationMember(db.Model):
    __tablename__ = "organization_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(default="member")
    custom_role_id: Mapped[int | None] = mapped_column(ForeignKey("organization_roles.id", ondelete="SET NULL"), default=None)
    joined_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)

    DEFAULT_ROLE_PERMISSIONS = {
        "member": [],
        "moderator": ["remove_members", "moderate_content"],
        "editor": ["manage_items"],
        "admin": ["invite_members", "remove_members", "edit_org", "manage_items", "moderate_content"],
        "owner": ["invite_members", "remove_members", "edit_org", "manage_items", "moderate_content", "manage_roles", "delete_org"],
    }

    ALL_PERMISSIONS = [
        ("invite_members", "Inviter des membres"),
        ("remove_members", "Retirer des membres"),
        ("edit_org", "Modifier l'organisation"),
        ("manage_items", "Gérer les données"),
        ("moderate_content", "Modérer le contenu"),
        ("manage_roles", "Gérer les rôles"),
        ("delete_org", "Supprimer l'organisation"),
    ]

    def get_permissions(self):
        if self.custom_role_id and self.custom_role:
            return self.custom_role.permissions or []
        return self.DEFAULT_ROLE_PERMISSIONS.get(self.role, [])

    def has_permission(self, permission):
        return permission in self.get_permissions()

    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization")
    custom_role = relationship("OrganizationRole", foreign_keys=[custom_role_id])


class OrganizationRole(db.Model, TimestampMixin):
    __tablename__ = "organization_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    name: Mapped[str]
    permissions: Mapped[dict | None] = mapped_column(JSON, server_default="[]")

    organization = relationship("Organization")


class Rating(db.Model):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[float]

    item = relationship("Item", back_populates="ratings")


class Comment(db.Model, TimestampMixin):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    author_name: Mapped[str | None]
    content: Mapped[str]

    item = relationship("Item", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side="Comment.id", back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")


class DataChunk(db.Model, TimestampMixin):
    __tablename__ = "data_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    name: Mapped[str]
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str | None]
    format_type: Mapped[str | None]
    magnet_link: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    data_url: Mapped[str | None]
    metadata_json: Mapped[dict | None] = mapped_column(JSON, server_default="{}")
    upload_status: Mapped[str] = mapped_column(default="uploaded")
    published_at: Mapped[datetime.datetime | None]

    def to_dict(self):
        meta = self.metadata_json or {}
        meta_json = _sanitize_metadata(meta) if isinstance(meta, dict) else {}
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "format_type": self.format_type,
            "magnet_link": self.magnet_link if validate_magnet_link(self.magnet_link or "") else None,
            "data_url": self.data_url if validate_external_url(self.data_url or "") else None,
            "metadata_json": meta_json,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
        }

    owner = relationship("User", back_populates="data_chunks")
    organization = relationship("Organization")


def _sanitize_metadata(meta):
    clean = {}
    for k, v in meta.items():
        ck = sanitize_value(str(k))
        if isinstance(v, list):
            cv = sanitize_gallery_data(v)
        elif isinstance(v, str):
            cv = sanitize_value(v)
        else:
            cv = v
        clean[ck] = cv
    return clean


class UserUpload(db.Model):
    __tablename__ = "user_uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("data_chunks.id"))
    file_name: Mapped[str]
    file_size_bytes: Mapped[int | None]
    mime_type: Mapped[str | None]
    original_format: Mapped[str | None]
    uploaded_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    processing_status: Mapped[str] = mapped_column(default="queued")
    error_message: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    published_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))

    owner = relationship("User", back_populates="user_uploads")
    organization = relationship("Organization")


class VisualizationLink(db.Model, TimestampMixin):
    __tablename__ = "visualization_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    name: Mapped[str]
    url: Mapped[str]
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    link_type: Mapped[str] = mapped_column(default="external")
    display_order: Mapped[int] = mapped_column(default=0)
    description: Mapped[str | None]
    thumbnail_url: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "link_type": self.link_type,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
        }

    item = relationship("Item", back_populates="visualization_links")


class Report(db.Model, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reported_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[str]
    target_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    reason: Mapped[str]
    description: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="pending")
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime.datetime | None]

    reporter = relationship("User", foreign_keys=[reporter_id], overlaps="made_reports,reports_by")
    reported_user = relationship("User", foreign_keys=[reported_user_id], overlaps="reported_reports,reports_made_against_me")
    target_item = relationship("Item", overlaps="reported_items,reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class AdminAudit(db.Model, TimestampMixin):
    __tablename__ = "admin_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str]
    target_type: Mapped[str | None]
    target_id: Mapped[int | None]
    details: Mapped[str | None] = mapped_column(JSON, server_default="{}")

    admin = relationship("User", foreign_keys=[admin_user_id])


class ContactMessage(db.Model, TimestampMixin):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    subject: Mapped[str]
    message: Mapped[str]
    is_read: Mapped[bool] = mapped_column(default=False)


class MirrorSite(db.Model, TimestampMixin):
    __tablename__ = "mirror_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    url: Mapped[str]
    description: Mapped[str]
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class FeaturedItem(db.Model, TimestampMixin):
    __tablename__ = "featured_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    item = relationship("Item")


class PredefinedTagCategory(db.Model, TimestampMixin):
    __tablename__ = "predefined_tag_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    display_order: Mapped[int] = mapped_column(default=0)

    tags = relationship("PredefinedTag", back_populates="category", cascade="all, delete-orphan", order_by="PredefinedTag.display_order")


class PredefinedTag(db.Model):
    __tablename__ = "predefined_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("predefined_tag_categories.id", ondelete="CASCADE"))
    name: Mapped[str]
    display_order: Mapped[int] = mapped_column(default=0)

    category = relationship("PredefinedTagCategory", back_populates="tags")


class GeoPackage(db.Model, TimestampMixin):
    __tablename__ = "geo_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    format_info: Mapped[str]
    link_url: Mapped[str]
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


# Back-references
User.data_chunks = relationship("DataChunk", back_populates="owner")
User.user_uploads = relationship("UserUpload", back_populates="owner")
User.comments = relationship("Comment", back_populates="user")
User.reported_reports = relationship(
    "Report",
    foreign_keys=[Report.reported_user_id],
    backref="reports_made_against_me",
)
User.made_reports = relationship(
    "Report",
    foreign_keys=[Report.reporter_id],
    backref="reports_by",
)
Item.visualization_links = relationship(
    "VisualizationLink",
    back_populates="item",
    cascade="all, delete-orphan",
)
Item.reports = relationship(
    "Report",
    foreign_keys=[Report.target_item_id],
    backref="reported_items",
)