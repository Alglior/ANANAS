# Architecture du Projet A.N.A.N.A.S.

## Vue d'ensemble

**A.N.A.N.A.S.** est un portail de services de données géospatiales qui distribue des données géographiques via magnet links et le protocole BitTorrent. Il s'agit d'une application web Flask monolithique, entièrement en français, avec des pages d'authentification (login/inscription), une page de contact et une page d'accueil.

L'application est déployable localement ou via Docker avec PostgreSQL, chaque mode ayant ses propres scripts de configuration.

---

## Stack Technique

| Couche | Technologie |
|--------|-------------|
| Framework Web | Flask 3.1.0 (Python) |
| Moteur de templates | Jinja2 (intégré à Flask) avec héritage de templates |
| Serveur de production | Gunicorn 23.0.0 |
| Base de données | PostgreSQL 18 Alpine (Docker uniquement) |
| Configuration | python-dotenv, variables d'environnement, fichier `.secret` |
| Sécurité | Flask-WTF, CSP headers, cookie sécurisés |
| CSS | Vanilla CSS modulaire (variables custom `:root {}`) |
| JavaScript | Vanilla JS (aucune librairie/framework) |
| Polices | Google Fonts — Ubuntu + Ubuntu Mono |
| Containerisation | Docker + Docker Compose (Python 3.12-slim, utilisateur non-root) |

---

## Script de Démarrage

### `setup.sh` — Entrée unique

Script unique avec deux modes :

```bash
./setup.sh              # → Mode Docker : génère .env (256 chars entropy), construit et lance les conteneurs
./setup.sh local        # → Mode local : crée .venv, .secret, et lance Flask dev server
```

Génère automatiquement des identifiants cryptographiquement aléatoires (256 caractères hexadécimaux via `secrets.token_hex(128)`).

### `run.sh` — Développeur local uniquement

Lanceur minimaliste de Flask en mode développement :
- Vérifie `.secret` (doit exister, sinon erreur)
- Charge la clé secrète dans l'environnement
- Lance le serveur Flask dev sur port 5000

### Supprimé : `run_prod.sh`

Supprimé car redondant avec Docker — la production utilise Gunicorn via le conteneur Docker.

---

## Stack Containerisée

```text
├── Dockerfile          # Image Python 3.12-slim, utilisateur non-root 'appuser', Gunicorn prod
├── .dockerignore       # Exclusions : .venv, __pycache__, .env, secrets, etc.
└── docker-compose.yml  # Orchestre app + postgres avec volumes nommés

services:
  app:     → image construite (gunicorn sur port 5000)
  postgres → postgres:16-alpine sur port 5432

volumes:
  pg_data:       → persistance PostgreSQL dans /var/lib/postgresql/data
  secret_key:    → persistance du fichier .secret Flask entre les redémarrages
```

### Dockerfile — Détails

- **Base** : `python:3.12-slim` (Debian)
- **Utilisateur non-root** : `appuser` créé avant la copie du code, `chown -R /app` appliqué
- **Production par défaut** : `ENV FLASK_ENV=production`, pas de mode debug actif
- **Gunicorn** : 3 workers, timeout 30s, bind sur `0.0.0.0:5000`

---

## Pattern Architectural

Application **MVC simplifié** avec une structure aplatie :

- **Pas de modèle traditionnel** — pas d'ORM, pas de schéma de base de données (données simulées dans `app.py`)
- **Pattern Factory** — `create_app()` dans `app.py` pour la création de l'application
- **Enregistrement dynamique des routes** — les routes sont définies comme objets de données et enregistrées via `_register_view()`, sans décorateurs individuels
- **Contrôleur unique** — toute la logique backend réside dans `app.py` (pas de blueprints, pas de modules séparés)
- **Héritage de templates** — `base.html` → templates de page → `partials/header.html`, `partials/footer.html`

---

## Routes / Endpoints

Toutes les routes sont en **GET**, retournant des templates Jinja2 :

| URL | Endpoint | Template | Description |
|-----|----------|----------|-------------|
| `/` | `home` | `index.html` | Page d'accueil (hero, miroirs BitTorrent) |
| `/connexion` | `connexion` | `connexion.html` | Formulaire de connexion |
| `/inscription` | `inscription` | `inscription.html` | Formulaire d'inscription |
| `/contact` | `contact` | `contact.html` | Page contact (bouton copier email) |
| `/catalogue` | `catalogue` | `catalogue.html` | Liste paginée de données géospatiales (30 par page) |
| `/catalogue/<int:page>` | `catalogue_page` | `catalogue.html` | Page spécifique du catalogue |
| `/catalogue/item/<int:id>` | `item_detail` | `item_detail.html` | Détail d'un item avec galerie, rating, formulaire de commentaire |
| `/catalogue/item/<int:id>/gallery` | `item_gallery` | `gallery.html` | Galerie complète avec Leaflet (cartes interactives, viewer CSV, dashboards) |

> **Note :** Les formulaires POST pour connexion/inscription n'ont pas encore de handlers.

---

## Structure des Fichiers

```text
sitev2/
├── app.py                     # Fichier unique : routes + factory create_app()
├── requirements.txt           # Dépendances Python
├── setup.sh                   # Script unique d'installation (Docker ou local)
├── run.sh                     # Lancement développement local (Flask dev server, port 5000)
├── Dockerfile                 # Image containerisée non-root (Python 3.12-slim + Gunicorn)
├── .dockerignore              # Exclusions pour le build Docker
├── docker-compose.yml         # Orchestre app + postgres avec volumes nommés
├── .env                       # Variables d'environnement auto-générées (ignoré par Git)
├── .env.example               # Template pour configuration manuelle
├── .secret                    # Clé secrète Flask (permissions 0o600)
├── .secret.example            # Exemple de fichier secret
├── README.md                  # Documentation du projet
├── ARCHITECTURE.md            # Ce document
├── charte_graphique_m2.pdf    # Charte graphique M2
├── templates/                 # Templates Jinja2
│   ├── base.html              # Template de base avec blocks (title, meta_description, content, extra_head, extra_scripts)
│   ├── index.html             # Page d'accueil (extends base.html)
│   ├── connexion.html         # Page de connexion (extends base.html)
│   ├── inscription.html       # Page d'inscription (extends base.html)
│   ├── contact.html           # Page de contact (extends base.html)
│   └── partials/
│       ├── header.html        # Barre fixe supérieure : logo, boutons auth, recherche, navigation principale
│       └── footer.html        # Pied de page : infos marque, liens nav, contact, mentions légales
├── static/                    # Assets statiques
│   ├── css/
│   │   ├── style.css          # Fichier maître — importe tous les autres modules CSS
│   │   ├── base.css           # Variables root, resets, typographie, styles globaux
│   │   ├── header.css         # Branding barre supérieure, navigation, recherche
│   │   ├── hero.css           # Hero section : layout, panneau de statut, ligne d'actions
│   │   ├── components.css     # Composants réutilisables (boutons, tags, cartes)
│   │   ├── auth.css           # Mise en page et formulaires des pages d'authentification
│   │   ├── services.css       # Grille de cartes du section miroirs
│   │   ├── scroll.css         # Flèche de défilement animée
│   │   ├── footer.css         # Colonnes grille footer, barre inférieure, mentions légales
│   │   └── responsive.css     # Breakpoints responsives (980px, 680px)
│   ├── js/
│   │   ├── main.js            # Gestionnaire de recherche, bouton copier email, validation mot de passe
│   │   ├── catalogue.js       # Expand/collapse description toggles
│   │   └── gallery.js         # Image carousel, modal navigation, Leaflet maps, CSV/dashboards viewer
│   └── images/
│       ├── logo/ANANAS.png    # Logo PNG du projet (128x128)
│       └── gallery/           # SVGs map thumbnails (map-1.svg → map-5.svg)
├── .venv/                     # Environnement virtuel Python (ignoré par Git)
├── __pycache__/               # Cache Python (ignoré par Git)
└── .sonar/                    # Artifacts SonarQube d'analyse statique
```

---

## Héritage des Templates

Chaque page étend `base.html` et fournit un bloc `{% block content %}` personnalisé ainsi qu'un titre et une meta description :

```
base.html
├── index.html      → Hero + grille de miroirs BitTorrent
├── catalogue.html  → Liste paginée de données géospatiales avec filtres par tags/format
├── item_detail.html→ Détail d'item, galerie inline, rating étoiles, formulaire commentaire
├── gallery.html    → Galerie plein écran (Leaflet cartes interactives, viewer CSV, dashboards)
├── connexion.html  → Formulaire de login (email, mot de passe)
├── inscription.html→ Formulaire d'inscription (nom, email, mot de passe)
└── contact.html    → Page contact avec bouton copier l'email
```

Les composants `partials/header.html` et `partials/footer.html` sont inclus via `{% include %}` dans `base.html`.

---

## Architecture CSS

Approche **modulaire atomic** :

- `style.css` est le point d'entrée qui importe tous les modules CSS dans l'ordre
- Aucun préprocesseur CSS — CSS brut avec variables custom (`:root {}`)
- Séparation logique par fonctionnalité (header, hero, composants, auth, services, footer)
- `responsive.css` gère les breakpoints (980px pour tablette, 680px pour mobile)

---

## Sécurité

| Fonctionnalité | Détail |
|----------------|--------|
| **Protection CSRF** | Activée globalement via Flask-WTF (`CSRFProtect(app)`) |
| **Headers de sécurité** | Définis sur chaque réponse : `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Content-Security-Policy`, `Referrer-Policy` |
| **Cookies de session** | HTTP-only, SameSite=Lax, Secure flag en production uniquement |
| **Durée de session** | 1 heure (`PERMANENT_SESSION_LIFETIME = 3600`) |
| **Clé secrète** | Minimum 32 caractères ; auto-générée en développement si absente ; erreur en production |
| **Permissions fichier** | `.secret` et `.env` en `0o600` (lecture/écriture propriétaire uniquement) |

---

## Observations / Limitations Actuelles

1. **Aucune base de données** — pas de modèles, migrations ou ORM. Toutes les données sont des données simulées générées dans `app.py` (~200 items catalogue).
2. **Pas de logique d'authentification fonctionnelle** — les formulaires POST pour login/inscription n'ont pas de handlers (405 Method Not Allowed).
3. **Pas de moteur de recherche réel** — la barre de recherche affiche une `alert()` JavaScript à la soumission.
4. **Aucun endpoint API** — tout est rendu côté serveur via Jinja2.
5. **Contenu hardcoded** — URLs des miroirs, email de contact et statistiques (seeders, torrents) sont fixes dans les templates.
6. **Structure minimaliste** — tout est plat, pas de blueprints ni sous-modules.

---

*Document généré automatiquement basé sur l'analyse du code source.*
