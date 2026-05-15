#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for PostgreSQL..."
while ! pg_isready -h "${POSTGRES_HOST:-postgres}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
    sleep 1
done
echo "[entrypoint] PostgreSQL is ready."

# ─── First boot: create tables + admin user only ───
first_boot=$(python3 -c "
import os, sys
sys.path.insert(0, '/app')
os.environ.setdefault('ADMIN_PASSWORD', 'system')
from app import create_app, db
app = create_app()
with app.app_context():
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print('true' if not tables else 'false')
")

if [ "$first_boot" = "true" ]; then
    echo "[entrypoint] First boot — creating database tables..."
    python3 scripts/init_db.py

    echo "[entrypoint] Creating admin account..."
    ADMIN_PASSWORD="${ADMIN_PASSWORD:-system}"
    python3 -c "
import os, sys
sys.path.insert(0, '/app')
os.environ.setdefault('ADMIN_PASSWORD', 'system')
from app import create_app, db
from models import User
app = create_app()
with app.app_context():
    from werkzeug.security import generate_password_hash
    pw = os.environ.get('ADMIN_PASSWORD', 'system')
    user = User(
        prenom='Système', nom='ANANAS',
        email='system@ananas.local',
        password_hash=generate_password_hash(pw),
        is_active=True, banned=False, is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    print(f'Admin created: system@ananas.local')
"

    echo "[entrypoint] Setting alembic version to head..."
    python3 -c "
import os, sys, subprocess
sys.path.insert(0, '/app')
os.environ.setdefault('ADMIN_PASSWORD', 'system')
result = subprocess.run(['flask', 'db', 'stamp', 'head'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'WARNING: {result.stderr}', file=sys.stderr)
"

else
    echo "[entrypoint] Database already initialized."
fi

echo "[entrypoint] Running flask db upgrade..."
flask db upgrade

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:5000 --workers 3 --timeout 30 'app:create_app()'
