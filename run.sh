#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
#  A.N.A.N.A.S. — Dev launcher (Flask dev server)
#
#  Usage: ./run.sh        → starts local dev server
#  Prerequisites: setup.sh (run first!)
# ──────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f ".secret" ]; then
    echo "ERROR: No .secret file found. Run ./setup.sh local first."
    exit 1
fi

source .secret
export FLASK_SECRET_KEY

echo "[START] Flask dev server on http://127.0.0.1:5000 (Ctrl+C to stop)"
./.venv/bin/python3 app.py
