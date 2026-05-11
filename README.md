# A.N.A.N.A.S.

Un portail de services géospatiaux basé sur des liens magnet et torrent pour le partage de données géographiques. Développé avec Flask, ce projet fournit une interface web pour accéder aux données géospatiales via des liens de téléchargement décentralisés.

## Fonctionnalités

- Distribution de données géographiques via liens magnet
- Pages d'inscription et d'authentification (non fonctionnelles — voir limitations)
- Formulaire de contact
- Catalogue paginé de données géospatiales avec galerie, viewer CSV et dashboards
- Protection CSRF (Flask-WTF)
- En-têtes de sécurité complets (CSP, X-Frame-Options DENY, etc.)
- Génération automatique sécurisée des clés secrètes

## Prérequis

**Docker mode (recommandé)** :
- Docker + Docker Compose v2

**Local mode (développement uniquement)** :
- Python 3.10+
- pip

```text
Flask == 3.1.0
Flask-WTF == 1.2.1
python-dotenv == 1.0.1
gunicorn == 23.0.0
```

## Démarrage rapide

### Mode Docker (recommandé) — avec PostgreSQL

```bash
./setup.sh        # génère .env + construit + lance les conteneurs
docker compose logs -f  # suivre les logs
```

Cela démarre 2 conteneurs :
- `ananas_app` — Flask en production via Gunicorn (port 5000)
- `ananas_postgres` — PostgreSQL 16 Alpine (port 5432)

### Mode Local (développement uniquement)

```bash
./setup.sh local   # crée .venv + .secret + lance le serveur dev
```

Accessible sur `http://localhost:5000`

## Structure du projet

```text
app.py               - Point d'entrée Flask unique (routes, factory create_app())
requirements.txt     - Dépendances Python
setup.sh             - Script unique : ./setup.sh (Docker) ou ./setup.sh local
run.sh              - Lanceur dev local (Flask dev server)
Dockerfile          - Image containerisée non-root (Python 3.12-slim + Gunicorn)
docker-compose.yml  - Orchestre app + postgres
.env                - Variables d'environnement (généré automatiquement, ignoré par Git)
.env.example        - Template pour personnalisation manuelle
.secret             - Clé secrète Flask (permissions 0o600)
.static/            - Ressources statiques (CSS modulaire, JS vanilla, images)
templates/          - Templates Jinja2 avec héritage de base.html
```

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | Nom de la base PostgreSQL |
| `POSTGRES_USER` | Utilisateur PostgreSQL (généré aléatoirement par défaut) |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL (généré aléatoirement par défaut) |
| `FLASK_SECRET_KEY` | Clé secrète Flask pour CSRF/sessions (256 chars crypto) |
| `FLASK_DEBUG` | `true`/`1` pour activer le mode debug |
| `FLASK_ENV` | `production` en mode Docker, non utilisé localement |

## Configuration

### .secret fichier

Fichier auto-généré contenant la clé secrète Flask :
```text
FLASK_SECRET_KEY=<valeur>
```
Généré automatiquement par `./setup.sh local`. Minimum 32 caractères requis. Permissions `0o600`.

### .env fichier

Contient les variables d'environnement PostgreSQL et Flask. Généré automatiquement par `./setup.sh` avec 256 caractères d'entropy cryptographique. Copié manuellement à partir de `.env.example` pour une configuration personnalisée :
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
```

## Structure du projet

```text
app.py               - Point d'entrée Flask unique (routes, factory create_app())
requirements.txt     - Dépendances Python
setup.sh             - Script unique : ./setup.sh (Docker) ou ./setup.sh local
run.sh              - Lanceur dev local (Flask dev server)
Dockerfile          - Image containerisée non-root (Python 3.12-slim + Gunicorn)
docker-compose.yml  - Orchestre app + postgres
.env                - Variables d'environnement (généré automatiquement, ignoré par Git)
.env.example        - Template pour personnalisation manuelle
.secret             - Clé secrète Flask (permissions 0o600)
static/             - Ressources statiques (CSS modulaire, JS vanilla, images)
templates/          - Templates Jinja2 avec héritage de base.html
```

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **CSRF** | Protéction globale via Flask-WTF (`CSRFProtect(app)`) |
| **Headers sécurité** | X-Frame-Options: DENY, X-Content-Type-Options: nosniff, CSP restreint, Referrer-Policy |
| **Cookies de session** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Durée de session** | 1 heure (`PERMANENT_SESSION_LIFETIME = 3600`) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée si absente ; erreur fatale en production |
| **Permissions fichier** | `.secret` et `.env` en `0o600` (lecture/écriture propriétaire uniquement) |

## Observations / Limitations Actuelles

1. **Aucune base de données** — toutes les données sont des données simulées (mock data) générées directement dans `app.py`. 200 items catalogue simulés.
2. **Pas d'authentification fonctionnelle** — formulaires POST pour login/inscription mais aucun handler implémenté (renvoie une erreur 405).
3. **Pas de recherche réelle** — la barre de recherche affiche une `alert()` JavaScript à la soumission.
4. **Aucun endpoint API** — tout est rendu côté serveur via Jinja2.
5. **Contenu en dur** — URLs des miroirs, email de contact et statistiques (seeders, torrents) sont fixes dans les templates.
6. **Structure unique** — tout réside dans `app.py`, pas de blueprints ni sous-modules.

---

*Projet développé pour un mémoire M2.*
