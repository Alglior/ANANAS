import datetime
import json
import os

from app import db
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from utils.security import sanitize_gallery_data, sanitize_value, validate_external_url, validate_magnet_link

IMOD_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "config", "imod-config.json"
)


def load_imod_config():
    default = {
        "weights": {"meta": 45, "tech": 36, "rich": 19},
        "max_raw": {"meta": 10, "tech": 10, "rich": 10},
        "thresholds": {"high": 70, "medium": 40},
        "levels": {"high": "Élevé", "medium": "Moyen", "low": "Faible"},
        "format_level_points": {"individual": 1, "simple": 2, "pack": 3},
    }
    try:
        with open(IMOD_CONFIG_PATH, encoding="utf-8") as f:
            config = json.load(f)
        for key in default:
            config.setdefault(key, default[key])
        for dim in default["weights"]:
            config["weights"].setdefault(dim, default["weights"][dim])
            config["max_raw"].setdefault(dim, default["max_raw"][dim])
        return config
    except (OSError, ValueError):
        return default


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class Item(db.Model, TimestampMixin):
    __tablename__ = "items"
    __table_args__ = (
        db.Index("ix_items_type", "type"),
        db.Index("ix_items_status", "status"),
        db.Index("ix_items_owner_user_id", "owner_user_id"),
        db.Index("ix_items_verification_status", "verification_status"),
        db.Index("ix_items_organization_id", "organization_id"),
        db.Index("ix_items_data_format_level", "data_format_level"),
    )

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
    imod_score: Mapped[float | None] = mapped_column(index=True)
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
    gallery_items = relationship("ItemGallery", back_populates="item", cascade="all, delete-orphan", order_by="ItemGallery.id")
    image_jobs = relationship("ItemImageJob", back_populates="item", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="item", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="item", cascade="all, delete-orphan")
    verifier = relationship("User", foreign_keys=[verifier_user_id])
    organization = relationship("Organization")

    CATALOGUE_MAP = {
        "geodonnee": "/catalogue/donnees",
        "carte": "/catalogue/cartes",
        "application": "/catalogue/applications",
    }

    def _compute_imod_score(self):
        cfg = load_imod_config()
        w = cfg["weights"]
        mr = cfg["max_raw"]
        thr = cfg["thresholds"]
        lvls = cfg["levels"]

        meta_score = 0
        if self.description and len(self.description.strip()) > 0:
            meta_score += 1
            if len(self.description) > 100:
                meta_score += 1
        tag_count = len(self.tags)
        if tag_count >= 3:
            meta_score += 2
        elif tag_count >= 1:
            meta_score += 1
        if self.license_type:
            meta_score += 2
        if self.author_name:
            meta_score += 1
        if self.organization:
            meta_score += 1
        if self.pdf_magnet_link and validate_magnet_link(self.pdf_magnet_link):
            meta_score += 2
        meta_pct = (min(meta_score, mr["meta"]) / mr["meta"]) * w["meta"]

        tech_score = 0
        if self.format_type:
            tech_score += 2
        if validate_magnet_link(self.magnet_link):
            tech_score += 2
        fmt_level = cfg["format_level_points"]
        tech_score += fmt_level.get(self.data_format_level, 0)
        tech_pct = (min(tech_score, mr["tech"]) / mr["tech"]) * w["tech"]

        rich_score = 0
        gallery_count = len(self.gallery_items)
        if gallery_count >= 5:
            rich_score += 3
        elif gallery_count >= 3:
            rich_score += 2
        elif gallery_count >= 1:
            rich_score += 1
        viz_count = len(self.visualization_links)
        if viz_count >= 3:
            rich_score += 2
        elif viz_count >= 1:
            rich_score += 1
        rating_count = len(self.ratings)
        if rating_count > 0:
            rich_score += 1
        if rating_count > 5:
            rich_score += 1
        comment_count = len(self.comments)
        if comment_count > 0:
            rich_score += 1
        if comment_count > 3:
            rich_score += 1
        if self._get_image_magnets():
            rich_score += 1
        rich_pct = (min(rich_score, mr["rich"]) / mr["rich"]) * w["rich"]

        imod = round(meta_pct + tech_pct + rich_pct, 1)

        # +20 pts de bonus quand l'item est vérifié par un admin
        if self.verification_status == "verified":
            imod = min(imod + 20, 100)

        if imod >= thr["high"]:
            level = "Eleve"
        elif imod >= thr["medium"]:
            level = "Moyen"
        else:
            level = "Faible"
        return {
            "score": imod,
            "level": level,
            "meta": round(meta_pct, 1),
            "tech": round(tech_pct, 1),
            "rich": round(rich_pct, 1),
        }

    def refresh_imod_cache(self):
        """Persiste le score IMOD calculé pour permettre un tri SQL efficace."""
        self.imod_score = self._compute_imod_score()["score"]
        return self.imod_score

    def to_dict(self, include_details=False):
        imod = self._compute_imod_score()
        tag_names = [t.tag for t in self.tags]
        tag_categories = self._get_tag_categories(tag_names)
        unique_categories = list(dict.fromkeys(c for c in tag_categories.values() if c))
        grouped = {}
        for tag, cat in tag_categories.items():
            if cat:
                grouped.setdefault(cat, []).append(tag)
        zoom_levels = []
        if isinstance(self.metadata_json, list):
            seen = set()
            for entry in self.metadata_json:
                zl = entry.get("zoom_level", "") if isinstance(entry, dict) else ""
                if zl and zl not in seen:
                    seen.add(zl)
                    zoom_levels.append(zl)
        elif isinstance(self.metadata_json, dict):
            zoom_levels = self.metadata_json.get("zoom_levels", [])
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
            "metadata_json": self.metadata_json if isinstance(self.metadata_json, dict) else None,
            "image": self.image_path,
            "author": self.author_name,
            "owner_user_id": self.owner_user_id,
            "organization_id": self.organization_id,
            "organization_name": self.organization.name if self.organization else None,
            "organization_slug": self.organization.slug if self.organization else None,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "tags": tag_names,
            "tag_categories": tag_categories,
            "unique_categories": unique_categories,
            "grouped_categories": [{"category": k, "tags": v} for k, v in grouped.items()],
            "zoom_levels": zoom_levels,
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
            "image_magnet_links": self.image_magnet_links if isinstance(self.image_magnet_links, list) else [],
            "visualization_links": [vl.to_dict() for vl in self.visualization_links],
            "imod": imod,
        }
        if include_details:
            result["data_chunks"] = [c.to_dict() for c in DataChunk.query.filter_by(parent_item_id=self.id).all()]
        return result

    def _get_tag_categories(self, tag_names):
        if not tag_names:
            return {}
        predefined_tags = PredefinedTag.query.options(
            db.joinedload(PredefinedTag.category)
        ).filter(PredefinedTag.name.in_(tag_names)).all()
        tag_to_category = {pt.name: pt.category.name for pt in predefined_tags if pt.category}
        return {tag: tag_to_category.get(tag) for tag in tag_names}

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
    __table_args__ = (
        db.Index("ix_item_tags_item_id", "item_id"),
        db.Index("ix_item_tags_tag", "tag"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    tag: Mapped[str]

    item = relationship("Item", back_populates="tags")


class ItemGallery(db.Model):
    __tablename__ = "item_gallery"
    __table_args__ = (
        db.Index("ix_item_gallery_item_id", "item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    media_type: Mapped[str]
    src: Mapped[str | None]
    data_json: Mapped[dict | None] = mapped_column(JSON, server_default="{}")
    label: Mapped[str | None]

    item = relationship("Item", back_populates="gallery_items")


class ItemImageJob(db.Model):
    __tablename__ = "item_image_jobs"
    __table_args__ = (
        db.Index("ix_item_image_jobs_item_id", "item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    idx: Mapped[int] = mapped_column(default=0)
    magnet_link: Mapped[str]
    label: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="pending")
    progress: Mapped[float] = mapped_column(default=0.0)
    details: Mapped[str | None] = mapped_column(default=None)

    item = relationship("Item", back_populates="image_jobs")


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    prenom: Mapped[str]
    nom: Mapped[str]
    pseudo: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    avatar_path: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    muted_until: Mapped[datetime.datetime | None]
    warned: Mapped[bool] = mapped_column(default=False)
    warnings: Mapped[str | None]
    session_version: Mapped[int] = mapped_column(default=0)
    recovery_codes_hash: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)
    totp_secret: Mapped[str | None] = mapped_column(default=None, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(default=False)

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


class OrganizationJoinRequest(db.Model, TimestampMixin):
    __tablename__ = "organization_join_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))

    user = relationship("User")
    organization = relationship("Organization")


class Rating(db.Model):
    __tablename__ = "ratings"
    __table_args__ = (
        db.Index("ix_ratings_item_id", "item_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[float]

    item = relationship("Item", back_populates="ratings")


class Comment(db.Model, TimestampMixin):
    __tablename__ = "comments"
    __table_args__ = (
        db.Index("ix_comments_item_id", "item_id"),
    )
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
    __table_args__ = (
        db.Index("ix_data_chunks_parent_item_id", "parent_item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
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
    parent_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("data_chunks.id"))
    file_name: Mapped[str]
    file_size_bytes: Mapped[int | None]
    mime_type: Mapped[str | None]
    original_format: Mapped[str | None]
    uploaded_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    processing_status: Mapped[str] = mapped_column(default="queued")
    error_message: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    published_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"))

    owner = relationship("User", back_populates="user_uploads")
    organization = relationship("Organization")


class VisualizationLink(db.Model, TimestampMixin):
    __tablename__ = "visualization_links"
    __table_args__ = (
        db.Index("ix_visualization_links_parent_item_id", "parent_item_id"),
    )

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
    __table_args__ = (
        db.Index("ix_reports_target_item_id", "target_item_id"),
    )

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


class SimpleFileItem(db.Model, TimestampMixin):
    __tablename__ = "simple_file_items"

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


class CatalogueConfig(db.Model):
    __tablename__ = "catalogue_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogue_type: Mapped[str] = mapped_column(unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True)


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(unique=True, nullable=False)
    value: Mapped[str]


class GeoPackage(db.Model, TimestampMixin):
    __tablename__ = "geo_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    format_info: Mapped[str]
    link_url: Mapped[str]
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class ChangelogVersion(db.Model, TimestampMixin):
    __tablename__ = "changelog_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[str] = mapped_column(nullable=False)
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    sections: Mapped[list["ChangelogSection"]] = relationship(
        "ChangelogSection", back_populates="version",
        cascade="all, delete-orphan", order_by="ChangelogSection.display_order",
    )


class ChangelogSection(db.Model):
    __tablename__ = "changelog_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("changelog_versions.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(nullable=False)
    items: Mapped[str] = mapped_column(nullable=False, default="[]")
    display_order: Mapped[int] = mapped_column(default=0)
    version: Mapped["ChangelogVersion"] = relationship("ChangelogVersion", back_populates="sections")


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
    cascade="all, delete-orphan",
)
Item.data_chunks = relationship(
    "DataChunk",
    foreign_keys="DataChunk.parent_item_id",
    backref="parent_item",
    cascade="all, delete-orphan",
)
Item.user_uploads = relationship(
    "UserUpload",
    foreign_keys="UserUpload.parent_item_id",
    backref="parent_item",
    cascade="all, delete-orphan",
)