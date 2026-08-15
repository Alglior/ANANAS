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
from src.auth_routes import _generate_pseudo
app = create_app()
with app.app_context():
    from werkzeug.security import generate_password_hash
    pw = os.environ.get('ADMIN_PASSWORD', 'system')
    pseudo = os.environ.get('ADMIN_PSEUDO', '') or _generate_pseudo('Système', 'ANANAS')
    user = User(
        prenom='Système', nom='ANANAS',
        pseudo=pseudo,
        password_hash=generate_password_hash(pw),
        is_active=True, banned=False, is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    print(f'Admin created: {pseudo}')
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
    echo "[entrypoint] Checking for missing tables..."
    python3 scripts/init_db.py
fi

echo "[entrypoint] Running flask db upgrade..."
flask db upgrade

echo "[entrypoint] Seeding predefined tags..."
python3 scripts/seed_predefined_tags.py

echo "[entrypoint] Syncing admin credentials from .env..."
python3 -c "
import os, sys
sys.path.insert(0, '/app')
from app import create_app, db
from models import User
from src.auth_routes import _generate_pseudo
from werkzeug.security import generate_password_hash
app = create_app()
with app.app_context():
    pw = os.environ.get('ADMIN_PASSWORD', 'system')
    pseudo = os.environ.get('ADMIN_PSEUDO', '') or _generate_pseudo('Système', 'ANANAS')
    admin = User.query.filter_by(prenom='Système', nom='ANANAS').first()
    if admin:
        admin.pseudo = pseudo
        admin.password_hash = generate_password_hash(pw)
        db.session.commit()
        print(f'Admin synced: pseudo={pseudo}')
    else:
        print(f'Admin user \"Système ANANAS\" not found, creating...')
        user = User(
            prenom='Système', nom='ANANAS',
            pseudo=pseudo,
            password_hash=generate_password_hash(pw),
            is_active=True, banned=False, is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        print(f'Admin created: {pseudo}')
"

echo "[entrypoint] Ensuring image cache directory..."
mkdir -p /app/instance/image_cache /app/static/uploads/avatars

echo "[entrypoint] Setting qBittorrent password..."
if [ -z "${QBITTORRENT_PASSWORD:-}" ]; then
    echo "[entrypoint] QBITTORRENT_PASSWORD not set, skipping qBittorrent configuration."
else
    QB_PASS="$QBITTORRENT_PASSWORD"
    python3 -c "
import requests, os, time, hashlib, base64, re

qb_url = os.environ.get('QBITTORRENT_URL', 'http://qbittorrent:8081')
qb_user = os.environ.get('QBITTORRENT_USERNAME', 'admin')
qb_pass_new = '$QB_PASS'
config_path = '/qbittorrent_config/qBittorrent.conf'

# Generate PBKDF2 hash for the password
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha1', qb_pass_new.encode(), salt, 600000)
qb_hash = '@ByteArray(' + base64.b64encode(salt).decode() + ':' + base64.b64encode(dk).decode() + ')'

# Write PBKDF2 hash to config file
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = f.read()
    config = re.sub(r'WebUI\\\\Password_PBKDF2=.*', 'WebUI\\\\Password_PBKDF2=\"' + qb_hash + '\"', config)
    with open(config_path, 'w') as f:
        f.write(config)
    print('qBittorrent config updated with generated password hash')
else:
    print(f'Config file not found at {config_path}')

# Wait for qBittorrent and verify login
s = requests.Session()
for attempt in range(30):
    try:
        r = s.post(f'{qb_url}/api/v2/auth/login', data={'username': qb_user, 'password': qb_pass_new}, timeout=5)
        if r.status_code == 204:
            print('qBittorrent password configured successfully')
            break
    except Exception as e:
        pass
    time.sleep(2)
else:
    print('Warning: Could not verify qBittorrent login after 30 attempts')
"
fi

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:5000 --workers 3 --timeout 30 'app:create_app()'
