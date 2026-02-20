#!/bin/bash
set -e

BACKUP_DIR="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

echo "[$(date)] Starting backup of ${POSTGRES_DB}..."
mkdir -p "$BACKUP_DIR"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$PGHOST" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleanup done. Backups: $(ls -1 "$BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l)"
