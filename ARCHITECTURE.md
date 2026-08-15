# Architecture du Projet A.N.A.N.A.S.

## Vue d'ensemble

**A.N.A.N.A.S.** est un portail de services de données géospatiales qui distribue des données géographiques via magnet links et le protocole BitTorrent. C'est une application web Flask avec une architecture modulaire basée sur les blueprints, utilisant PostgreSQL 18 comme base de données relationnelle.

L'application supporte l'authentification avec 2FA, la gestion d'organisations avec rôles personnalisés, les interactions utilisateurs (ratings, commentaires threadés, signalements), un score de qualité IMOD, et un panneau d'administration complet. Elle est déployable via Docker avec 5 services (Nginx, Flask, PostgreSQL, Redis, qBittorrent) ou en mode local avec Flask dev server.

---

## Stack Technique

| Couche | Technologie |
|--------|-------------|
| Framework Web | Flask 3.1.0 (Python) |
| ORM | SQLAlchemy 2.x (via Flask-SQLAlchemy 3.1.1) |
| Migrations | Alembic (via Flask-Migrate 4.0.5) |
| Moteur de templates | Jinja2 avec héritage `base.html` |
| Rendu Markdown | mistune 3.0.2 |
| Serveur de production | Gunicorn 23.0.0 (3 workers, timeout 30s) |
| Base de données | PostgreSQL 18 Alpine |
| Cache/Rate limiting | Redis 7 Alpine |
| Client torrent | qBittorrent (téléchargement images via magnet) |
| Reverse proxy | Nginx 1.27 Alpine |
| Sécurité | Flask-WTF (CSRF), Flask-Limiter 3.6.0 (rate limiting), bleach 6.1.0 (sanitisation) |
| 2FA | pyotp 2.9.0 (TOTP), qrcode 7.4.2 (génération QR codes) |
| Images | Pillow 11.0.0 (conversion favicon, traitement images) |
| CSS | Vanilla CSS modulaire — primitives/ et features/ |
| JavaScript | Vanilla JS en modules IIFE (49 fichiers) |
| Containerisation | Docker + Docker Compose (Python 3.12-slim, multi-stage, utilisateur non-root `appuser`) |

---

## Architecture de l'Application

### Pattern Factory

L'application utilise le pattern **Factory** via `create_app()` dans `app.py` :
- Crée l'instance Flask, charge la configuration depuis `.secret` + variables d'environnement
- Configure SQLAlchemy et Alembic Migrate
- Applique les headers de sécurité (`after_request`) avec CSP nonce-based dynamique
- Configure les cookies de session (HTTP-only, SameSite=Lax)
- Initialise CSRFProtect avec exemptions pour `/api/*` et `/health`
- Installe le rate limiter (Flask-Limiter + Redis)
- Enregistre dynamiquement les routes statiques via `_register_view()` helper
- Enregistre tous les blueprints modulaires (14 blueprints)

### Structure Modulaire (Blueprints)

Le code est organisé en **14 blueprints** répartis dans `src/` :

| Blueprint | Fichier | Routes principales | Responsable |
|-----------|---------|--------------------|-------------|
| `auth` | `src/auth_routes.py` | `/connexion`, `/inscription`, `/logout` | Authentification, validation mot de passe |
| `catalogue` | `src/catalogue_routes.py` | `/catalogue/{donnees\|cartes\|applications}`, JSON API | Filtrage paginé avec convertisseur `CatalogueTypeConverter` |
| `items` | `src/item_routes.py` | `/catalogue/item/<id>`, galerie, téléchargement magnets | Détail d'item, galerie inline, zoom magnets, favicon |
| `organizations` | `src/organization_routes.py` | `/api/organizations`, `/organizations/<slug>` | CRUD orgs, membres, API |
| `interactions` | `src/interactions.py` | `/catalogue/item/<id>/rate`, `/comment`, vérification | Ratings (1-5), commentaires threadés, verification d'items |
| `users` | `src/user_routes.py` | `/compte`, `/upload`, `/api/users/2fa/*` | Profil, compte, upload, 2FA, avatars, brouillons |
| `admin` | `src/admin/` (package) | `/admin/*`, `/api/admin/*` | Package modulaire (14 sous-modules) |
| `contact` | `src/contact_routes.py` | `/contact` | Formulaire de contact |
| `privacy` | `src/privacy_routes.py` | `/confidentialite` | Politique de confidentialité |
| `legal` | `src/legal_routes.py` | `/mentions-legales` | Mentions légales |
| `tos` | `src/tos_routes.py` | `/cgu` | Conditions d'utilisation |
| `doc` | `src/doc_routes.py` | `/doc/*` | Documentation intégrée (rendu Markdown) |
| `api_docs` | `src/api_docs.py` | `/api` | Documentation interactive de l'API REST |
| `index` | `src/index_routes.py` | `/` | Route d'accueil dynamique (mirrors, featured, geopackages) |

### Package Admin (`src/admin/`)

L'administration est un package modulaire composé de **14 sous-fichiers** :

| Module | Fichier | Responsable |
|--------|---------|-------------|
| Init | `src/admin/__init__.py` | Helpers, serializers, catalogue config |
| Users | `src/admin/users.py` | Ban/unban/mute/warn/kick |
| Reports | `src/admin/reports.py` | Signalements |
| Pages | `src/admin/pages.py` | Routes pages admin |
| Content | `src/admin/content.py` | Modération commentaires/items |
| Audit | `src/admin/audit.py` | Journal d'audit |
| Contact | `src/admin/contact.py` | Messages de contact |
| Mirrors | `src/admin/mirrors.py` | Sites miroirs |
| Featured | `src/admin/featured.py` | Données en avant |
| GeoPackages | `src/admin/geopackages.py` | Packs GeoPackage |
| Catalogues | `src/admin/catalogues.py` | Activation/désactivation catalogues |
| Replication | `src/admin/replication.py` | Réplication de catalogue distant |
| Backup | `src/admin/backup.py` | Sauvegarde/restauration DB |
| Tags | `src/admin/tags.py` | Tags prédéfinis |
| Simple Files | `src/admin/simple_files.py` | Fichiers simples |
| Settings | `src/admin/settings.py` | Paramètres globaux du site |

### Fichiers Partagés

- **`src/shared.py`** — Decorator `@login_required`, helper `get_current_user()`, pagination (`_build_page_numbers()`), configuration (`Config.validate()`)
- **`src/image_cache.py`** — Téléchargement asynchrone d'images via magnet/qBittorrent
- **`utils/security.py`** — `sanitize_html()`, `validate_external_url()`, `validate_magnet_link()`, `sanitize_value()`, `sanitize_gallery_data()`, `validate_filename()`
- **`utils/email.py`** — Envoi d'emails SMTP

---

## Routes / Endpoints

### Public

| Méthode | URL | Endpoint | Template/API | Description |
|---------|-----|----------|-------------|-------------|
| GET | `/` | `home` | `index.html` | Page d'accueil dynamique |
| GET | `/contact` | `contact` | `contact.html` | Page contact |
| GET | `/mentions-legales` | `legal` | `legal.html` | Mentions légales |
| GET | `/cgu` | `tos` | `tos.html` | Conditions d'utilisation |
| GET | `/confidentialite` | `privacy` | `privacy.html` | Politique de confidentialité |
| GET | `/doc` | `doc.index` | `doc_index.html` | Documentation |
| GET | `/doc/<slug>` | `doc.page` | `doc.html` | Page de documentation |
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
| GET | `/organizations` | `org.organization_list_view` | `organization_list.html` | Liste des organisations |
| GET | `/organizations/<slug>` | — | `organization_detail.html` | Page d'une organisation |
| GET | `/organizations/<slug>/items` | `org.organization_items_view` | `organization_detail.html` | Items d'une organisation |
| GET | `/compte` | `users.account_page` | `users/compte.html` | Page compte utilisateur |
| GET | `/health` | `health_check` | JSON | Health check |

### Auth POST

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/connexion` | Login (5 req/heure rate limit) |
| POST | `/connexion/2fa` | Vérification code 2FA |
| POST | `/inscription` | Inscription avec validation mot de passe complexe |

### API Utilisateurs

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/users/2fa/setup` | Initialiser le setup TOTP |
| POST | `/api/users/2fa/enable` | Activer la 2FA |
| POST | `/api/users/2fa/disable` | Désactiver la 2FA |
| POST | `/api/users/generate-recovery-codes` | Générer des codes de récupération |

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
| GET | `/admin/moderation` | Modération commentaires/items |
| GET | `/admin/audit` | Journal d'audit |
| GET | `/admin/settings` | Paramètres globaux |
| GET | `/admin/mirrors` | Sites miroirs |
| GET | `/admin/featured` | Données en avant |
| GET | `/admin/geopackages` | Packs GeoPackage |
| GET | `/admin/catalogues` | Activation/désactivation catalogues |
| GET | `/admin/tags` | Tags prédéfinis |
| GET | `/admin/replication` | Réplication de catalogue |
| GET | `/admin/backup` | Sauvegarde/restauration |
| GET | `/admin/contact-messages` | Messages de contact |
| GET | `/api/admin/reports` | API signalements (filtrage) |
| POST | `/api/admin/reports/<id>/resolve` | Résoudre un signalement |
| POST | `/api/users/<id>/ban` | Bannir/unban un utilisateur |
| GET | `/api/users/banned` | Liste des utilisateurs bannis |
| POST | `/api/admin/settings/update` | Mettre à jour les paramètres |
| POST | `/api/admin/settings/logo-upload` | Upload logo du site |
| POST | `/api/admin/comments/<id>` | Modérer un commentaire |
| POST | `/api/admin/mirrors` | CRUD miroirs |
| POST | `/api/admin/featured` | CRUD featured items |
| POST | `/api/admin/geopackages` | CRUD geopackages |
| POST | `/api/admin/catalogues/<type>/toggle` | Activer/désactiver un catalogue |
| POST | `/api/admin/tags` | CRUD tags |
| POST | `/api/admin/replication/fetch` | Récupérer un catalogue distant |
| POST | `/api/admin/backup/download` | Télécharger une sauvegarde |
| POST | `/api/admin/backup/restore` | Restaurer une sauvegarde |
| POST | `/api/admin/home-sections` | CRUD sections d'accueil |
| POST | `/api/admin/simple-files` | CRUD fichiers simples |
| POST | `/api/admin/contact-messages/<id>/read` | Marquer un message comme lu |

---

## Modèles de Données (SQLAlchemy)

20 modèles relationnels dans `models.py` :

| Modèle | Table | Champs Clés | Description |
|--------|-------|-------------|-------------|
| **User** | `users` | id, prenom, nom, pseudo(unique), password_hash, avatar_path, is_active, banned, is_admin, muted_until, warned, warnings, session_version, totp_secret, totp_enabled, recovery_codes_hash, created_at | Utilisateurs authentifiés |
| **Organization** | `organizations` | id, name, slug(unique), description, logo_url, website_url, created_by, is_active, created_at | Structures qui publient des données |
| **OrganizationMember** | `organization_members` | id, user_id(FK), organization_id(FK), role(member\|moderator\|editor\|admin\|owner), custom_role_id(FK), joined_at, is_active | Appartenance utilisateur → organisation |
| **OrganizationRole** | `organization_roles` | id, organization_id(FK), name, permissions(JSON), created_at | Rôles personnalisés par organisation |
| **Item** | `items` | id, type(geodonnee\|carte\|application), title, description, format_type, magnet_link, image_path, owner_user_id(FK), author_name, organization_id(FK), verification_status, data_format_level(individual\|simple\|pack), pdf_magnet_link, status(published\|draft\|trashed), deleted_at, license_type, image_magnets_pending, image_magnets_total, image_magnet_links(JSON), metadata_json(JSON), verifier_user_id(FK), verified_at, verification_notes, created_at | Données géospatiales du catalogue |
| **ItemTag** | `item_tags` | id, item_id(FK), tag | Tags associés aux items |
| **ItemGallery** | `item_gallery` | id, item_id(FK), media_type(image\|csv\|dashboard\|interactive_map), src, data_json(JSON), label | Galerie inline des items |
| **Rating** | `ratings` | id, item_id(FK), user_id(FK), rating(float 1-5) | Notes utilisateurs sur les items |
| **Comment** | `comments` | id, item_id(FK), user_id(FK), parent_id(FK), author_name, content, created_at | Commentaires threadés sur les items |
| **DataChunk** | `data_chunks` | id, parent_item_id(FK), name, owner_user_id(FK), description, format_type, magnet_link, organization_id(FK), data_url, metadata_json(JSON), upload_status, published_at, created_at | Chunks de données uploadées |
| **UserUpload** | `user_uploads` | id, owner_user_id(FK), parent_item_id(FK), chunk_id(FK), file_name, file_size_bytes, mime_type, original_format, uploaded_at, processing_status, error_message, organization_id(FK), published_item_id(FK) | Suivi des uploads utilisateurs |
| **VisualizationLink** | `visualization_links` | id, parent_item_id(FK), name, url, owner_user_id(FK), link_type(external\|internal\|embed\|widget), display_order, description, thumbnail_url, is_active, created_at | Liens de visualisation pour les items |
| **Report** | `reports` | id, reporter_id(FK), reported_user_id(FK), report_type, target_item_id(FK), reason(spam\|fake_data\|other), description, status(pending\|reviewed\|dismissed\|resolved), reviewed_by(FK), reviewed_at, created_at | Signalements modérés par l'admin |
| **AdminAudit** | `admin_audit` | id, admin_user_id(FK), action_type, target_type, target_id, details(JSON), created_at | Journalisation des actions admin |
| **ContactMessage** | `contact_messages` | id, name, email, subject, message, is_read, created_at | Messages de contact |
| **MirrorSite** | `mirror_sites` | id, name, url, description, display_order, is_active, created_at | Sites miroirs |
| **FeaturedItem** | `featured_items` | id, item_id(FK), display_order, is_active, created_at | Données en avant sur la page d'accueil |
| **SimpleFileItem** | `simple_file_items` | id, item_id(FK), display_order, is_active, created_at | Fichiers simples |
| **PredefinedTagCategory** | `predefined_tag_categories` | id, name(unique), display_order, created_at | Catégories de tags prédéfinis |
| **PredefinedTag** | `predefined_tags` | id, category_id(FK), name, display_order, created_at | Tags prédéfinis |
| **CatalogueConfig** | `catalogue_config` | id, catalogue_type(unique), enabled | Activation/désactivation des catalogues |
| **SiteSetting** | `site_settings` | id, key(unique), value | Paramètres globaux du site (clé/valeur) |
| **GeoPackage** | `geo_packages` | id, title, description, format_info, link_url, display_order, is_active, created_at | Packs GeoPackage |

### Score IMOD

Le modèle `Item` contient une méthode `_compute_imod_score()` qui calcule un **score de qualité composite** :

| Dimension | Poids | Critères |
|-----------|-------|----------|
| **Métadonnées** | 45% | Description (0-2pts), tags (0-2pts), licence (0-2pts), auteur (0-1pt), organisation (0-1pt), PDF (0-2pts) |
| **Technique** | 36% | Format type (0-2pts), magnet valide (0-2pts), niveau de format (0-3pts) |
| **Richesse** | 19% | Galerie (0-3pts), liens visualisation (0-2pts), ratings (0-2pts), commentaires (0-2pts), images magnet (0-1pt) |

Bonus : +20 pts si l'item est vérifié par un admin. Seuils : Élevé ≥70, Moyen ≥40, Faible <40.

### Relations Principales

```
User ────→ OrganizationMember ←──── Organization
  │             │                      │
  │             ├── (role: member/editor/admin/owner)
  │             └── (custom_role_id → OrganizationRole)
  │
  ├──→ Rating (1-n sur Item)
  ├──→ Comment (1-n, threadés via parent_id)
  ├──→ Report (reporter / reported_user)
  ├──→ DataChunk (owner)
  ├──→ UserUpload (owner)
  └──→ comments (backref)

Item ────→ ItemTag (n-m via junction)
        ───→ ItemGallery (1-n)
        ───→ Rating (1-n)
        ───→ Comment (1-n, threadés)
        ───→ VisualizationLink (1-n)
        ───→ Report (target_item)
        ───→ DataChunk (1-n, pour level downloads)
        ───→ Organization (FK owner)
        ───→ _compute_imod_score() (score qualité)

Organization ───→ OrganizationMember (1-n)
             ───→ OrganizationRole (1-n)

AdminAudit ───→ User (admin_user_id)
ContactMessage ──── (standalone)
MirrorSite ──── (standalone)
FeaturedItem ───→ Item
SimpleFileItem ───→ Item
PredefinedTagCategory ───→ PredefinedTag (1-n)
CatalogueConfig ──── (standalone)
SiteSetting ──── (standalone)
GeoPackage ──── (standalone)
```

---

## Structure des Templates

```text
templates/
├── base.html                    # Template de base avec blocks (title, meta_description, content, extra_head, extra_scripts)
├── auth_base.html               # Template de base pour les pages d'auth
├── index.html                   # Page d'accueil (extends base.html)
├── catalogue.html               # Liste paginée filtrée par type et statut de vérification
├── item_detail.html             # Détail item : galerie inline, rating étoiles, commentaires, rapport
├── gallery.html                 # Galerie plein écran (Leaflet cartes interactives, viewer CSV, dashboards)
├── connexion.html               # Formulaire de login avec messages d'erreur
├── connexion_2fa.html           # Formulaire de vérification 2FA
├── inscription.html             # Formulaire d'inscription avec validation de mot de passe en temps réel
├── contact.html                 # Page contact avec bouton copier email
├── organization_detail.html     # Page organisation : infos + items associés
├── organization_list.html       # Liste des organisations
├── api_docs.html                # Documentation interactive de l'API
├── legal.html                   # Mentions légales
├── tos.html                     # Conditions d'utilisation
├── privacy.html                 # Politique de confidentialité
├── doc_index.html               # Index de la documentation
├── doc.html                     # Page de documentation (rendu Markdown)
├── base_admin.html              # Template de base pour les pages admin
├── partials/
│   ├── header.html              # Barre supérieure : logo, auth actions, recherche, navigation + org links
│   ├── footer.html              # Pied de page : infos marque, liens nav, contact
│   ├── admin_nav.html           # Navigation admin
│   ├── auth_page.html           # Layout pages auth
│   ├── comment_thread.html      # Thread de commentaires
│   ├── catalogue_item.html      # Card d'item dans le catalogue
│   ├── pagination.html          # Composant pagination
│   └── viz_links.html           # Liens de visualisation
├── users/
│   ├── upload.html              # Formulaire d'upload
│   ├── compte.html              # Page compte utilisateur
│   ├── brouillons.html          # Brouillons d'items
│   └── public_profile.html      # Profil public d'un utilisateur
└── admin/
    ├── users.html               # Liste utilisateurs avec ban/unban (admin only)
    ├── reports.html             # Gestion signalements avec filtres (admin only)
    ├── moderation.html          # Modération commentaires/items
    ├── audit.html               # Journal d'audit
    ├── settings.html            # Paramètres globaux
    ├── mirrors.html             # Sites miroirs
    ├── featured.html            # Données en avant
    ├── geopackages.html         # Packs GeoPackage
    ├── catalogues.html          # Activation/désactivation catalogues
    ├── replication.html         # Réplication de catalogue
    ├── backup.html              # Sauvegarde/restauration
    ├── tags.html                # Tags prédéfinis
    ├── home_section_blocks.html # Sections d'accueil
    └── contact_messages.html    # Messages de contact
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

Modules Vanilla JS encapsulés en IIFE (49 fichiers) :

| Module | Fonctionnalité |
|--------|---------------|
| `app.js` | Point d'entrée/orchestrateur |
| `csrf.js` | Gestion CSRF |
| `main.js` | Gestionnaire de recherche, bouton copier email, validation mot de passe côté client |
| `catalogue.js` | Expand/collapse description toggles + filtre par catégorie |
| `gallery/starRating.js` | Composant notation étoiles interactif |
| `gallery/imageModal.js` | Galerie plein écran avec navigation et modal |
| `gallery/inlineGallery.js` | Galerie inline (Leaflet cartes, CSV viewer, dashboards) |
| `gallery/copyMagnet.js` | Copier magnet link dans le presse-papier |
| `gallery/reportModal.js` | Modal de signalement |
| `item/detail.js` | Détail item (onglets, réponses, scroll) |
| `item/zoom-magnets.js` | Navigation magnets par zoom level |
| `auth/connexion.js` | Authentification |
| `users/compte.js` | Gestion compte utilisateur |
| `organizations/detail.js` | Détail organisation |
| `organizations/list.js` | Liste organisations |
| `pages/api-docs.js` | Recherche/filtrage API docs |
| `pages/contact.js` | Formulaire contact |
| `upload/*.js` | 13 modules pour le formulaire d'upload complet |
| `admin/*.js` | 15 modules pour l'interface administration |
| `utils/clipboard.js` | Utilitaire clipboard générique |
| `utils/pagination.js` | Pagination côté client |

---

## Scripts

| Script | Commande | Description |
|--------|----------|-------------|
| `setup.sh` | `./setup.sh` | Mode Docker : génère `.env` (credentials aléatoires 256 chars), credentials admin/qBittorrent, construit et lance les 5 conteneurs |
| `setup.sh` | `./setup.sh local` | Mode local : crée `.venv`, `.secret`, lance Flask dev server |
| `run.sh` | `./run.sh` | Lanceur dev (Flask dev server, port 5000) — nécessite `setup.sh local` d'abord |
| `build.sh` | `./build.sh` | Rebuild tous les services Docker (`docker compose up -d --build`) |
| `docker-entrypoint.sh` | — | Script de démarrage conteneur (attente PG, création tables, config admin/qBittorrent) |

---

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **CSRF** | Activé globalement via Flask-WTF, exempté sur `/api/*` et `/health` |
| **Rate limiting** | 5 req/heure sur `/connexion` (brute-force), 100/heure par défaut (Flask-Limiter + Redis) |
| **Headers** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff, HSTS max-age=31536000; includeSubDomains, CSP dynamique (nonce-based) |
| **Cookies** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Session** | 30 minutes max (PERMANENT_SESSION_LIFETIME = 1800) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée via `secrets.token_hex(32)` en dev si absente ; erreur fatale en production |
| **2FA/TOTP** | Authentification à deux facteurs optionnelle avec pyotp, QR codes, codes de récupération |
| **Sanitisation** | `bleach.clean()` sur tout contenu utilisateur |
| **Uploads** | Validation magic bytes (contenu réel ≠ extension) + whitelist extensions |
| **URL validation** | `validate_external_url()` — bloqué les URL non sécurisées pour les liens de visualisation |
| **Magnet validation** | `validate_magnet_link()` — validation des liens magnet |
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
├── Dockerfile          # Python 3.12-slim multi-stage (base/test/production), utilisateur appuser non-root, Gunicorn prod
├── .dockerignore       # Exclusions : .venv, __pycache__, .env, secrets, etc.
├── docker-compose.yml  # Orchestre 5 services
├── docker-entrypoint.sh # Script de démarrage conteneur
└── nginx/              # Configuration Nginx reverse proxy

services:
  nginx      → nginx:1.27-alpine, reverse proxy (port 80), dépend de app (healthy)
  app        → image construite depuis Dockerfile (gunicorn sur port 5000, interne uniquement)
  postgres   → postgres:18-alpine (port 5432, healthcheck via pg_isready)
  redis      → redis:7-alpine (rate limiting, 64mb max, LRU)
  qbittorrent → linuxserver/qbittorrent (téléchargement images via magnet, WebUI port 8081)

volumes:
  pg_data:                → persistance PostgreSQL dans /var/lib/postgresql
  qbittorrent_downloads:  → persistance téléchargements qBittorrent
  image_cache:            → cache d'images téléchargées
```

---

## Migrations

Alembic avec les versions actuelles (32 migrations) :
1. `initial_schema` — Création des tables de base (users, organizations, items, tags)
2. `auth_interactions` — Ajout de ratings, commentaires, reports, et champs d'authentification
3. ... (30 migrations supplémentaires couvrant l'ajout de 2FA, score IMOD, admin audit, etc.)

---

*Document généré automatiquement basé sur l'analyse du code source.*
