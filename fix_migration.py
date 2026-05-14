"""Fix pending -> unofficial migration at startup."""
import os
os.environ.setdefault("FLASK_ENV", "production")

from app import create_app, db
from models import Item

app = create_app()

with app.app_context():
    updated = Item.query.filter_by(verification_status="pending").update({"verification_status": "unofficial"})
    if updated:
        db.session.commit()
        print(f"[fix_migration] Updated {updated} records from 'pending' to 'unofficial'")
    else:
        print("[fix_migration] No pending records found.")
