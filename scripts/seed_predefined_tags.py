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

        existing_count = PredefinedTagCategory.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} categories, skipping seed.")
            return

        for i, cat_data in enumerate(data.get("categories", [])):
            category = PredefinedTagCategory(name=cat_data["name"], display_order=i)
            db.session.add(category)
            db.session.flush()

            for j, tag_name in enumerate(cat_data.get("tags", [])):
                tag = PredefinedTag(category_id=category.id, name=tag_name, display_order=j)
                db.session.add(tag)

        db.session.commit()
        print(f"Seeded {len(data.get('categories', []))} categories and their tags successfully.")


if __name__ == "__main__":
    seed_predefined_tags()