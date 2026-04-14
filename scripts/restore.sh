#!/usr/bin/env bash
# PostgreSQL restore script for mainty-v2
# Usage: bash scripts/restore.sh /path/to/mainty-YYYYMMDD-HHMMSS.sql.gz

set -euo pipefail

BACKUP_FILE="${1:?Usage: $0 <backup-file.sql.gz>}"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

# ── Project root ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

: "${POSTGRES_USER:?POSTGRES_USER is not set}"
: "${POSTGRES_DB:?POSTGRES_DB is not set}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set}"

cd "$PROJECT_DIR"

_on_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RESTORE FAILED — attempting to restart web container..." >&2
    docker compose -f "$COMPOSE_FILE" start web || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Database may be empty. Verify before serving traffic." >&2
}
trap _on_error ERR

echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: This will DESTROY all data in $POSTGRES_DB and replace it with:"
echo "  Backup file: $BACKUP_FILE"
echo "  Compose:     $COMPOSE_FILE"
echo "  Press Ctrl-C within 5 seconds to abort."
sleep 5

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring from: $BACKUP_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping web container..."
docker compose -f "$COMPOSE_FILE" stop web

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Wiping database schema..."
docker compose -f "$COMPOSE_FILE" exec -T \
    -e PGPASSWORD="$POSTGRES_PASSWORD" \
    db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring dump..."
gunzip -c "$BACKUP_FILE" \
    | docker compose -f "$COMPOSE_FILE" exec -T \
        -e PGPASSWORD="$POSTGRES_PASSWORD" \
        db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -v ON_ERROR_STOP=1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restarting web container..."
docker compose -f "$COMPOSE_FILE" start web

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore complete."
