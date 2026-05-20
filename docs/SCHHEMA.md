# Schéma Relationnel de la Base de Données

Ce document présente le schéma relationnel de l'application **A.N.A.N.A.S.** basée sur PostgreSQL avec SQLAlchemy (Flask-SQLAlchemy).

---

## Technologie

| Composant | Valeur |
|-----------|--------|
| ORM | SQLAlchemy 2.x (via Flask-SQLAlchemy) |
| Migrations | Alembic |
| Base de données | PostgreSQL 18 |

---

## Schéma Physique

### Table `users`

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    prenom          VARCHAR NOT NULL,
    nom             VARCHAR NOT NULL,
    email           VARCHAR NOT NULL UNIQUE,
    password_hash   VARCHAR NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    banned          BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Table `organizations`

```sql
CREATE TABLE organizations (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR NOT NULL,
    slug            VARCHAR NOT NULL UNIQUE,
    description     TEXT,
    logo_url        TEXT,
    website_url     TEXT,
    created_by      INTEGER NOT NULL REFERENCES users(id),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Table `organization_members` (Many-to-Many)

```sql
CREATE TABLE organization_members (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role            VARCHAR NOT NULL,  -- 'member', 'editor', 'admin', 'owner'
    joined_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);
```

### Table `items` (Catalogue)

```sql
CREATE TABLE items (
    id                      SERIAL PRIMARY KEY,
    type                    VARCHAR NOT NULL,  -- 'geodonnee', 'carte', 'application'
    title                   VARCHAR NOT NULL,
    description             TEXT NOT NULL,
    format_type             VARCHAR,
        magnet_link             VARCHAR NOT NULL,
        image_path              VARCHAR NOT NULL DEFAULT '/static/images/logo/ANANAS.png',
    author_name             TEXT,
    organization_id         INTEGER REFERENCES organizations(id),
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    verification_status     VARCHAR NOT NULL DEFAULT 'unofficial',  -- 'unofficial', 'verified'
    data_format_level       VARCHAR NOT NULL DEFAULT 'individual',  -- 'individual', 'pack'
    verifier_user_id        INTEGER REFERENCES users(id),
    verified_at             TIMESTAMP,
    verification_notes      TEXT,
    owner_user_id           INTEGER REFERENCES users(id)
);
```

### Table `item_tags`

```sql
CREATE TABLE item_tags (
    id              SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag             VARCHAR NOT NULL
);
```

### Table `item_gallery`

```sql
CREATE TABLE item_gallery (
    id              SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    media_type      VARCHAR NOT NULL,  -- 'image', 'csv', 'dashboard', 'interactive_map'
    src             TEXT,
    data_json       JSON NOT NULL DEFAULT '{}',
    label           VARCHAR
);
```

### Table `ratings`

```sql
CREATE TABLE ratings (
    id              SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id         INTEGER REFERENCES users(id),
    rating          REAL NOT NULL CHECK (rating >= 1 AND rating <= 5)
);
```

### Table `comments`

```sql
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    author_name     TEXT,
    content         VARCHAR NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    user_id         INTEGER REFERENCES users(id)
);
```

### Table `data_chunks`

```sql
CREATE TABLE data_chunks (
    id                  SERIAL PRIMARY KEY,
    parent_item_id      INTEGER REFERENCES items(id),
    name                VARCHAR NOT NULL,
    owner_user_id       INTEGER NOT NULL REFERENCES users(id),
    description         TEXT,
    format_type         VARCHAR,
    magnet_link         TEXT,
    organization_id     INTEGER REFERENCES organizations(id),
    data_url            TEXT,
    metadata_json       JSON NOT NULL DEFAULT '{}',
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    upload_status       VARCHAR NOT NULL DEFAULT 'uploaded',  -- 'uploaded', 'processing', 'ready', 'error'
    published_at        TIMESTAMP
);
```

### Table `user_uploads`

```sql
CREATE TABLE user_uploads (
    id                      SERIAL PRIMARY KEY,
    owner_user_id           INTEGER NOT NULL REFERENCES users(id),
    parent_item_id          INTEGER REFERENCES items(id),
    chunk_id                INTEGER REFERENCES data_chunks(id),
    file_name               VARCHAR NOT NULL,
    file_size_bytes         BIGINT,
    mime_type               VARCHAR,
    original_format         VARCHAR,
    uploaded_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    processing_status       VARCHAR NOT NULL DEFAULT 'queued',  -- 'queued', 'processing', 'done', 'error'
    error_message           TEXT,
    organization_id         INTEGER REFERENCES organizations(id),
    published_item_id       INTEGER REFERENCES items(id)
);
```

### Table `visualization_links`

```sql
CREATE TABLE visualization_links (
    id                  SERIAL PRIMARY KEY,
    parent_item_id      INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    name                VARCHAR NOT NULL,
    url                 VARCHAR NOT NULL,
    owner_user_id       INTEGER REFERENCES users(id),
    link_type           VARCHAR NOT NULL DEFAULT 'external',  -- 'external', 'internal', 'embed', 'widget'
    display_order       INTEGER NOT NULL DEFAULT 0,
    description         TEXT,
    thumbnail_url       TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Table `reports`

```sql
CREATE TABLE reports (
    id                  SERIAL PRIMARY KEY,
    reporter_id         INTEGER REFERENCES users(id),
    reported_user_id    INTEGER REFERENCES users(id),
    report_type         VARCHAR NOT NULL,  -- 'user', 'item_geodonnee', 'item_carte', 'item_application'
    target_item_id      INTEGER REFERENCES items(id),
    reason              VARCHAR NOT NULL,  -- 'spam', 'fake_data', 'other'
    description         TEXT,
    status              VARCHAR NOT NULL DEFAULT 'pending',  -- 'pending', 'reviewed', 'dismissed', 'resolved'
    reviewed_by         INTEGER REFERENCES users(id),
    reviewed_at         TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Table `admin_audit`

```sql
CREATE TABLE admin_audit (
    id                  SERIAL PRIMARY KEY,
    admin_user_id       INTEGER REFERENCES users(id),
    action_type         VARCHAR NOT NULL,  -- 'ban', 'unban', 'resolved', 'dismissed', 'comment_deleted', 'item_deleted', 'item_verified', 'item_unverified', 'user_verify'
    target_type         VARCHAR,  -- 'user', 'item', 'report'
    target_id           INTEGER,
    details             JSON NOT NULL DEFAULT '{}',
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_admin_audit_admin_user_id ON admin_audit(admin_user_id);
CREATE INDEX ix_admin_audit_action_type   ON admin_audit(action_type);
```

---

## Diagramme Relationnel (ER)

```
┌───────────┐      ┌──────────────────────┐      ┌──────────────────┐
│  USERS    │<─────│ ORGANIZATION_MEMBERS │──────>│ ORGANIZATIONS    │
│           │      │                      │      │                  │
│ id (PK)   │      │ user_id (FK→users)   │      │ id (PK)          │
│ prenom    │      │ org_id (FK→orgs)     │      │ name             │
│ nom       │      │ role                 │      │ slug (unique)    │
│ email     │      │ joined_at            │      │ description      │
│ pwd_hash  │      │ is_active            │      │ created_by(FK)   │
│ is_active │      └──────────────────────┘      │ is_active        │
│ banned      ┌─────────┴────┐                    │ website_url      │
│ is_admin    │              ├────────────────────>│                  │
│ created_at  │   Items      │                     └──────────────────┘
└─────────────┘              │
                             │
             ┌───────────────┼───────────────────┐
             │               │                   │
┌────────────▼─────┐ ┌──────┴──────┐   ┌────────┴──────────┐
│     ITEMS        │ │ ITEM_TAGS   │   │    ITEM_GALLERY   │
│                  │ │             │   │                   │
│ id (PK)          │ item_id(FK)   │   │ id (PK)           │
│ type             │ tag           │   │ item_id (FK)      │
│ title            └───────────────┘   │ media_type          │
│ description               ┌──────────┼────────┐            │
│ magnet_link      ┌───────┴────────┐ │ src      │ data_json  │
│ org_id (FK)      │                │ │          │ label      │
│ owner_user_id(FK)│   RATINGS      │ └──────────┴──────────┘
│ verifier_id(FK)  │                │
│ ver_status       │ item_id(FK)    │     ┌─────────────────────┐
│ verified_at      │ user_id (FK)   │     │    COMMENTS         │
│ notes            │ rating         │     │                     │
│ data_format_lvl  │                │     │ id (PK)             │
└────────┬─────────┘ └──────────────┘     │ item_id (FK)        │
         │                                │ author_name         │
┌────────┴──────────┐  ┌───────────────┐  │ content             │
│ DATA_CHUNKS       │  │ VISUALIZATION │  │ created_at          │
│                   │  │ LINKS         │  │ user_id (FK)        │
│ id (PK)           │  │               │  └─────────────────────┘
│ parent_item_id(FK)│  │ id (PK)       │
│ name              │  │ parent_item   │     ┌───────────────────┐
│ owner_user_id(FK) │  │ name          │     │    REPORTS        │
│ org_id (FK)       │  │ url           │     │                   │
│ metadata_json     │  │ display_order │     │ reporter_id (FK)  │
│ upload_status     │  │ thumbnail_url │     │ report_type       │
│ published_at      │  │ is_active     │     │ target_item (FK)  │
└────────┬──────────┘ └───────┬───────┘     │ reason              │
         │                    │              │ status              │
┌────────┴──────────┐  ┌─────┴────────┐    │ reviewed_by (FK)   │
│ USER_UPLOADS      │  │ ADMIN_AUDIT  │    │ reviewed_at        │
│                   │  │              │    │ created_at         │
│ id (PK)           │  │ id (PK)      │    └────────────────────┘
│ owner_user_id(FK) │  │ admin_user   │
│ parent_item_id(FK)│  │ action_type  │
│ chunk_id (FK)     │  │ target_type  │
│ file_name         │  │ target_id    │
│ mime_type         │  │ details(JSON)│
│ processing_status │  │ created_at   │
│ published_item(FK)│ └────────────────┘
│ org_id (FK)       │
└───────────────────┘
```

---

## Clés Étrangères Détaillées

| Champ | Table | Référence | Contrainte |
|-------|-------|-----------|------------|
| `organizations.created_by` | organizations | users.id | NOT NULL |
| `organization_members.user_id` | organization_members | users.id | ON DELETE CASCADE |
| `organization_members.organization_id` | organization_members | organizations.id | ON DELETE CASCADE |
| `items.organization_id` | items | organizations.id | NULLABLE |
| `items.verifier_user_id` | items | users.id | NULLABLE |
| `items.owner_user_id` | items | users.id | NULLABLE |
| `item_tags.item_id` | item_tags | items.id | ON DELETE CASCADE |
| `item_gallery.item_id` | item_gallery | items.id | ON DELETE CASCADE |
| `ratings.item_id` | ratings | items.id | ON DELETE CASCADE |
| `ratings.user_id` | ratings | users.id | NULLABLE |
| `comments.item_id` | comments | items.id | ON DELETE CASCADE |
| `comments.user_id` | comments | users.id | NULLABLE |
| `data_chunks.parent_item_id` | data_chunks | items.id | NULLABLE |
| `data_chunks.owner_user_id` | data_chunks | users.id | NOT NULL |
| `data_chunks.organization_id` | data_chunks | organizations.id | NULLABLE |
| `user_uploads.owner_user_id` | user_uploads | users.id | NOT NULL |
| `user_uploads.parent_item_id` | user_uploads | items.id | NULLABLE |
| `user_uploads.chunk_id` | user_uploads | data_chunks.id | NULLABLE |
| `user_uploads.published_item_id` | user_uploads | items.id | NULLABLE |
| `user_uploads.organization_id` | user_uploads | organizations.id | NULLABLE |
| `visualization_links.parent_item_id` | visualization_links | items.id | ON DELETE CASCADE |
| `visualization_links.owner_user_id` | visualization_links | users.id | NULLABLE |
| `reports.reporter_id` | reports | users.id | NULLABLE |
| `reports.reported_user_id` | reports | users.id | NULLABLE |
| `reports.target_item_id` | reports | items.id | NULLABLE |
| `reports.reviewed_by` | reports | users.id | NULLABLE |
| `admin_audit.admin_user_id` | admin_audit | users.id | NULLABLE |

---

## Valeurs Possible des Champs ENUM/VARCHAR

### `items.type`
- `geodonnee`, `carte`, `application`

### `items.verification_status`
- `unofficial`, `verified`

### `items.data_format_level`
- `individual`, `pack`

### `item_gallery.media_type`
- `image`, `csv`, `dashboard`, `interactive_map`

### `organization_members.role`
- `member`, `editor`, `admin`, `owner`

### `data_chunks.upload_status`
- `uploaded`, `processing`, `ready`, `error`

### `user_uploads.processing_status`
- `queued`, `processing`, `done`, `error`

### `visualization_links.link_type`
- `external`, `internal`, `embed`, `widget`

### `reports.report_type`
- `user`, `item_geodonnee`, `item_carte`, `item_application`

### `reports.reason`
- `spam`, `fake_data`, `other`

### `reports.status`
- `pending`, `reviewed`, `dismissed`, `resolved`

### `admin_audit.action_type`
- `ban`, `unban`, `resolved`, `dismissed`, `comment_deleted`, `item_deleted`, `item_verified`, `item_unverified`, `user_verify`

---

## Résumé

| # | Table | Colonnes | PKs | FKs | Références NULLABLES |
|---|-------|----------|-----|-----|----------------------|
| 1 | users | 9 | id | — | — |
| 2 | organizations | 9 | id | created_by → users.id | — |
| 3 | organization_members | 6 | id | user_id → users.id, org_id → orgs.id | — |
| 4 | items | 16 | id | org_id → orgs.id, verifier → users, owner → users | org, verifier, owner |
| 5 | item_tags | 3 | id | item_id → items.id | — |
| 6 | item_gallery | 6 | id | item_id → items.id | — |
| 7 | ratings | 4 | id | item_id → items.id, user_id → users | — |
| 8 | comments | 6 | id | item_id → items.id, user_id → users | — |
| 9 | data_chunks | 13 | id | parent → items, owner → users, org → orgs | parent, org |
| 10 | user_uploads | 13 | id | owner → users, parent → items, chunk → data_chunks, pub → items, org → orgs | owner, parent, chunk, publisher, org |
| 11 | visualization_links | 11 | id | parent → items, owner → users | — |
| 12 | reports | 10 | id | reporter → users, reportee → users, target → items, reviewer → users | reporter, reportee, target, reviewer |
| 13 | admin_audit | 7 | id | admin → users | — |
| **Total** | **13 tables** | **113 colonnes** | **13 PKs** | **22 FKs** | **—** |

---

## Historique des Migrations Alembic

```
fa99e124f96c  initial_schema          → Toutes les tables de base
a1b2c3d4e5f6  auth_interactions       → is_active, is_admin, created_at (users); 
                                          author_name, created_at (comments); user_id (ratings)
b2c3d4e5f6g7  add_data_format_level   → data_format_level (items)
32cff08a15b4  add_admin_audit_table   → Table admin_audit + index
c3d4e5f6g7h8  add_user_id_comments    → user_id FK → users (comments)
d4e5f6g7h8i9  add_owner_user_items    → owner_user_id FK → users (items)
e5f6g7h8i9j0  remove_is_published     → suppression de is_published (items)
f6g7h8i9j0k1  remove_data_chunk_fields → suppression de visibility/is_published (data_chunks)
```

---

*Dernière mise à jour : Mai 2026*
