# Phase 4 — Seed Data (Peuplement de la BDD)

### 4.1 Extraire le générateur mock existant
**Fichier :** `scripts/seed_data.py` (nouveau)

Créer un script Python qui :
1. Lit les constantes mock actuelles de `app.py` (`LOREM_IPSUM_FR`, `_AUTHOR_NAMES`, etc.)
2. Génère les 600 items en les insérant directement via SQLAlchemy ORM
3. Pour chaque item, crée ses tags et gallery items associés

Structure du script :
```python
from app import create_app, db
from models import Item, ItemTag, ItemGallery

def seed_all():
    with create_app().app_context():
        # Nettoyer les anciennes données
        db.session.execute(db.table("item_gallery").delete())
        db.session.execute(db.table("item_tags").delete())
        db.session.execute(db.table("items").delete())

        # Générer items donnees (200)
        for i in range(1, 201):
            item = Item(type="geodonnee", title=..., format_type=..., ...)
            db.session.add(item)
            db.session.flush()  # récupère l'ID

            # Insérer les tags
            for tag in tags:
                db.session.add(ItemTag(item_id=item.id, tag=tag))

            # Insérer la galerie
            for g in gallery:
                db.session.add(ItemGallery(...))

        db.session.commit()

        # Répéter pour cartes (200) et applications (200)
```

### 4.2 Exécution
```bash
# Via docker
docker compose exec app python scripts/seed_data.py

# Ou en local
python scripts/seed_data.py
```
