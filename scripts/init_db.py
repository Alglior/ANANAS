import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def init_db():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if existing_tables:
            print(f"Tables already exist: {', '.join(existing_tables)}")
            return

        print("Creating database tables...")
        db.create_all()
        print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
