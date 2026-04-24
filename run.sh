#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────
#  A.N.A.N.A.S. – Launch script
#  Checks for .secret, generates if missing.
# ────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "[INFO] Checking secret key…"

if [ -f ".secret" ] && grep -q "^FLASK_SECRET_KEY=" .secret; then
    echo "[OK]  Secret key exists – launching app."
else
    echo "[! ]  No secret key found. Generating a secure one..."
    SECRET="FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    echo "$SECRET" > .secret
    chmod 600 .secret
    echo "[OK]  Secret key generated."
fi

# Source the secret so the env var is exported for Python too.
set -a
source .secret
set +a

# Use venv Python if available, otherwise system Python
if [ -d ".venv" ]; then
    PY=".venv/bin/python3"
else
    PY="python3"
fi

echo ""
echo "[START] Starting Flask server on http://127.0.0.1:5000"
$PY app.py
