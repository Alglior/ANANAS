# Architecture du Projet A.N.A.N.A.S.

## Vue d'ensemble

**A.N.A.N.A.S.** est un portail de services de données géospatiales qui distribue des données géographiques via magnet links et le protocole BitTorrent. Il s'agit d'une application web Flask monolithique, entièrement en français, avec des pages d'authentification (login/inscription), une page de contact et une page d'accueil.

---

## Stack Technique

| Couche | Technologie |
|--------|-------------|
| Framework Web | Flask 3.1.0 (Python) |
| Moteur de templates | Jinja2 (intégré à Flask) avec héritage de templates |
| Serveur de production | Gunicorn 23.0.0 |
| Configuration | python-dotenv 1.0.1, variables d'environnement, fichier `.secret` |
| Sécurité | Flask-WTF 1.2.1 (protection CSRF), headers de sécurité personnalisés |
| CSS | Vanilla CSS modulaire (variables CSS custom properties) |
| JavaScript | Vanilla JS (aucune librairie/framework) |
| Polices | Google Fonts — Ubuntu + Ubuntu Mono |

---

## Pattern Architectural

Application **MVC simplifié** avec une structure aplatie :

- **Pas de modèle traditionnel** — aucun ORM, aucun schéma de base de données
- **Pattern Factory** — `create_app()` dans `app.py` pour la création de l'application
- **Enregistrement dynamique des routes** — les routes sont définies comme objets de données et enregistrées via `_register_view()`, sans décorateurs individuels
- **Contrôleur unique** — toute la logique backend réside dans `app.py` (pas de blueprints, pas de modules séparés)
- **Héritage de templates** — `base.html` → templates de page → `partials/header.html`, `partials/footer.html`
- **Contrôleur fin** — chaque handler de route appelle simplement `render_template()` avec titre et données meta

---

## Routes / Endpoints

Toutes les routes sont en **GET**, retournant des templates Jinja2 :

| URL | Endpoint | Template | Description |
|-----|----------|----------|-------------|
| `/` | `home` | `index.html` | Page d'accueil (hero, miroirs BitTorrent) |
| `/connexion` | `connexion` | `connexion.html` | Formulaire de connexion |
| `/inscription` | `inscription` | `inscription.html` | Formulaire d'inscription |
| `/contact` | `contact` | `contact.html` | Page contact (bouton copier email) |

> **Note :** Les formulaires de login et d'inscription utilisent `method="POST"` mais aucune route POST n'est implémentée — ils retourneraient une erreur 405 Method Not Allowed.

---

## Structure des Fichiers

```
sitev2/
├── app.py                     # Fichier unique : routes + factory create_app()
├── requirements.txt           # Dépendances Python
├── run.sh                     # Lancement développement (Flask dev server, port 5000)
├── run_prod.sh                # Lancement production (Gunicorn, port 5000)
├── .secret                    # Clé secrète Flask (permissions 0o600)
├── .secret.example            # Exemple de fichier secret
├── README.md                  # Documentation du projet
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
│   │   └── main.js            # Gestionnaire de recherche, bouton copier email, validation mot de passe
│   └── images/
│       └── logo/ANANAS.png    # Logo PNG du projet (128x128)
└── __pycache__/               # Cache Python
└── .venv/                     # Environnement virtuel Python
```

---

## Héritage des Templates

Chaque page étend `base.html` et fournit un bloc `{% block content %}` personnalisé ainsi qu'un titre et une meta description :

```
base.html
├── index.html      → Hero + grille de miroirs BitTorrent
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
| **Cookies de session** | HTTP-only, SameSite=Lax, Secure flag en production |
| **Durée de session** | 1 heure (`PERMANENT_SESSION_LIFETIME = 3600`) |
| **Clé secrète** | Validation minimum 32 caractères ; auto-générée en développement si absente ; erreur en production |
| **Permissions fichier** | `.secret` en `0o600` (lecture/écriture propriétaire uniquement) |

---

## Script de Déploiement

| Script | Environnement | Serveur | Port |
|--------|--------------|---------|------|
| `run.sh` | Développement | Flask dev server | 5000 |
| `run_prod.sh` | Production | Gunicorn (3 workers) | 5000 |

Les deux scripts :
1. Créent l'environnement virtuel si nécessaire
2. Valident/génèrent la clé secrète
3. Lancent le serveur

---

## Observations / Limitations Actuelles

1. **Aucune base de données** — pas de modèles, migrations ou ORM
2. **Pas de logique d'authentification fonctionnelle** — les formulaires POST n'ont pas de handlers (405)
3. **Pas de moteur de recherche réel** — la barre de recherche affiche une `alert()` JavaScript à la soumission
4. **Aucun endpoint API** — tout est rendu côté serveur via Jinja2
5. **Contenu hardcoded** — URLs des miroirs, email de contact et statistiques (seeders, torrents) sont fixes dans les templates
6. **Structure minimaliste** — tout est plat, pas de sous-applications ni blueprints

---

*Document généré automatiquement basé sur l'analyse du code source.*
