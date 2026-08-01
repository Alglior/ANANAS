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

        existing_names = {c.name for c in PredefinedTagCategory.query.all()}
        added = 0

        for i, cat_data in enumerate(data.get("categories", [])):
            if cat_data["name"] in existing_names:
                continue

            category = PredefinedTagCategory(name=cat_data["name"], display_order=i)
            db.session.add(category)
            db.session.flush()

            for j, tag_name in enumerate(cat_data.get("tags", [])):
                tag = PredefinedTag(category_id=category.id, name=tag_name, display_order=j)
                db.session.add(tag)

            added += 1

        db.session.commit()

        if added:
            print(f"Seeded {added} new categories and their tags successfully.")
        else:
            print(f"All {len(data.get('categories', []))} categories already exist, nothing to add.")


if __name__ == "__main__":
    seed_predefined_tags()