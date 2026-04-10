#!/bin/bash

# ============================================
# MAYA SOC ENTERPRISE - AUTOMATED DEPLOYMENT
# ============================================
# This script automates the entire deployment process
# Usage: sudo ./deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ HELPER FUNCTIONS ============
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============ CHECK PREREQUISITES ============
log_info "Checking prerequisites..."

if [ "$EUID" -ne 0 ]; then 
    log_error "This script must be run as root"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi

if ! command -v git &> /dev/null; then
    log_error "Git is not installed"
    exit 1
fi

log_success "Prerequisites check passed"

# ============ CONFIGURATION ============
PROJECT_DIR="/root/maya-mvp"
BACKUP_DIR="/root/backups"
DOMAIN="maya.vaultrap.com"
EMAIL="your-email@example.com"
DB_USER="${POSTGRES_USER:-soc_user}"
DB_NAME="${POSTGRES_DB:-maya_soc}"

log_info "Configuration:"
log_info "  Project Directory: $PROJECT_DIR"
log_info "  Backup Directory: $BACKUP_DIR"
log_info "  Domain: $DOMAIN"

# ============ STEP 1: BACKUP CURRENT DATABASE ============
log_info "Step 1: Creating database backup..."

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/maya_soc_$TIMESTAMP.sql.gz"

if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cd "$PROJECT_DIR"
    
    if docker compose ps | grep -q "db"; then
        log_info "Backing up database..."
        docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$BACKUP_FILE" || {
            log_warning "Database backup failed or database not available"
        }
        
        if [ -f "$BACKUP_FILE" ]; then
            log_success "Database backed up: $BACKUP_FILE"
        fi
    else
        log_warning "Database container not running, skipping backup"
    fi
fi

# ============ STEP 2: PULL LATEST CODE ============
log_info "Step 2: Pulling latest code from GitHub..."

cd "$PROJECT_DIR"
git fetch origin
git reset --hard origin/main
chmod +x "$PROJECT_DIR/deployment/"*.sh
log_success "Code updated to latest version"

# ============ STEP 3: UPDATE ENVIRONMENT ============
log_info "Step 3: Checking environment configuration..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        log_warning ".env file not found, creating from .env.example"
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        log_warning "Please edit .env with your configuration and run deploy again"
        exit 1
    fi
else
    log_success ".env file found"
fi

# ============ STEP 4: VERIFY SSL CERTIFICATE ============
log_info "Step 4: Checking SSL certificate..."

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    log_warning "SSL certificate not found for $DOMAIN"
    log_info "To generate certificate, run:"
    echo "  certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos"
    log_warning "Certificate is required for HTTPS deployment"
else
    EXPIRY=$(certbot certificates | grep -A2 "$DOMAIN" | grep "Expiry Date")
    log_success "SSL Certificate: $EXPIRY"
fi

# ============ STEP 5: BUILD DOCKER IMAGES ============
log_info "Step 5: Building Docker images..."

cd "$PROJECT_DIR"
if [ "${BUILD_NO_CACHE:-false}" = "true" ]; then
    log_warning "BUILD_NO_CACHE=true set - performing no-cache build"
    docker compose build --no-cache
else
    docker compose build
fi
log_success "Docker images built successfully"

# ============ STEP 6: START SERVICES ============
log_info "Step 6: Starting services..."

docker compose down || true
docker volume prune -f
docker compose up -d
log_success "Services started"

# ============ STEP 7: WAIT FOR SERVICES ============
log_info "Step 7: Waiting for services to be healthy..."

sleep 10

# Check database
log_info "Checking database health..."
RETRY=0
while [ $RETRY -lt 30 ]; do
    if docker compose exec -T db pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        log_success "Database is healthy"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 1
done

if [ $RETRY -ge 30 ]; then
    log_error "Database failed to become healthy"
    docker compose logs db
    exit 1
fi

# Check backend
log_info "Checking backend health..."
RETRY=0
while [ $RETRY -lt 30 ]; do
    if docker compose exec backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 1
done

if [ $RETRY -ge 30 ]; then
    log_error "Backend failed to become healthy"
    docker compose logs backend
    exit 1
fi

log_success "All services are healthy"

# ============ STEP 8: VERIFY DEPLOYMENT ============
log_info "Step 8: Verifying deployment..."

echo ""
log_info "Service Status:"
docker compose ps

echo ""
log_info "Testing endpoints:"

# Test backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log_success "Backend health endpoint: OK"
else
    log_warning "Backend health endpoint: FAILED"
fi

# Test frontend
if curl -f http://localhost:5173 > /dev/null 2>&1; then
    log_success "Frontend: OK"
else
    log_warning "Frontend: FAILED"
fi

# ============ STEP 9: CLEANUP ============
log_info "Step 9: Cleaning up..."

# Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
log_success "Old backups cleaned"

# Cleanup Docker
docker system prune -f --filter "until=168h"
log_success "Docker images cleaned"

# ============ COMPLETION ============
echo ""
log_success "============================================"
log_success "DEPLOYMENT COMPLETE!"
log_success "============================================"
echo ""
log_info "Access your application:"
echo "  Frontend: https://$DOMAIN"
echo "  API: https://$DOMAIN/api/v1"
echo "  Health: https://$DOMAIN/health"
echo ""
log_info "View logs:"
echo "  cd $PROJECT_DIR"
echo "  docker compose logs -f"
echo ""

# ============ FINAL STATUS ============
docker compose ps
