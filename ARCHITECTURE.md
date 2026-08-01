# Architecture du Projet A.N.A.N.A.S.

## Vue d'ensemble

**A.N.A.N.A.S.** est un portail de services de données géospatiales qui distribue des données géographiques via magnet links et le protocole BitTorrent. C'est une application web Flask avec une architecture modulaire basée sur les blueprints, utilisant PostgreSQL 18 comme base de données relationnelle.

L'application supporte l'authentification, la gestion d'organisations, les interactions utilisateurs (ratings, commentaires, signalements), et un panneau d'administration pour la modération. Elle est déployable via Docker avec PostgreSQL ou en mode local avec Flask dev server.

---

## Stack Technique

| Couche | Technologie |
|--------|-------------|
| Framework Web | Flask 3.1.0 (Python) |
| ORM | SQLAlchemy 2.x (via Flask-SQLAlchemy) |
| Migrations | Alembic (via Flask-Migrate) |
| Moteur de templates | Jinja2 avec héritage `base.html` |
| Serveur de production | Gunicorn 23.0.0 (3 workers, timeout 30s) |
| Base de données | PostgreSQL 18 Alpine |
| Sécurité | Flask-WTF (CSRF), Flask-Limiter (rate limiting), bleach (sanitisation) |
| CSS | Vanilla CSS modulaire — primitives/ et features/ |
| JavaScript | Vanilla JS en modules IIFE |
| Containerisation | Docker + Docker Compose (Python 3.12-slim, utilisateur non-root `appuser`) |

---

## Architecture de l'Application

### Pattern Factory

L'application utilise le pattern **Factory** via `create_app()` dans `app.py` :
- Crée l'instance Flask, charge la configuration depuis `.secret` + variables d'environnement
- Configure SQLAlchemy et Alembic Migrate
- Applique les headers de sécurité (`after_request`)
- Configure les cookies de session (HTTP-only, SameSite=Lax)
- Initialise CSRFProtect avec exemptions pour `/api/*` et `/health`
- Installe le rate limiter (Flask-Limiter)
- Enregistre dynamiquement les routes statiques via `_register_view()` helper
- Enregistre tous les blueprints modulaires

### Structure Modulaire (Blueprints)

Le code est organisé en **8 blueprints** répartis dans `src/` :

| Blueprint | Fichier | Routes principales | Responsable |
|-----------|---------|--------------------|-------------|
| `auth` | `src/auth_routes.py` | `/connexion`, `/inscription`, `/logout` | Authentification, validation mot de passe |
| `catalogue` | `src/catalogue_routes.py` | `/catalogue/{donnees\|cartes\|applications}`, JSON API | Filtrage paginé avec convertisseur `CatalogueTypeConverter` |
| `items` | `src/item_routes.py` | `/catalogue/item/<id>`, galerie, téléchargement magnets | Détail d'item, galerie inline, zoom magnets, favicon |
| `organizations` | `src/organization_routes.py` | `/api/organizations`, `/organizations/<slug>` | CRUD orgs, membres, API |
| `admin` | `src/admin_routes.py` | `/admin/users`, `/admin/reports`, ban/unban | Modération, gestion utilisateurs |
| `interactions` | `src/interactions.py` | `/catalogue/item/<id>/rate`, `/comment`, vérification | Ratings (1-5), commentaires, verification d'items |
| `upload` | `src/upload_routes.py` | `/api/upload/chunk`, liens de visualisation | Upload par chunks, validation magic bytes |
| `api_docs` | `src/api_docs.py` | `/api` | Documentation interactive de l'API REST |

### Fichiers Partagés

- **`src/shared.py`** — Decorator `@login_required`, helper `get_current_user()`, pagination (`_build_page_numbers()`), configuration (`Config.validate()`)
- **`utils/security.py`** — `sanitize_html()` (bleach), `validate_external_url()`, `validate_file_magic()` (vérification magic bytes)

---

## Routes / Endpoints

### Public

| Méthode | URL | Endpoint | Template/API | Description |
|---------|-----|----------|-------------|-------------|
| GET | `/` | `home` | `index.html` | Page d'accueil |
| GET | `/contact` | `contact` | `contact.html` | Page contact |
| GET | `/catalogue` | `catalogue` | `catalogue.html` | Vue par défaut (donnees) |
| GET | `/catalogue/{type}` | `catalogue_view` | `catalogue.html` | {donnees\|cartes\|applications} |
| GET | `/catalogue/{type}/{page}` | — | `catalogue.html` | Pagination |
| GET | `/catalogue/{type}/{page}/json` | — | JSON API | Liste paginée au format JSON |
| GET | `/connexion` | `auth.connexion_page` | `connexion.html` | Formulaire de connexion |
| GET | `/inscription` | `auth.inscription_page` | `inscription.html` | Formulaire d'inscription |
| GET | `/logout` | `auth.logout` | — | Déconnexion (clear session) |
| GET | `/catalogue/item/<id>` | `items.item_detail_view` | `item_detail.html` | Détail item avec galerie, ratings, magnets par échelle et IMOD |
| GET | `/catalogue/item/<id>/magnets/download` | `items.download_item_magnets` | `.magnet` file | Téléchargement de tous les liens magnet groupés par échelle |
| GET | `/catalogue/item/<id>/gallery` | `items.item_gallery_view` | `gallery.html` | Galerie plein écran (Leaflet, CSV viewer) |
| GET | `/organizations/<slug>` | — | `organization_detail.html` | Page d'une organisation |
| GET | `/organizations/<slug>/items` | `org.organization_items_view` | `organization_detail.html` | Items d'une organisation |
| GET | `/health` | `health_check` | JSON | Health check |

### Auth POST

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/connexion` | Login (5 req/heure rate limit) |
| POST | `/inscription` | Inscription avec validation mot de passe complexe |

### API Interactions

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/catalogue/item/<id>/rate` | Note 1-5 sur un item |
| POST | `/catalogue/item/<id>/comment` | Ajouter un commentaire (sanitisation HTML) |
| POST | `/api/items/<id>/verify` | Vérifier/rejeter un item (admin) |

### API Organisations

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/organizations` | Créer une organisation |
| POST | `/api/organizations/<slug>/join` | Rejoindre une organisation |
| POST | `/api/organizations/<slug>/leave` | Quitter une organisation |
| POST | `/api/organizations/<slug>/members/<id>/role` | Modifier le rôle d'un membre (admin/owner) |

### Upload

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/upload/chunk` | Upload de fichier chunké (csv, shp, geojson, gpkg, json, xml) |
| POST | `/api/items/<id>/viz-links` | Ajouter un lien de visualisation |

### Admin (login_required + is_admin)

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/admin/users` | Liste des utilisateurs |
| GET | `/admin/reports` | Signalements en attente |
| GET | `/api/admin/reports` | API signalements (filtrage) |
| POST | `/api/admin/reports/<id>/resolve` | Résoudre un signalement |
| POST | `/api/users/<id>/ban` | Bannir/unban un utilisateur |
| GET | `/api/users/banned` | Liste des utilisateurs bannis |

---

## Modèles de Données (SQLAlchemy)

12 modèles relationnels dans `models.py` :

| Modèle | Table | Champs Clés | Description |
|--------|-------|-------------|-------------|
| **User** | `users` | id, prenom, nom, email(unique), password_hash, is_active, banned, is_admin, created_at | Utilisateurs authentifiés |
| **Organization** | `organizations` | id, name, slug(unique), description, logo_url, website_url, created_by, is_active, created_at | Structures qui publient des données |
| **OrganizationMember** | `organization_members` | id, user_id(FK), organization_id(FK), role(member\|editor\|admin\|owner), joined_at, is_active | Appartenance utilisateur → organisation |
| **Item** | `items` | id, type(geodonnee\|carte\|application), title, description, format_type, magnet_link, organization_id(FK), verification_status, verifier_user_id(FK) | Données géospatiales du catalogue |
| **ItemTag** | `item_tags` | id, item_id(FK), tag | Tags associés aux items |
| **ItemGallery** | `item_gallery` | id, item_id(FK), media_type(image\|csv\|dashboard\|interactive_map), src, data_json(JSON), label | Galerie inline des items |
| **Rating** | `ratings` | id, item_id(FK), user_id(FK), rating(float 1-5) | Notes utilisateurs sur les items |
| **Comment** | `comments` | id, item_id(FK), author_name, content, created_at | Commentaires sur les items |
| **Report** | `reports` | id, reporter_id(FK), reported_user_id(FK), report_type, target_item_id(FK), reason(spam\|fake_data\|other), description, status(pending\|reviewed\|dismissed\|resolved), reviewed_by(FK) | Signalements modérés par l'admin |
| **DataChunk** | `data_chunks` | id, parent_item_id(FK), name, owner_user_id(FK), data_url, metadata_json(JSON) | Chunks de données uploadées |
| **UserUpload** | `user_uploads` | id, owner_user_id(FK), parent_item_id(FK), chunk_id(FK), file_name, file_size_bytes, mime_type, original_format, processing_status, error_message | Suivi des uploads utilisateurs |
| **VisualizationLink** | `visualization_links` | id, parent_item_id(FK), name, url, owner_user_id(FK), link_type(external\|internal\|embed\|widget), display_order, thumbnail_url, is_active | Liens de visualisation pour les items |

### Relations Principales

```
User ────→ OrganizationMember ←──── Organization
  │             │                      │
  │             └── (role: member/editor/admin/owner)
  │
  ├──→ Rating (1-n sur Item)
  ├──→ Comment (author_name only, pas FK user)
  ├──→ Report (reporter / reported_user)
  ├──→ DataChunk (owner)
  └──→ UserUpload (owner)

Item ────→ ItemTag (n-m via junction)
        ───→ ItemGallery (1-n)
        ───→ Rating (1-n)
        ───→ Comment (1-n)
        ───→ VisualizationLink (1-n)
        ───→ Report (target_item)
        ──── Organization (FK owner)
```

---

## Structure des Templates

```text
templates/
├── base.html                    # Template de base avec blocks (title, meta_description, content, extra_head, extra_scripts)
├── index.html                   # Page d'accueil (extends base.html)
├── catalogue.html               # Liste paginée filtrée par type et statut de vérification
├── item_detail.html             # Détail item : galerie inline, rating étoiles, commentaires, rapport
├── gallery.html                 # Galerie plein écran (Leaflet cartes interactives, viewer CSV, dashboards)
├── connexion.html               # Formulaire de login avec messages d'erreur
├── inscription.html             # Formulaire d'inscription avec validation de mot de passe en temps réel
├── contact.html                 # Page contact avec bouton copier email
├── organization_detail.html     # Page organisation : infos + items associés
└── partials/
│   ├── header.html              # Barre supérieure : logo, auth actions, recherche, navigation + org links
│   └── footer.html              # Pied de page : infos marque, liens nav, contact
└── admin/
    ├── users.html               # Liste utilisateurs avec ban/unban (admin only)
    └── reports.html             # Gestion signalements avec filtres (admin only)
```

---

## Architecture CSS

Approche **modulaire** avec separation en deux sous-répertoires :

### Primitives (`static/css/primitives/`)
- `buttons.css` — Boutons réutilisables (`.btn`, `.btn-outline`)
- `badges.css` — Badges et tags visuels

### Features (`static/css/features/`)
- `sections/attribution.css` — Section attribution (`.attribution-section`, `.attribution-card`, etc.)
- `sections/info.css` — Section informations (`.info-section`, `.info-card`, etc.)
- `sections/p2p.css` — Section P2P & résilience (timeline, avantages)
- `sections/geopackage.css` — Section GeoPackage Packs (collections, CTA)
- `sections/individual-data.css` — Section données individuelles (avantages, exemples)
- `sections/magnet.css` — Section Magnet/Torrent (étapes, liens magnétiques)
- `product.css` — Cards produit du catalogue
- `gallery-modal.css` — Galerie fullscreen, navigation images
- `ratings.css` — étoiles de notation (star rating)
- `comments.css` — Formulaire et liste de commentaires
- `technical.css` — Spécifications techniques des items

### Général
| Fichier | Rôle |
|---------|------|
| `style.css` | Point d'entrée — importe tous les modules CSS dans l'ordre |
| `base.css` | Variables CSS custom (`:root {}`), resets, typographie (Ubuntu + Ubuntu Mono) |
| `header.css` | Branding, navigation, barre de recherche |
| `hero.css` | Section héro : layout, panneau de statut, ligne d'actions |
| `components.css` | Composants utilitaires |
| `auth.css` | Layout et formulaires des pages auth |
| `services.css` | Grille de cartes du section miroirs |
| `footer.css` | Colonnes grille footer, barre inférieure |
| `responsive.css` | Breakpoints (980px tablette, 680px mobile) |

---

## JavaScript

Modules Vanilla JS encapsulés en IIFE :

| Fichier | Fonctionnalité |
|---------|---------------|
| `main.js` | Gestionnaire de recherche, bouton copier email, validation mot de passe côté client |
| `catalogue.js` | Expand/collapse description toggles dans le catalogue |
| `gallery/starRating.js` | Composant notation étoiles interactif |
| `gallery/imageModal.js` | Galerie plein écran avec navigation et modal |
| `gallery/inlineGallery.js` | Galerie inline (Leaflet cartes, CSV viewer, dashboards) |
| `gallery/copyMagnet.js` | Copier magnet link dans le presse-papier |
| `utils/clipboard.js` | Utilitaire clipboard générique |

---

## Scripts

| Script | Commande | Description |
|--------|----------|-------------|
| `setup.sh` | `./setup.sh` | Mode Docker : génère `.env` (credentials aléatoires 256 chars), construit et lance les conteneurs |
| `setup.sh` | `./setup.sh local` | Mode local : crée `.venv`, `.secret`, lance Flask dev server |
| `run.sh` | `./run.sh` | Lanceur dev (Flask dev server, port 5000) — nécessite `setup.sh local` d'abord |
| `build.sh` | `./build.sh` | Rebuild uniquement le conteneur Flask app (sans PostgreSQL) |

---

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **CSRF** | Activé globalement via Flask-WTF, exempté sur `/api/*` et `/health`. Rejet d'un token `X-CSRF-Token` pour les requêtes JSON API |
| **Rate limiting** | 5 req/heure sur `/connexion` (brute-force), 100/heure par défaut (Flask-Limiter) |
| **Headers** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff, HSTS max-age=31536000; includeSubDomains, CSP restreint (self + Google Fonts + unpkg + OpenStreetMap tiles) |
| **Cookies** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Session** | 30 minutes max (PERMANENT_SESSION_LIFETIME = 1800) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée via `secrets.token_hex(32)` en dev si absente ; erreur fatale en production |
| **Sanitisation** | `bleach.clean()` sur tout contenu utilisateur |
| **Uploads** | Validation magic bytes (contenu réel ≠ extension) + whitelist extensions |
| **URL validation** | `validate_external_url()` — bloqué les URL non sécurisées pour les liens de visualisation |
| **Permissions fichier** | `.secret` et `.env` en `0o600` |

---

## Tests

Suite de tests pytest dans `tests/` :
- `conftest.py` — Fixtures Flask test client, base de données test
- `test_routes.py` — Tests des routes (statut HTTP, templates renderés)
- `test_models.py` — Tests des modèles (champs, relations, validation)

Lancement : `pytest tests/`

---

## Déploiement Docker

```text
├── Dockerfile          # Python 3.12-slim → utilisateur appuser non-root → Gunicorn prod (3 workers)
├── .dockerignore       # Exclusions : .venv, __pycache__, .env, secrets, etc.
└── docker-compose.yml  # Orchestre app + postgres avec volumes nommés

services:
  app:     → image construite depuis Dockerfile (gunicorn sur port 5000)
  postgres → postgres:18-alpine sur port 5432, healthcheck via pg_isready

volumes:
  pg_data:       → persistance PostgreSQL dans /var/lib/postgresql/data
  secret_key:    → persistance du fichier .secret Flask entre les redémarrages
```

---

## Migrations

Alembic avec les versions actuelles :
1. `initial_schema` — Création des tables de base (users, organizations, items, tags)
2. `auth_interactions` — Ajout de ratings, commentaires, reports, et champs d'authentification

---

*Document généré automatiquement basé sur l'analyse du code source.*
