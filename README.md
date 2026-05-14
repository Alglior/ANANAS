# A.N.A.N.A.S.

**Atlas Numérique d'Archives de Nœuds et d'Accès Synchronisés** — Portail de services géospatiales basé sur les liens magnet et BitTorrent pour le partage de données géographiques. Développé avec Flask, ce projet fournit une interface web complète pour découvrir, consulter et gérer des données géospatiales via un catalogue structuré par organisations.

[Architecture →](ARCHITECTURE.md) — Vue détaillée du code, routes, sécurité et patterns architecturaux

## Fonctionnalités

- **Catalogue de données** — Géodonnées, cartes et applications géospatiales avec filtrage (vérifié/non-officiel, par organisation)
- **Authentification** — Inscription, connexion et sessions sécurisées (1h, HTTP-only, SameSite=Lax)
- **Organisations** — Création, adhésion, gestion des membres (member/editor/admin/owner)
- **Interactions** — Ratings étoiles (1-5), commentaires annotés, signalements, vérification d'items
- **Upload de fichiers** — Upload par chunks avec validation magic bytes (csv, shp, geojson, gpkg, json, xml)
- **Administration** — Panneau admin pour modération de signalements et gestion des utilisateurs (ban/unban)
- **Protection CSRF** — Globale via Flask-WTF, exemptée sur les routes `/api/*` et `/health`
- **Headers de sécurité** — CSP restreint, HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff
- **Rate limiting** — Protection brute-force (5 requêtes/heure sur connexion, 100/heure par défaut)
- **Sanitisation HTML** — Entrées utilisateur nettoyées via `bleach.clean()`

## Prérequis

**Docker mode (recommandé)** :
- Docker + Docker Compose v2

**Local mode (développement uniquement)** :
- Python 3.12+
- pip

```text
Flask == 3.1.0
Flask-WTF == 1.2.1
Flask-SQLAlchemy >= 3.1
Flask-Migrate >= 4.0
Flask-Limiter >= 3.0
python-dotenv == 1.0.1
psycopg2-binary >= 2.9
gunicorn == 23.0.0
bleach >= 6.0
pytest == 8.3.4
```

## Démarrage rapide

### Mode Docker (recommandé) — avec PostgreSQL 18

```bash
./setup.sh        # génère .env + construit + lance les conteneurs
docker compose logs -f  # suivre les logs
```

Cela démarre 2 conteneurs :
- `ananas_app` — Flask en production via Gunicorn (port 5000, 3 workers)
- `ananas_postgres` — PostgreSQL 18 Alpine (port 5432)

### Mode Local (développement uniquement)

```bash
./setup.sh local   # crée .venv + .secret + lance le serveur dev
```

Accessible sur `http://localhost:5000`

## Structure du projet

```text
app.py                   - Point d'entrée Flask (factory create_app(), route /health)
models.py                - Modèles SQLAlchemy (User, Organization, Item, Rating, Comment, etc.)
src/                     - Blueprints modulaires des routes
│   ├── __init__.py      - register_all_blueprints(), _register_view() helper
│   ├── auth_routes.py   - Connexion, inscription, logout + validation mot de passe
│   ├── catalogue_routes.py - Catalogues (donnees/cartes/applications), JSON API
│   ├── item_routes.py    - Détail item, galerie inline
│   ├── organization_routes.py - CRUD orgs, membres, rejoindre/quitter
│   ├── admin_routes.py   - Ban/unban, gestion des signalements
│   ├── upload_routes.py  - Upload chunké, validation magic bytes
│   ├── interactions.py   - Ratings, commentaires, vérification d'items
│   └── shared.py         - login_required, get_current_user, pagination, Config
utils/
│   └── security.py      - sanitize_html(), validate_external_url(), validate_file_magic()
templates/               - Templates Jinja2 avec héritage de base.html
static/                  - CSS (primitives/features), JS (IIFE modules)
alembic/                 - Migrations (initial_schema → auth_interactions)
tests/                   - pytest (test_routes.py, test_models.py, conftest.py)
scripts/seed_data.py     - Seed data pour l'environnement de développement
Dockerfile               - Image Python 3.12-slim, utilisateur non-root, Gunicorn prod
docker-compose.yml       - Orchestre app + postgres avec volumes nommés
setup.sh                 - Script unique : ./setup.sh (Docker) ou ./setup.sh local
run.sh                   - Lanceur dev local (Flask dev server, port 5000)
build.sh                 - Rebuild uniquement le conteneur Flask app
requirements.txt         - Dépendances Python
.env                     - Variables d'environnement (généré automatiquement, ignoré par Git)
.env.example             - Template pour personnalisation manuelle
.secret                  - Clé secrète Flask (permissions 0o600)
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

## Configuration

### `.secret` fichier

Fichier auto-généré contenant la clé secrète Flask :
```text
FLASK_SECRET_KEY=<valeur>
```
Généré automatiquement par `./setup.sh local`. Minimum 32 caractères requis. Permissions `0o600`.

### `.env` fichier

Contient les variables d'environnement PostgreSQL et Flask. Généré automatiquement par `./setup.sh` avec 256 caractères d'entropy cryptographique (`secrets.token_hex(128)`). Copié manuellement à partir de `.env.example` pour une configuration personnalisée :
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
./build.sh                      # rebuild uniquement le Flask app (sans PG)
```

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **CSRF** | Protection globale via Flask-WTF (`CSRFProtect(app)`), exemptée sur `/api/*` et `/health` |
| **Headers sécurité** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff, CSP restreint, HSTS (31536000s) |
| **Cookies de session** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Durée de session** | 30 minutes (`PERMANENT_SESSION_LIFETIME = 1800`) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée si absente ; erreur fatale en production |
| **Rate limiting** | 5 req/heure sur `/connexion`, 100/heure par défaut (Flask-Limiter) |
| **Sanitisation HTML** | `bleach.clean()` sur les contenus utilisateur |
| **Validation uploads** | Magic bytes + whitelist extensions (csv, shp, geojson, gpkg, json, xml) |
| **Permissions fichier** | `.secret` et `.env` en `0o600` (lecture/écriture propriétaire uniquement) |
| **Max upload** | 10 Mo (`MAX_CONTENT_LENGTH`) |

---

*Projet développé pour un mémoire M2.*
