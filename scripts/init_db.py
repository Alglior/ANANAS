import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def init_db():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        all_tables = set(db.metadata.tables.keys())
        missing_tables = all_tables - existing_tables

        if missing_tables:
            print(f"Creating missing tables: {', '.join(sorted(missing_tables))}")
            db.create_all()
            print("Missing tables created successfully.")
        else:
            print("All tables already exist.")

        if existing_tables:
            columns = [col["name"] for col in inspector.get_columns("items")]

            if "image_magnets_pending" not in columns:
                print("Adding image_magnets_pending column...")
                db.session.execute(db.text("ALTER TABLE items ADD COLUMN image_magnets_pending BOOLEAN NOT NULL DEFAULT 0"))
            if "image_magnets_total" not in columns:
                print("Adding image_magnets_total column...")
                db.session.execute(db.text("ALTER TABLE items ADD COLUMN image_magnets_total INTEGER NOT NULL DEFAULT 0"))

            db.session.commit()
            return


if __name__ == "__main__":
    init_db()
