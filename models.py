import datetime

from app import db
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column


class Item(db.Model):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]  # 'geodonnee', 'carte', 'application'
    title: Mapped[str]
    description: Mapped[str]
    format_type: Mapped[str | None]
    size_mb: Mapped[int | None]
    magnet_link: Mapped[str]
    image_path: Mapped[str] = mapped_column(default="/static/images/logo/ANANAS.png")
    author_name: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    is_published: Mapped[bool] = mapped_column(default=True)
    verification_status: Mapped[str] = mapped_column(default="unofficial")
    data_format_level: Mapped[str] = mapped_column(default="individual")
    verifier_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime.datetime | None]
    verification_notes: Mapped[str | None]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.is_published is None:
            self.is_published = True
        if self.verification_status is None:
            self.verification_status = "unofficial"
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    tags = relationship("ItemTag", back_populates="item", cascade="all, delete-orphan")
    gallery_items = relationship("ItemGallery", back_populates="item", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="item", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="item", cascade="all, delete-orphan")
    verifier = relationship("User", foreign_keys=[verifier_user_id])
    organization = relationship("Organization")

    def to_dict(self):
        catalogue_map = {
            "geodonnee": "/catalogue/donnees",
            "carte": "/catalogue/cartes",
            "application": "/catalogue/applications",
        }
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "format": self.format_type,
            "size": f"{self.size_mb} Mo" if self.size_mb else "",
            "magnet": self.magnet_link,
            "image": self.image_path,
            "author": self.author_name,
            "organization_id": self.organization_id,
            "organization_name": self.organization.name if self.organization else None,
            "organization_slug": self.organization.slug if self.organization else None,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "tags": [t.tag for t in self.tags],
            "gallery": self._build_gallery_dict(),
            "pdf_doc": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/r6.pdf",
            "verification_status": self.verification_status,
            "is_official_verified": self.verification_status == "verified",
            "verifier_nom": f"{self.verifier.prenom} {self.verifier.nom}" if (self.verifier and getattr(self.verifier, "prenom", None)) else None,
            "verified_at": self.verified_at.strftime("%Y-%m-%d") if self.verified_at else None,
            "verification_notes": self.verification_notes,
            "catalogue_link": catalogue_map.get(self.type, "/catalogue"),
            "report_type": self.type.replace("geodonnee", "geodonnee").replace("carte", "carte").replace("application", "application"),
            "rating": self._get_rating_avg(),
            "review_count": len(self.ratings),
            "data_format_level": self.data_format_level,
            "download_levels": [{"name": c.name, "size_mb": c.size_mb, "magnet": c.magnet_link} for c in DataChunk.query.filter_by(parent_item_id=self.id).all()] if self.data_format_level == "individual" else None,
        }

    def _get_rating_avg(self):
        if not self.ratings:
            return 3.8
        return sum(r.rating for r in self.ratings) / len(self.ratings)

    def _build_gallery_dict(self):
        result = []
        for g in self.gallery_items:
            entry = {"type": g.media_type, "label": g.label}
            if g.src:
                entry["src"] = g.src
            if g.data_json:
                if isinstance(g.data_json, dict):
                    if g.media_type == "csv":
                        entry["data"] = g.data_json.get("rows", [])
                    elif g.media_type == "dashboard":
                        entry["metrics"] = g.data_json.get("metrics", [])
            result.append(entry)
        return result


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
    media_type: Mapped[str]  # image, csv, dashboard, interactive_map
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
    is_active: Mapped[bool]
    banned: Mapped[bool]
    is_admin: Mapped[bool]
    created_at: Mapped[datetime.datetime]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = True if getattr(self, "is_active", None) is None else self.is_active
        self.banned = False if getattr(self, "banned", None) is None else bool(self.banned)
        self.is_admin = False if getattr(self, "is_admin", None) is None else bool(self.is_admin)
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    organizations = relationship("OrganizationMember", back_populates="user")


class Organization(db.Model):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    logo_url: Mapped[str | None]
    website_url: Mapped[str | None]
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = True
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.is_active is None or self.is_active is False:
            self.is_active = True
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

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
    role: Mapped[str] = mapped_column(default="member")  # member, editor, admin, owner
    joined_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    is_active: Mapped[bool] = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None or not self.role:
            self.role = "member"
        if self.is_active is None:
            self.is_active = True
        if self.joined_at is None:
            self.joined_at = datetime.datetime.now()

    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization")


class Rating(db.Model):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[float]

    item = relationship("Item", back_populates="ratings")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    author_name: Mapped[str | None]
    content: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    item = relationship("Item", back_populates="comments")


class DataChunk(db.Model):
    __tablename__ = "data_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    name: Mapped[str]
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str | None]
    format_type: Mapped[str | None]
    size_mb: Mapped[int | None]
    magnet_link: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    upload_status: Mapped[str] = mapped_column(default="pending")
    visibility: Mapped[str] = mapped_column(default="public")
    data_url: Mapped[str | None]
    metadata_json: Mapped[dict | None] = mapped_column(JSON, server_default="{}")
    is_published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.upload_status is None:
            self.upload_status = "pending"
        if self.visibility is None:
            self.visibility = "public"
        if self.is_published is None:
            self.is_published = False
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    published_at: Mapped[datetime.datetime | None]

    owner = relationship("User", back_populates="data_chunks")
    organization = relationship("Organization")


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


class VisualizationLink(db.Model):
    __tablename__ = "visualization_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    name: Mapped[str]
    url: Mapped[str]
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    link_type: Mapped[str] = mapped_column(default="external")  # external, internal, embed, widget
    display_order: Mapped[int] = mapped_column(default=0)
    description: Mapped[str | None]
    thumbnail_url: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.link_type is None:
            self.link_type = "external"
        if self.is_active is None:
            self.is_active = True
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

    item = relationship("Item", back_populates="visualization_links")


class Report(db.Model):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reported_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    report_type: Mapped[str]  # 'user', 'item_geodonnee', 'item_carte', 'item_application'
    target_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))
    reason: Mapped[str]  # spam, contenu_inapproprié, fake_data, other
    description: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="pending")  # pending, reviewed, dismissed, resolved
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime.datetime | None]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    reporter = relationship("User", foreign_keys=[reporter_id], overlaps="made_reports,reports_by")
    reported_user = relationship("User", foreign_keys=[reported_user_id], overlaps="reported_reports,reports_made_against_me")
    target_item = relationship("Item", overlaps="reported_items,reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ─── Back-references sur User et Item ───

User.data_chunks = relationship("DataChunk", back_populates="owner")
User.user_uploads = relationship("UserUpload", back_populates="owner")
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
