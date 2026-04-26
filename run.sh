#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────
#  A.N.A.N.A.S. – Launch script
#  Checks for .secret, generates if missing or invalid.
#  Sets up venv + dependencies if not present.
# ────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# ───────────────────────────────────────────────
# 1) Virtual environment & dependencies
# ───────────────────────────────────────────────

if [ ! -d ".venv" ]; then
    echo "[SETUP] No virtual environment found. Creating .venv..."
    python3 -m venv .venv
    echo "[SETUP] Activating .venv and installing dependencies..."
    ./.venv/bin/pip install --quiet -r requirements.txt
    echo "[OK] Virtual environment ready."
else
    echo "[SETUP] Using existing .venv."
fi

# ───────────────────────────────────────────────
# 2) Secret key validation & generation
# ───────────────────────────────────────────────

validate_key() {
    # Returns 0 if valid (>=32 chars), 1 otherwise
    local val="$1"
    [[ -n "$val" && ${#val} -ge 32 ]]
}

echo "[INFO] Checking secret key..."

if [ -f ".secret" ] && grep -q "^FLASK_SECRET_KEY=" ".secret"; then
    # Extract the key value safely
    KEY_VAL=$(grep "^FLASK_SECRET_KEY=" ".secret" | head -n 1 | cut -d'=' -f2)
    if validate_key "$KEY_VAL"; then
        echo "[OK] Secret key is valid – launching app."
    else
        echo "[! ] Key found but too short (<32 chars). Generating a new one..."
    fi
else
    echo "[! ] No secret key found. Generating a secure one..."
fi

if [ -z "$KEY_VAL" ]; then
    SECRET="FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    echo "$SECRET" > .secret
    chmod 600 .secret
    KEY_VAL=$(echo "$SECRET" | cut -d'=' -f2)
fi

# Export the key to environment for the app
export FLASK_SECRET_KEY="$KEY_VAL"

# ───────────────────────────────────────────────
# 3) Launch the app
# ───────────────────────────────────────────────

set -a
source .secret
set +a

echo ""
echo "[START] Starting Flask server on http://127.0.0.1:5000"
./.venv/bin/python3 app.py
