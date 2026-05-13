# Phase 3 — Initialisation & Migrations

### 3.1 Initialiser Flask-SQLAlchemy dans `app.py`
**Fichier :** `app.py` (modifier les lignes 1-7)

Remplacer le début de `create_app()` :
```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def create_app(app_name="ANANAS"):
    app = Flask(__name__)
    config = Config()
    config.validate()
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ananas.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    csrf.init_app(app)
    ...
```

### 3.2 Créer le script de migration initiale
**Fichier :** `scripts/init_db.py` (nouveau, exécuté une seule fois)

Ce script :
1. Crée les tables si elles n'existent pas (`db.create_all()`)
2. Insère les données seed via des inserts batch (voir Phase 4)
