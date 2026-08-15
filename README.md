# A.N.A.N.A.S.

**Atlas Numérique d'Archives de Nœuds et d'Accès Synchronisés** — Portail de services géospatiales basé sur les liens magnet et BitTorrent pour le partage de données géographiques. Développé avec Flask, ce projet fournit une interface web complète pour découvrir, consulter et gérer des données géospatiales via un catalogue structuré par organisations.

[Architecture →](ARCHITECTURE.md) — Vue détaillée du code, routes, sécurité et patterns architecturaux

## Fonctionnalités

- **Catalogue de données** — Géodonnées, cartes et applications géospatiales avec filtrage (vérifié/non-officiel, par organisation)
- **Authentification** — Inscription, connexion, sessions sécurisées (30min, HTTP-only, SameSite=Lax) et authentification à deux facteurs (2FA/TOTP)
- **Organisations** — Création, adhésion, gestion des membres (member/editor/admin/owner) avec rôles personnalisés
- **Interactions** — Ratings étoiles (1-5), commentaires threadés, signalements, vérification d'items
- **Upload de fichiers** — Upload par chunks avec validation magic bytes (csv, shp, geojson, gpkg, json, xml)
- **Score IMOD** — Indice de qualité composite (métadonnées 45%, technique 36%, richesse 19%) pour évaluer les items
- **Administration** — Panneau admin complet : modération, audit, tags, miroirs, featured items, geopackages, réplication, sauvegarde
- **Documentation intégrée** — Système de rendu Markdown pour la documentation du site
- **Pages légales** — Mentions légales, CGU, politique de confidentialité
- **Protection CSRF** — Globale via Flask-WTF, exemptée sur les routes `/api/*` et `/health`
- **Headers de sécurité** — CSP dynamique (nonce-based), HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff
- **Rate limiting** — Protection brute-force (5 requêtes/heure sur connexion, 100/heure par défaut) via Redis
- **Sanitisation HTML** — Entrées utilisateur nettoyées via `bleach.clean()`

## Prérequis

**Docker mode (recommandé)** :
- Docker + Docker Compose v2

**Local mode (développement uniquement)** :
- Python 3.12+
- pip

```text
Flask==3.1.0
Flask-WTF==1.2.1
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Limiter==3.6.0
python-dotenv==1.0.1
psycopg2-binary==2.9.9
gunicorn==23.0.0
bleach==6.1.0
mistune==3.0.2
pytest==8.3.4
requests==2.31.0
redis==5.2.1
pyotp==2.9.0
qrcode==7.4.2
Pillow==11.0.0
```

## Démarrage rapide

### Mode Docker (recommandé) — avec PostgreSQL 18

```bash
./setup.sh        # génère .env + credentials admin + construit + lance les conteneurs
docker compose logs -f  # suivre les logs
```

Cela démarre 5 conteneurs :
- `ananas_nginx` — Reverse proxy Nginx (port 80)
- `ananas_app` — Flask en production via Gunicorn (port 5000, 3 workers)
- `ananas_postgres` — PostgreSQL 18 Alpine (port 5432)
- `ananas_redis` — Redis pour le rate limiting
- `ananas_qbittorrent` — Client torrent pour le téléchargement d'images via magnet

### Mode Local (développement uniquement)

```bash
./setup.sh local   # crée .venv + .secret + lance le serveur dev
```

Accessible sur `http://localhost:5000`

## Structure du projet

```text
app.py                   - Point d'entrée Flask (factory create_app(), route /health)
models.py                - Modèles SQLAlchemy (20 modèles : User, Organization, Item, Rating, Comment, etc.)
src/                     - Blueprints modulaires des routes (14 blueprints)
│   ├── __init__.py      - register_all_blueprints(), _register_view() helper
│   ├── auth_routes.py   - Connexion, inscription, logout + validation mot de passe
│   ├── catalogue_routes.py - Catalogues (donnees/cartes/applications), JSON API
│   ├── item_routes.py    - Détail item, galerie inline
│   ├── organization_routes.py - CRUD orgs, membres, rejoindre/quitter
│   ├── user_routes.py   - Profil, compte, upload, 2FA, avatars, brouillons
│   ├── contact_routes.py - Formulaire de contact
│   ├── privacy_routes.py - Politique de confidentialité
│   ├── legal_routes.py   - Mentions légales
│   ├── tos_routes.py     - Conditions d'utilisation
│   ├── doc_routes.py     - Documentation intégrée (rendu Markdown)
│   ├── index_routes.py   - Route d'accueil dynamique
│   ├── api_docs.py       - Documentation interactive de l'API REST
│   ├── interactions.py   - Ratings, commentaires threadés, vérification d'items
│   ├── shared.py         - login_required, get_current_user, pagination, Config
│   ├── image_cache.py    - Téléchargement asynchrone d'images via magnet/qBittorrent
│   └── admin/            - Package admin modulaire (14 sous-modules)
│       ├── __init__.py   - Helpers, serializers, catalogue config
│       ├── users.py      - Ban/unban/mute/warn/kick
│       ├── reports.py    - Signalements
│       ├── pages.py      - Routes pages admin
│       ├── content.py    - Modération commentaires/items
│       ├── audit.py      - Journal d'audit
│       ├── contact.py    - Messages de contact
│       ├── mirrors.py    - Sites miroirs
│       ├── featured.py   - Données en avant
│       ├── geopackages.py - Packs GeoPackage
│       ├── catalogues.py - Activation/désactivation catalogues
│       ├── replication.py - Réplication de catalogue distant
│       ├── backup.py     - Sauvegarde/restauration DB
│       ├── tags.py       - Tags prédéfinis
│       ├── simple_files.py - Fichiers simples
│       └── settings.py   - Paramètres globaux du site
utils/
│   ├── security.py       - sanitize_html(), validate_external_url(), validate_magnet_link(), sanitize_value(), sanitize_gallery_data(), validate_filename()
│   └── email.py          - Envoi d'emails SMTP
templates/                - Templates Jinja2 avec héritage de base.html (46 templates)
static/                   - CSS modulaire (primitives/features), JS (49 fichiers en modules IIFE)
alembic/                  - Migrations (32 versions)
tests/                    - pytest (test_routes.py, test_models.py, conftest.py)
scripts/seed_data.py      - Seed data pour l'environnement de développement
Dockerfile                - Image Python 3.12-slim multi-stage (base/test/production), Gunicorn prod
docker-compose.yml        - Orchestre 5 services (nginx, app, postgres, redis, qbittorrent)
docker-entrypoint.sh      - Script de démarrage (attente PG, création admin, config qBittorrent)
setup.sh                  - Script unique : ./setup.sh (Docker) ou ./setup.sh local
run.sh                    - Lanceur dev local (Flask dev server, port 5000)
build.sh                  - Rebuild tous les services Docker
requirements.txt          - Dépendances Python (16 packages)
.env                      - Variables d'environnement (généré automatiquement, ignoré par Git)
.env.example              - Template pour personnalisation manuelle
.secret                   - Clé secrète Flask (permissions 0o600)
```

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | Nom de la base PostgreSQL |
| `POSTGRES_USER` | Utilisateur PostgreSQL (généré aléatoirement par défaut) |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL (généré aléatoirement par défaut) |
| `FLASK_SECRET_KEY` | Clé secrète Flask pour CSRF/sessions (minimum 32 caractères crypto) |
| `FLASK_DEBUG` | `true`/`1` pour activer le mode debug |
| `POSTGRES_HOST` | Hôte PostgreSQL (défaut : `postgres`) |
| `ADMIN_PSEUDO` | Pseudo du compte admin (auto-généré par setup.sh) |
| `ADMIN_PASSWORD` | Mot de passe du compte admin (auto-généré par setup.sh) |
| `QBITTORRENT_URL` | URL du serveur qBittorrent (défaut : `http://qbittorrent:8081`) |
| `QBITTORRENT_USERNAME` | Utilisateur qBittorrent (défaut : `admin`) |
| `QBITTORRENT_PASSWORD` | Mot de passe qBittorrent (auto-généré par setup.sh) |
| `REDIS_URL` | URL Redis pour le rate limiting (défaut : `redis://redis:6379/0`) |
| `DB_SSL_ROOT_CERT` | Certificat racine SSL PostgreSQL (optionnel) |
| `DB_SSL_CERT` | Certificat client SSL PostgreSQL (optionnel, mTLS) |
| `DB_SSL_KEY` | Clé client SSL PostgreSQL (optionnel, mTLS) |

## Configuration

### `.secret` fichier

Fichier auto-généré contenant la clé secrète Flask :
```text
FLASK_SECRET_KEY=<valeur>
```
Généré automatiquement par `./setup.sh local`. Minimum 32 caractères requis. Permissions `0o600`.

### `.env` fichier

Contient les variables d'environnement PostgreSQL, Flask, qBittorrent et admin. Généré automatiquement par `./setup.sh` avec 256 caractères d'entropy cryptographique (`secrets.token_hex(128)`) et credentials admin/qBittorrent. Copié manuellement à partir de `.env.example` pour une configuration personnalisée :
```bash
cp .env.example .env   # puis modifier les valeurs
```

## Démarrage avancé

```bash
docker compose up -d            # démarrer tous les services
docker compose down             # arrêter + supprimer conteneurs
docker compose logs -f          # suivre les logs en temps réel
docker compose exec app bash    # shell dans le conteneur app
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB  # accéder à Postgres
./build.sh                      # rebuild tous les services Docker
```

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **CSRF** | Protection globale via Flask-WTF (`CSRFProtect(app)`), exemptée sur `/api/*` et `/health` |
| **Headers sécurité** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff, CSP dynamique (nonce-based), HSTS (31536000s) |
| **Cookies de session** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Durée de session** | 30 minutes (`PERMANENT_SESSION_LIFETIME = 1800`) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée si absente ; erreur fatale en production |
| **Rate limiting** | 5 req/heure sur `/connexion`, 100/heure par défaut (Flask-Limiter + Redis) |
| **2FA/TOTP** | Authentification à deux facteurs optionnelle avec codes de récupération |
| **Sanitisation HTML** | `bleach.clean()` sur les contenus utilisateur |
| **Validation uploads** | Magic bytes + whitelist extensions (csv, shp, geojson, gpkg, json, xml) |
| **Permissions fichier** | `.secret` et `.env` en `0o600` (lecture/écriture propriétaire uniquement) |
| **Max upload** | 10 Mo (`MAX_CONTENT_LENGTH`) |

---

*Projet développé pour un mémoire M2.*
