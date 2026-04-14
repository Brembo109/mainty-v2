#!/usr/bin/env bash
# PostgreSQL backup script for mainty-v2
# Reads POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD from .env (project root)
# Overridable via environment: BACKUP_DIR, BACKUP_RETENTION_DAYS, COMPOSE_FILE

set -euo pipefail

# ── Project root (one level up from scripts/) ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Source .env for DB credentials
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

# ── Config (overridable via env) ────────────────────────────────────────────
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-/backup}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/mainty-$TIMESTAMP.sql.gz"
trap 'rm -f "$BACKUP_FILE"' ERR

# ── Validate required vars ──────────────────────────────────────────────────
[[ -n "$BACKUP_DIR" ]] || { echo "BACKUP_DIR must not be empty" >&2; exit 1; }
: "${POSTGRES_USER:?POSTGRES_USER is not set}"
: "${POSTGRES_DB:?POSTGRES_DB is not set}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set}"

# ── Run ─────────────────────────────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup → $BACKUP_FILE"

mkdir -p "$BACKUP_DIR"

cd "$PROJECT_DIR"
docker compose -f "$COMPOSE_FILE" exec -T \
    -e PGPASSWORD="$POSTGRES_PASSWORD" \
    db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$BACKUP_FILE"

SIZE="$(du -sh "$BACKUP_FILE" | cut -f1)"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup complete: $BACKUP_FILE ($SIZE)"

# ── Retention ────────────────────────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Removing backups older than $BACKUP_RETENTION_DAYS days"
find "$BACKUP_DIR" -name "mainty-*.sql.gz" -mtime "+$BACKUP_RETENTION_DAYS" -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done."
