# Plan de refactorisation de app.py → package blueprints

## Diagnostic

`app.py` fait **1151 lignes** contre ~350 utiles. Le problème principal : **tout est inline dans `create_app()`**, avec 3 versions dupliquées de la logique catalogue, et aucun regroupement fonctionnel.

---

## Objectif

Réduire `app.py` à **~200 lignes** en externalisant les routes dans des **blueprints Flask** (`flask.Blueprint`). Le fichier d'entrée ne doit plus contenir que l'usine de création, la config DB et l'enregistrement des blueprints.

---

## Architecture cible

```
sitev2/
├── app.py                          ← create_app() + registration (150-200 lignes)
└── web/                            ← nouveau package
    ├── __init__.py                 ← blueprint_factory + register_all()
    ├── auth_routes.py              ← connexion / inscription / logout
    ├── catalogue_routes.py         ← logique catalogue unique (fusion des 3 vues)
    ├── item_routes.py              ← detail, galerie
    ├── organization_routes.py      ← CRUD orgs, membres, détails org
    ├── admin_routes.py             ← ban/unban, reports, admin pages
    ├── upload_routes.py            ← chunk upload, viz links
    └── shared.py                   ← login_required, get_current_user, page numbers, config
```

---

## Etapes de refactorisation

### Etape 1 — Extraire les utilitaires partagés (`web/shared.py`)

**Extrait de app.py : lignes 32-56, 96-146**

Créer `web/shared.py` avec :
- `login_required` (decorator + check banned/non-active)
- `get_current_user()`
- `_build_page_numbers(current, total)`
- `Config` class (lecture clé secrète + validation prod)
- `ITEMS_PER_PAGE = 30`

### Etape 2 — Fusionner les 3 vues catalogue (`web/catalogue_routes.py`)

**Le probleme** : `get_catalogue_page()`(l.58), `catalogue_view()(l.265)`, `catalogue_type_view()(l.353)`, `catalogue_type_json_view()(l.427)` font la meme requete SQL 4 fois avec du code dupliqué.

**Solution** : creer un seul endpoint `get_catalogue(catalogue, page, filter_verified, org_slug, format_param)` qui:
1. Map le nom du catalogue au type SQL (`geodonnee`/`carte`/`application`)
2. Construit la query avec filtres optionnels
3. Renvoie soit un JSON `jsonify()` soit le template `catalogue.html`

Routes finales :
```python
bp = Blueprint("catalogue", __name__)

@bp.route("/catalogue")
@bp.route("/catalogue/<catalogue_type>")
@bp.route("/catalogue/<catalogue_type>/<int:page>")
def catalogue(catalogue_type="donnees", page=1):
    ...  # logique unique

@bp.route("/catalogue/<catalogue_type>/<int:page>/json")
def catalogue_json(catalogue_type, page):
    ...  # appelle get_catalogue(..., format="json")
```

**Gain estimé** : -180 lignes.

### Etape 3 — Routes d'authentification (`web/auth_routes.py`)

**Extrait de app.py : lignes 514-578, 1123-1126**

Regrouper :
- `connexion_page` GET (l.517)
- `connexion_post` POST + limiter (l.535)
- `inscription_page` GET (l.525)
- `inscription_post` POST + limiter (l.554)
- `logout` (l.1123)

```python
bp = Blueprint("auth", __name__)
@bp.route("/connexion")
@bp.route("/connexion", methods=["POST"])
...
```

**Gain estimé** : -65 lignes.

### Etape 4 — Routes des items (`web/item_routes.py`)

**Extrait de app.py : lignes 472-511**

Regrouper :
- `favicon_route` (l.472) — peut rester dans app.py ou ici
- `item_detail_view` (l.477)
- `item_gallery_view` (l.502)

```python
bp = Blueprint("items", __name__)
@bp.route("/catalogue/item/<int:item_id>")
@bp.route("/catalogue/item/<int:item_id>/gallery")
...
```

**Gain estimé** : -40 lignes.

### Etape 5 — Interactions utilisateur (`web/interactions.py`)

**Extrait de app.py : lignes 580-662**

Regrouper :
- `rate_item` (l.583)
- `add_comment` (l.612)
- `verify_item` (l.637)

```python
bp = Blueprint("interactions", __name__)
@bp.route("/catalogue/item/<int:item_id>/rate", methods=["POST"])
...
```

**Gain estimé** : -80 lignes.

### Etape 6 — Routes organisations (`web/organization_routes.py`)

**Extrait de app.py : lignes 664-806**

Regrouper les 6 fonctions :
- `create_organization` (l.667)
- `join_organization` (l.699)
- `leave_organization` (l.723)
- `update_member_role` (l.740)
- `organization_detail_view` (l.767)
- `organization_items` (l.785)

```python
bp = Blueprint("organizations", __name__)
@bp.route("/api/organizations", methods=["POST"])
@bp.route("/api/organizations/<slug>/join", methods=["POST"])
...
```

**Gain estimé** : -140 lignes.

### Etape 7 — Routes admin (`web/admin_routes.py`)

**Extrait de app.py : lignes 808-968, 969-1017**

Regrouper les 8 fonctions en 2 blueprints ou 1 seul `admin` blueprint :
- `ban_user` (l.811)
- `list_banned_users` (l.836)
- `create_report` (l.861)
- `list_reports` API (l.909)
- `resolve_report` (l.945)
- `admin_users` page (l.972)
- `admin_reports` page (l.989)

```python
bp = Blueprint("admin", __name__)
@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
...  # tous les endpoints admin/API
```

**Gain estimé** : -200 lignes.

### Etape 8 — Upload et visualisation (`web/upload_routes.py`)

**Extrait de app.py : lignes 1019-1118**

Regrouper :
- `is_allowed_file`, `ALLOWED_EXTENSIONS` (utilitaires internes)
- `upload_chunk` (l.1030)
- `add_viz_link` (l.1087)

```python
bp = Blueprint("upload", __name__)
@bp.route("/api/upload/chunk", methods=["POST"])
@bp.route("/api/items/<int:item_id>/viz-links", methods=["POST"])
...
```

**Gain estimé** : -100 lignes.

### Etape 9 — Finaliser `app.py` (`app.py` ~150 lignes)

Ne plus contenir que :

```python
from app import db, migrate
from web import create_web_blueprints

def create_app(app_name="ANANAS"):
    from flask import Flask
    app = Flask(__name__, template_folder="templates")

    # Config (deplacé vers web/shared.py)
    config = Config()
    config.validate()
    ...

    # DB setup
    ...
    db.init_app(app)
    migrate.init_app(app, db=db)

    # Security
    @app.after_request
    ...

    # Register blueprints
    for bp in create_web_blueprints():
        app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
```

**Final `app.py` : ~120-150 lignes**

---

## Impact cumule

| Fichier | Lignes actuelles | Lignes cible | Gain |
|---------|-----------------|-------------|------|
| app.py | 1151 | ~150 | -1000 |
| web/shared.py | — | ~80 | new |
| web/catalogue_routes.py | — | ~80 | new |
| web/auth_routes.py | — | ~40 | new |
| web/item_routes.py | — | ~25 | new |
| web/interactions.py | — | ~50 | new |
| web/organization_routes.py | — | ~70 | new |
| web/admin_routes.py | — | ~130 | new |
| web/upload_routes.py | — | ~45 | new |
| web/__init__.py | — | ~25 | new |
| **Total** | **1151** | **~615** | **~536 lignes supprimées (duplication)** |

---

## Phasage recommande

1. **Phase A** — `web/shared.py` + `web/__init__.py` (infrastructure)
2. **Phase B** — `web/catalogue_routes.py` (le plus gros gain, -180 lignes)
3. **Phase C** — `web/auth_routes.py`, `web/item_routes.py` (routes simples)
4. **Phase D** — `web/interactions.py`, `web/organization_routes.py`
5. **Phase E** — `web/admin_routes.py`, `web/upload_routes.py`
6. **Phase F** — Supprimer les routes d'app.py, register blueprints

A chaque phase : executer `python -m pytest tests/` pour verifier que tout passe.

---

## Points de vigilance

- **Circular imports** : `models.py` fait `from app import db`. Ne pas changer (c'est un pattern Flask-SQLAlchemy valide).
- **Imports dynamiques inside routes** : deja presentes dans le code actuel (`from models import ...`). Les laisser tel quel ou les remonter en haut des fichiers blueprints respectifs.
- **Limiter + CSRFProtect** : doivent etes attaches a l'app principale (deja fait dans `create_app()`), pas dans les blueprints.
- **`@app.context_processor` inject_user** : le déplacer dans un blueprint avec `bp.context_processor` — Flask permet ca depuis la v2.0+.
