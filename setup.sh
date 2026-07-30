#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
#  A.N.A.N.A.S. — Setup & Launch script
#
#  ./setup.sh              → Docker (dev + prod)
#  ./setup.sh local        → Python venv (local dev only)
# ──────────────────────────────────────────────

ENV_FILE=".env"
SECRET_FILE=".secret"
generate_random() {
    python3 -c "import secrets; print(secrets.token_hex(128))"   # 256 hex chars (cryptographic)
}

generate_password() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# ──────────────────────────────────────────────
#  Docker mode — generates .env if missing, then docker compose up
# ──────────────────────────────────────────────
docker_setup() {
    if [ ! -f "$ENV_FILE" ]; then
        local pg_db=$(generate_random | head -c 32)     # DB name short for safety
        local pg_user=$(generate_random | head -c 63)   # PG username max 63 chars (NAMEDATA_LEN-1)
        local pg_pass=$(generate_random | head -c 63)   # PG passwords also limited to ~64 in internal queries
        local flask_key=$(generate_random)

        local admin_pass=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
        local admin_pseudo="systeme-ananas"
        local qb_pass=$(generate_password)

        cat > "$ENV_FILE" <<EOF
# ─── Postgres (generated automatically — SAVE THESE!) ───
POSTGRES_DB=${pg_db}
POSTGRES_USER=${pg_user}
POSTGRES_PASSWORD=${pg_pass}
SQLALCHEMY_DATABASE_URI=postgresql://${pg_user}:${pg_pass}@postgres/${pg_db}

# ─── Admin Account ───
ADMIN_EMAIL=system@ananas.local
ADMIN_PSEUDO=${admin_pseudo}
ADMIN_PASSWORD=${admin_pass}

# ─── Flask ───
FLASK_SECRET_KEY=${flask_key}

# ─── qBittorrent (image magnet downloads) ───
QBITTORRENT_URL=http://qbittorrent:8081
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=${qb_pass}
EOF
        chmod 600 "$ENV_FILE"

        echo "=============================================="
        echo "   CREDENTIALS GENERATED — SAVE THESE:"
        echo "=============================================="
        printf "POSTGRES_DB         : %s\n" "${pg_db}"
        printf "POSTGRES_USER       : %s\n" "${pg_user}"
        printf "POSTGRES_PASSWORD   : %s\n" "${pg_pass}"
        printf "ADMIN_EMAIL         : %s\n" "system@ananas.local"
        printf "ADMIN_PSEUDO        : %s\n" "${admin_pseudo}"
        printf "ADMIN_PASSWORD      : %s\n" "${admin_pass}"
        printf "FLASK_SECRET_KEY    : %s\n" "${flask_key}"
        printf "QBITTORRENT_URL     : %s\n" "http://qbittorrent:8081"
        printf "QBITTORRENT_USERNAME: %s\n" "admin"
        printf "QBITTORRENT_PASSWORD: %s\n" "${qb_pass}"
        echo "=============================================="
    else
        echo "[SKIP] .env already exists."
    fi

    echo ""
    echo "[START] Building & starting Docker containers..."
    docker compose up -d --build
}

# ──────────────────────────────────────────────
#  Local mode — setup venv + secret key, launch Flask dev
# ──────────────────────────────────────────────
local_setup() {
    echo "[SETUP] Virtual environment..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        ./.venv/bin/pip install --quiet -r requirements.txt
    fi
    echo "[OK] Virtual environment ready."

    echo ""
    echo "[SETUP] Secret key..."
    if [ -f "$SECRET_FILE" ]; then
        source "$SECRET_FILE"
        KEY_LEN=${#FLASK_SECRET_KEY}
        if [ "$KEY_LEN" -ge 32 ]; then
            echo "[OK] Key valid ($KEY_LEN chars)."
        else
            FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
            echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" > "$SECRET_FILE"
            chmod 600 "$SECRET_FILE"
            echo "[! ] Key too short — regenerated."
        fi
    else
        FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" > "$SECRET_FILE"
        chmod 600 "$SECRET_FILE"
        echo "[OK] Key generated."
    fi

    echo ""
    echo "[START] Flask dev server on http://127.0.0.1:5000 (Ctrl+C to stop)"
    ./.venv/bin/python3 app.py
}

# ─── Entry point ───
case "${1:-}" in
    local)  local_setup ;;
    *)      docker_setup ;;
esac
