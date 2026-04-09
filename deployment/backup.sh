#!/bin/bash

# ============================================
# MAYA SOC ENTERPRISE - BACKUP SCRIPT
# ============================================
# Creates automated database backups
# Usage: ./backup.sh

set -e

BACKUP_DIR="/root/backups"
PROJECT_DIR="/root/maya-soc-enterprise"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/maya_soc_$TIMESTAMP.sql.gz"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

log_info "Starting database backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
cd "$PROJECT_DIR"

if ! docker compose ps db | grep -q "Up"; then
    log_error "Database container is not running"
    exit 1
fi

log_info "Creating database dump..."
docker compose exec -T db pg_dump -U maya_user maya_soc | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_success "Backup created: $BACKUP_FILE ($SIZE)"
else
    log_error "Backup failed"
    exit 1
fi

# Cleanup old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete | wc -l)
log_success "Removed $DELETED old backup files"

# Backup statistics
log_info "Backup Statistics:"
echo "  Total backups: $(ls -1 "$BACKUP_DIR"/*.sql.gz | wc -l)"
echo "  Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "  Latest backup: $(ls -lh "$BACKUP_FILE" | awk '{print $5, $6, $7, $8, $9}')"

log_success "Backup complete!"
