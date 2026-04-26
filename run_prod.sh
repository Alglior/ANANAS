#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────
#  A.N.A.N.A.S. – Production Launch Script
#  Uses Gunicorn instead of Flask's dev server.
#  Requires the SECRET_KEY to be configured via environment variable.
# ────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# ───────────────────────────────────────────────
# 1) Virtual environment & dependencies
# ───────────────────────────────────────────────

if [ ! -d ".venv" ]; then
    echo "[SETUP] No virtual environment found. Creating .venv..."
    python3 -m venv .venv
    echo "[SETUP] Installing production dependencies..."
    ./.venv/bin/pip install --quiet -r requirements.txt
    echo "[OK] Virtual environment ready."
else
    echo "[SETUP] Using existing .venv."
fi

# ───────────────────────────────────────────────
# 2) Secret Key / Environment Config (MANDATORY)
# ───────────────────────────────────────────────

if [ -f ".secret" ]; then
    source .secret
else
    # Check if FLASK_SECRET_KEY is already set in the environment
    if [ -z "${FLASK_SECRET_KEY:-}" ]; then
        echo "CRITICAL ERROR: No secret key found! Cannot start production without it."
        echo "Please create a .secret file or export FLASK_SECRET_KEY before launching."
        exit 1
    fi
fi

# Force production mode flags
export FLASK_ENV=production
export FLASK_DEBUG=false
export SESSION_COOKIE_SECURE=true

echo ""
echo "[START] A.N.A.N.A.S. (Production Mode)"
echo "----------------------------------------"
./.venv/bin/gunicorn -b 127.0.0.1:5000 --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s' --timeout 30 "app:create_app()"
