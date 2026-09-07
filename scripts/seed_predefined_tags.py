"""
Seed les tags prédéfinis depuis predefined_tags.json.
Ajoute les nouvelles catégories ET les tags manquants aux catégories existantes.
S'exécute automatiquement au démarrage du Docker (docker-entrypoint.sh).
"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import PredefinedTagCategory, PredefinedTag


def seed_predefined_tags():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        if not inspector.has_table("predefined_tag_categories"):
            print("Creating predefined_tag_categories and predefined_tags tables...")
            PredefinedTagCategory.__table__.create(db.engine)
            PredefinedTag.__table__.create(db.engine)

        json_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "static" / "predefined_tags.json"
        if not json_path.exists():
            print("predefined_tags.json not found, nothing to seed.")
            return

        with open(json_path) as f:
            data = json.load(f)

        existing_cats = {c.name: c for c in PredefinedTagCategory.query.all()}
        added_cats = 0
        added_tags = 0

        for i, cat_data in enumerate(data.get("categories", [])):
            cat_name = cat_data["name"]

            if cat_name in existing_cats:
                # Catégorie existante → ajouter les tags manquants
                category = existing_cats[cat_name]
                existing_tag_names = {t.name for t in category.tags}
                new_tags = [t for t in cat_data.get("tags", []) if t not in existing_tag_names]

                if new_tags:
                    max_order = db.session.query(
                        db.func.max(PredefinedTag.display_order)
                    ).filter(PredefinedTag.category_id == category.id).scalar() or 0

                    for j, tag_name in enumerate(new_tags):
                        tag = PredefinedTag(
                            category_id=category.id,
                            name=tag_name,
                            display_order=max_order + j + 1
                        )
                        db.session.add(tag)
                        added_tags += 1
                    print(f"  + {len(new_tags)} tag(s) ajouté(s) à « {cat_name} »")
            else:
                # Nouvelle catégorie → tout créer
                category = PredefinedTagCategory(name=cat_name, display_order=i)
                db.session.add(category)
                db.session.flush()

                for j, tag_name in enumerate(cat_data.get("tags", [])):
                    tag = PredefinedTag(
                        category_id=category.id,
                        name=tag_name,
                        display_order=j
                    )
                    db.session.add(tag)

                added_cats += 1
                print(f"  + Nouvelle catégorie « {cat_name} » ({len(cat_data.get('tags', []))} tags)")

        db.session.commit()

        total_cats = PredefinedTagCategory.query.count()
        total_tags = PredefinedTag.query.count()
        print(f"\n✅ Seed terminé : {total_cats} catégories, {total_tags} tags au total")
        if added_cats or added_tags:
            print(f"   ({added_cats} catégorie(s) neuve(s), {added_tags} tag(s) ajouté(s))")


if __name__ == "__main__":
    seed_predefined_tags()
