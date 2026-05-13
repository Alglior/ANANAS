# Phase 2 — Modélisation de la Base de Données

### 2.1 Créer les modèles SQLAlchemy
**Fichier :** `models.py` (nouveau)

#### Table items (catalogue commun à donnees/cartes/applications)

```sql
CREATE TABLE items (
    id              SERIAL PRIMARY KEY,
    type            VARCHAR(20) NOT NULL,  -- 'geodonnee', 'carte', 'application'
    title           VARCHAR(300) NOT NULL,
    description     TEXT NOT NULL,
    format_type     VARCHAR(50),           -- Shapefile, GeoJSON, Carte raster, etc.
    size_mb         INTEGER,               -- taille en Mo
    magnet_link     VARCHAR(200) NOT NULL,
    image_path       VARCHAR(200) DEFAULT '/static/images/logo/ANANAS.png',
    author_name      VARCHAR(100),
    organization_id  INTEGER REFERENCES organizations(id),  -- orga qui publie la donnée (optionnel)
    created_at      TIMESTAMP DEFAULT NOW(),
    is_published    BOOLEAN DEFAULT TRUE,
    verification_status  VARCHAR(20) DEFAULT 'pending',  -- pending (données visibles mais pas vérifiées), verified (confiance officielle)
    verifier_user_id INTEGER REFERENCES users(id),       -- utilisateur qui a vérifié
    verified_at     TIMESTAMP,                           -- date de vérification
    verification_notes TEXT,                             -- notes du vérificateur
    metadata_json   JSONB                  -- pour champs extensibles
);

CREATE UNIQUE INDEX idx_items_magnet ON items(magnet_link);
CREATE INDEX idx_items_type ON items(type);
CREATE INDEX idx_items_format ON items(format_type);
CREATE INDEX idx_items_created ON items(created_at DESC);
CREATE INDEX idx_items_verification ON items(verification_status);
```

#### Table item_tags (relation many-to-many)

```sql
CREATE TABLE item_tags (
    id          SERIAL PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag         VARCHAR(50) NOT NULL
);

CREATE INDEX idx_item_tags_tag ON item_tags(tag);
```

#### Table item_gallery (galerie de chaque item)

```sql
CREATE TABLE item_gallery (
    id          SERIAL PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    media_type  VARCHAR(20) NOT NULL,  -- 'image', 'csv', 'dashboard', 'interactive_map'
    src         VARCHAR(500),           -- chemin/image/svg
    data_json   JSONB,                  -- données csv ou metrics dashboard
    label       VARCHAR(100)
);

CREATE INDEX idx_gallery_item ON item_gallery(item_id);
```

#### Table users (pour auth future)

Authentification par prénom + nom (pas de username).

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    prenom          VARCHAR(100) NOT NULL,
    nom             VARCHAR(100) NOT NULL,
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE,
    banned          BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_users_nom ON users(nom);
```

#### Table reports (signalements utilisateurs et contenus)

Les administrateurs peuvent consulter les signalements, les clôturer ou les marquer comme non fondés. Un utilisateur ne peut pas se signérer lui-même (tentative de ban/rapport sur soi-même ignoré).

```sql
CREATE TABLE reports (
    id              SERIAL PRIMARY KEY,
    reporter_id     INTEGER REFERENCES users(id),   -- NULL si signalement externe/non connecté
    reported_user_id INTEGER REFERENCES users(id),  -- NULL si ce n'est pas un utilisateur
    report_type     VARCHAR(20) NOT NULL,            -- 'user', 'item_geodonnee', 'item_carte', 'item_application'
    target_item_id  INTEGER REFERENCES items(id),    -- NULL si c'est un signalement d'utilisateur
    reason          VARCHAR(100) NOT NULL,           -- spam, contenu_inapproprié, fake_data, other
    description     TEXT,                             -- détails du signaleur
    status          VARCHAR(20) DEFAULT 'pending',   -- pending, reviewed, dismissed, resolved
    reviewed_by     INTEGER REFERENCES users(id),    -- admin qui a traité le report
    reviewed_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reports_user ON reports(reported_user_id);
CREATE INDEX idx_reports_item ON reports(target_item_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_type ON reports(report_type);
```

#### Table organizations (groupes d'utilisateurs / organisations)

Chaque utilisateur peut appartenir à une ou plusieurs organisations. Les items publiés peuvent être associés à une organisation, affichant alors le nom de l'organisation à côté du prénom + nom de l'auteur.

```sql
CREATE TABLE organizations (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,       -- nom de l'organisation ("IRD", "CNRS", "Université de Paris")
    slug                VARCHAR(100) UNIQUE NOT NULL,  -- identifiant unique URL-safe ("ird", "cnrs-geoservices")
    description         TEXT,                         -- description courte de l'organisation
    logo_url            VARCHAR(500),                 -- URL du logo (optionnel)
    website_url         VARCHAR(500),                 -- site web officiel
    created_by          INTEGER NOT NULL REFERENCES users(id),  -- administrateur fondateur
    is_active           BOOLEAN DEFAULT TRUE,         -- organisation active/désactivée
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_org_slug ON organizations(slug);
```

#### Table organization_members (liens utilisateur ↔ organisation)

Un utilisateur peut appartenir à plusieurs organisations avec des rôles différents.

```sql
CREATE TABLE organization_members (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id     INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role                VARCHAR(30) DEFAULT 'member',  -- member, editor, admin, owner
    joined_at           TIMESTAMP DEFAULT NOW(),
    is_active           BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX idx_org_members_unique ON organization_members(user_id, organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_org_members_org ON organization_members(organization_id);
```

#### Table comments

```sql
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id         INTEGER REFERENCES users(id),
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comments_item ON comments(item_id);
```

#### Table data_chunks (données fragmentées uploadées par les utilisateurs)

Chaque utilisateur peut uploader une partie des données et elle apparaît directement dans l'onglet "Données".

```sql
CREATE TABLE data_chunks (
    id                  SERIAL PRIMARY KEY,
    parent_item_id      INTEGER REFERENCES items(id),  -- NULL si nouveau jeu complet
    name                VARCHAR(200) NOT NULL,          -- nom du fragment ("Secteur Nord", "Couche hydrique B")
    owner_user_id       INTEGER NOT NULL REFERENCES users(id),
    description         TEXT,
    format_type         VARCHAR(50),                    -- Shapefile, GeoJSON, CSV, etc.
    size_mb             INTEGER,                        -- taille en Mo
    magnet_link         VARCHAR(200),                   -- lien magnet du torrent associé
    organization_id     INTEGER REFERENCES organizations(id),  -- orga qui publie le chunk (optionnel)
    upload_status       VARCHAR(20) DEFAULT 'pending',  -- pending, processing, published, failed
    visibility          VARCHAR(20) DEFAULT 'public',   -- public, private, shared
    data_url            VARCHAR(500),                   -- URL vers le fichier stocké (S3/local)
    metadata_json       JSONB,                          -- métadonnées spécifiques au dataset
    is_published        BOOLEAN DEFAULT FALSE,          -- vrai quand le traitement est terminé
    created_at          TIMESTAMP DEFAULT NOW(),
    published_at        TIMESTAMP
);

CREATE INDEX idx_chunks_owner ON data_chunks(owner_user_id);
CREATE INDEX idx_chunks_status ON data_chunks(upload_status);
CREATE INDEX idx_chunks_published ON data_chunks(is_published) WHERE is_published = TRUE;
```

#### Table visualization_links (liens d'applications ajoutées à l'onglet "Visualisation")

Chaque utilisateur peut associer des applications externes à un item pour permettre la visualisation.

```sql
CREATE TABLE visualization_links (
    id                  SERIAL PRIMARY KEY,
    parent_item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    name                VARCHAR(200) NOT NULL,          -- nom de l'app ("QGIS Online Viewer", "Dashboard Carto")
    url                 VARCHAR(500) NOT NULL,          -- URL externe vers l'application
    owner_user_id       INTEGER REFERENCES users(id),   -- NULL = lien officiel du système
    link_type           VARCHAR(30) DEFAULT 'external', -- external, internal, embed, widget
    display_order       INTEGER DEFAULT 0,              -- ordre d'affichage dans l'onglet Visualisation
    description         TEXT,
    thumbnail_url       VARCHAR(500),
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vizlinks_item ON visualization_links(parent_item_id);
CREATE INDEX idx_vizlinks_order ON visualization_links(parent_item_id, display_order);
```

#### Table user_uploads (suivi des uploads de données brutes)

Gère les fragments de données qu'un utilisateur peut soumettre pour qu'ils apparaissent dans le catalogue.

```sql
CREATE TABLE user_uploads (
    id                  SERIAL PRIMARY KEY,
    owner_user_id       INTEGER NOT NULL REFERENCES users(id),
    parent_item_id      INTEGER REFERENCES items(id),   -- NULL = nouveau dataset complet
    chunk_id            INTEGER REFERENCES data_chunks(id),  -- lien vers le chunk créé
    file_name           VARCHAR(300) NOT NULL,          -- nom du fichier uploadé
    file_size_bytes     BIGINT,                          -- taille en octets
    mime_type           VARCHAR(100),                   -- application/x-shp, text/csv, etc.
    original_format     VARCHAR(50),                    -- format d'origine avant conversion
    uploaded_at         TIMESTAMP DEFAULT NOW(),
    processing_status   VARCHAR(20) DEFAULT 'queued',   -- queued, converting, done, error
    error_message       TEXT,
    published_item_id   INTEGER REFERENCES items(id)    -- l'item créé dans le catalogue après traitement
);

CREATE INDEX idx_uploads_owner ON user_uploads(owner_user_id);
CREATE INDEX idx_uploads_status ON user_uploads(processing_status);
```

---

### 2.2 Définir les modèles ORM Python
**Fichier :** `models.py`

```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

db = SQLAlchemy()

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_published: Mapped[bool] = mapped_column(default=True)
    verification_status: Mapped[str] = mapped_column(default="pending")
    verifier_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None]
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
    data_json: Mapped[dict | None] = mapped_column(server_default="{}")
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


# ─── Organisations / Groupes d'utilisateurs ───

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    creator = relationship("User", foreign_keys=[created_by])


class OrganizationMember(db.Model):
    __tablename__ = "organization_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(default="member")  # member, editor, admin, owner
    joined_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_active: Mapped[bool] = True

    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization")


class Rating(db.Model):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    rating: Mapped[float]


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    content: Mapped[str]


# ─── Chunks de données uploadés (visible dans onglet Données) ───

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
    metadata_json: Mapped[dict | None] = mapped_column(server_default="{}")
    is_published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    published_at: Mapped[datetime | None]

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
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.now)
    processing_status: Mapped[str] = mapped_column(default="queued")
    error_message: Mapped[str | None]
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    published_item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"))

    owner = relationship("User", back_populates="user_uploads")
    organization = relationship("Organization")


# ─── Liens d'applications (visible dans onglet Visualisation) ───

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    item = relationship("Item", back_populates="visualization_links")


# ─── Système de signalements ───

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
    reviewed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    target_item = relationship("Item")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# ─── Back-references sur User ───
User.data_chunks = relationship("DataChunk", back_populates="owner")
User.user_uploads = relationship("UserUpload", back_populates="owner")
User.reported_reports = relationship("Report", foreign_keys=[Report.reported_user_id], backref="reports_made_against_me")
User.made_reports = relationship("Report", foreign_keys=[Report.reporter_id], backref="reports_by")
Item.visualization_links = relationship("VisualizationLink", back_populates="item", cascade="all, delete-orphan")
Item.reports = relationship("Report", foreign_keys=[Report.target_item_id], backref="reported_items")
```
