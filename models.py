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
    verification_status: Mapped[str] = mapped_column(default="pending")
    verifier_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime.datetime | None]
    verification_notes: Mapped[str | None]

    tags = relationship("ItemTag", back_populates="item", cascade="all, delete-orphan")
    gallery_items = relationship("ItemGallery", back_populates="item", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="item", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="item", cascade="all, delete-orphan")
    verifier = relationship("User", foreign_keys=[verifier_user_id])
    organization = relationship("Organization")


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
    is_active: Mapped[bool] = True
    banned: Mapped[bool] = mapped_column(default=False)

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

    creator = relationship("User", foreign_keys=[created_by])


class OrganizationMember(db.Model):
    __tablename__ = "organization_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(default="member")  # member, editor, admin, owner
    joined_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    is_active: Mapped[bool] = True

    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization")


class Rating(db.Model):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    rating: Mapped[float]

    item = relationship("Item", back_populates="ratings")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    content: Mapped[str]

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

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    target_item = relationship("Item")
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
