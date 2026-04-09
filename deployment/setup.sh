#!/bin/bash

# ============================================
# MAYA SOC ENTERPRISE - INITIAL SETUP SCRIPT
# ============================================
# Prepares a fresh DigitalOcean droplet for deployment
# Usage: sudo bash <(curl -s https://raw.githubusercontent.com/YOUR_USERNAME/maya-soc-enterprise/main/deployment/setup.sh)
# Or: sudo ./setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# ============ PREREQUISITES ============
log_info "Checking prerequisites..."

if [ "$EUID" -ne 0 ]; then 
    log_error "This script must be run as root"
    exit 1
fi

# ============ UPDATE SYSTEM ============
log_info "Updating system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git build-essential vim htop

log_success "System updated"

# ============ INSTALL DOCKER ============
log_info "Installing Docker..."

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    usermod -aG docker root
else
    log_warning "Docker already installed"
fi

log_success "Docker installed"

# ============ INSTALL DOCKER COMPOSE ============
log_info "Installing Docker Compose..."

if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
else
    log_warning "Docker Compose already installed"
fi

log_success "Docker Compose installed"

# ============ ENABLE DOCKER ============
log_info "Enabling Docker daemon..."
systemctl enable docker
systemctl start docker
log_success "Docker enabled"

# ============ INSTALL SSL TOOLS ============
log_info "Installing SSL tools..."
apt-get install -y certbot python3-certbot-nginx

log_success "SSL tools installed"

# ============ INSTALL MONITORING TOOLS ============
log_info "Installing monitoring tools..."
apt-get install -y htop iotop nethogs

log_success "Monitoring tools installed"

# ============ CREATE PROJECT DIRECTORY ============
log_info "Creating project directory..."
mkdir -p /root/maya-mvp
mkdir -p /root/backups
mkdir -p /root/logs

log_success "Directories created"

# ============ CLONE REPOSITORY ============
log_info "Initializing repository..."

if [ ! -d "/root/maya-mvp/.git" ]; then
    cd /root/maya-mvp
    git init
    git remote add origin https://github.com/geethu5166/maya-mvp.git
    git pull origin main
    log_success "Repository initialized"
else
    log_warning "Repository already initialized"
fi

cd /root/maya-mvp

# ============ CREATE ENVIRONMENT FILE ============
log_info "Creating environment file..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_warning ".env created from .env.example"
        log_warning "IMPORTANT: Edit .env with your configuration before deployment"
    else
        log_error ".env.example not found"
    fi
else
    log_warning ".env already exists"
fi

# ============ SETUP BACKUPS CRON ============
log_info "Setting up automated backups..."

CRON_JOB="0 2 * * * /root/maya-mvp/deployment/backup.sh >> /root/logs/backup.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "backup.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log_success "Backup cron job scheduled (2 AM daily)"
else
    log_warning "Backup cron job already scheduled"
fi

# ============ SETUP CERTIFICATE RENEWAL CRON ============
log_info "Setting up certificate renewal..."

CERT_CRON_JOB="0 3 * * * certbot renew --quiet >> /root/logs/certbot.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "$CERT_CRON_JOB") | crontab -
    log_success "Certificate renewal cron job scheduled (3 AM daily)"
else
    log_warning "Certificate renewal cron job already scheduled"
fi

# ============ CREATE DEPLOYMENT GUIDE ============
log_info "Creating quick start guide..."

cat > /root/README.md << 'EOF'
# MAYA SOC ENTERPRISE - Deployment Quick Start

## Next Steps

1. **Configure Environment**
   ```bash
   cd /root/maya-mvp
   nano .env
   ```
   Update with your:
   - Secure passwords
   - Domain name (maya.vaultrap.com)
   - Email address
   - Any API keys

2. **Generate SSL Certificate**
   ```bash
   certbot certonly --standalone -d maya.vaultrap.com --email your-email@example.com --agree-tos
   ```

3. **Deploy Application**
   ```bash
   sudo /root/maya-mvp/deployment/deploy.sh
   ```

4. **Monitor Services**
   ```bash
   /root/maya-mvp/deployment/monitor.sh
   ```

5. **View Logs**
   ```bash
   cd /root/maya-mvp
   docker compose logs -f
   ```

## Important Files

- `.env` - Configuration (DO NOT commit to git)
- `docker-compose.yml` - Service definitions
- `deployment/deploy.sh` - Main deployment script
- `deployment/backup.sh` - Database backup script
- `deployment/monitor.sh` - System monitoring

## Status Commands

```bash
# View all services
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# View resource usage
docker stats

# Check disk space
df -h
```

## Support

- GitHub: https://github.com/geethu5166/maya-mvp
- Logs: /root/logs/
- Backups: /root/backups/

Need help? Check the COMPLETE_DEPLOYMENT_GUIDE.md
EOF

log_success "Quick start guide created"

# ============ PERMISSION FIX ============
log_info "Setting up file permissions..."

chmod +x /root/maya-mvp/deployment/*.sh

log_success "Permissions configured"

# ============ COMPLETION ============
echo ""
log_success "════════════════════════════════════════════════════════════"
log_success "INITIAL SETUP COMPLETE!"
log_success "════════════════════════════════════════════════════════════"
echo ""

log_info "NEXT STEPS:"
echo ""
echo "1. Configure your environment:"
echo "   nano /root/maya-mvp/.env"
echo ""
echo "2. Generate SSL certificate:"
echo "   certbot certonly --standalone -d maya.vaultrap.com --email your-email@example.com"
echo ""
echo "3. Start deployment:"
echo "   sudo /root/maya-mvp/deployment/deploy.sh"
echo ""
echo "4. Monitor your application:"
echo "   /root/maya-mvp/deployment/monitor.sh"
echo ""

echo -e "${BLUE}Useful commands:${NC}"
echo "  View logs:     docker compose logs -f"
echo "  Service status: docker compose ps"
echo "  Quick guide:   cat /root/README.md"
echo ""

log_success "Setup complete! Your server is ready for deployment."
