# Phase 3 — Initialisation & Migrations

> **Statut : ✅ TERMININÉ** — Commit `5941843` — "feat: add DB initialization and seed script (Phase 3)"

### 3.1 Flask-SQLAlchemy initialisé dans `app.py`
Configuration de `create_app()` avec SQLAlchemy, Config, CSRF configurée.

### 3.2 Migration Alembic initiale créée
**Fichier :** `alembic/versions/fa99e124f96c_initial_schema.py`
- Révision racine (pas de down_revision)
- Crée toutes les tables depuis zéro : users, organizations, organization_members, items, item_tags, item_gallery, comments, ratings, data_chunks, user_uploads, visualization_links, reports

### 3.3 Scripts d'initialisation
**Fichier :** `scripts/init_db.py` — initialisation automatique des tables
**Fichier :** `alembic/env.py` — runner de migrations (mode online/offline)
