#!/bin/bash

# ============================================
# MAYA SOC Enterprise - Domain & DNS Verification Script
# ============================================
# Checks DNS, SSL certificates, and web connectivity
# Usage: bash ./verify-domain.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
IP="64.227.137.81"
DOMAIN="vaultrap.com"
SUBDOMAIN="maya.vaultrap.com"
APP_SUBDOMAIN="app.vaultrap.com"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  MAYA SOC Enterprise - Domain & DNS Verification                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  IP: $IP                                     ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Domain: $DOMAIN                                               ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============ DNS Resolution Tests ============
log_info "Checking DNS Resolution..."
echo ""

# Test root domain
log_info "Root Domain: $DOMAIN"
if result=$(nslookup $DOMAIN 2>/dev/null | grep -i "Address" | tail -1); then
    if echo "$result" | grep -q "$IP"; then
        log_success "DNS resolves to $IP"
    else
        log_warning "DNS resolves but to different IP:"
        echo "  $result"
    fi
else
    log_error "DNS does not resolve for $DOMAIN"
    echo "  Try waiting 30 minutes or check registrar DNS settings"
fi

echo ""

# Test MAYA subdomain
log_info "Subdomain: $SUBDOMAIN"
if result=$(nslookup $SUBDOMAIN 2>/dev/null | grep -i "Address" | tail -1); then
    if echo "$result" | grep -q "$IP"; then
        log_success "DNS resolves to $IP"
    else
        log_warning "DNS resolves but to different IP:"
        echo "  $result"
    fi
else
    log_error "DNS does not resolve for $SUBDOMAIN"
    echo "  Try waiting 30 minutes or check registrar DNS settings"
fi

echo ""

# Test APP subdomain
log_info "Subdomain: $APP_SUBDOMAIN"
if result=$(nslookup $APP_SUBDOMAIN 2>/dev/null | grep -i "Address" | tail -1); then
    if echo "$result" | grep -q "$IP"; then
        log_success "DNS resolves to $IP"
    else
        log_warning "DNS resolves but to different IP:"
        echo "  $result"
    fi
else
    log_warning "DNS does not resolve for $APP_SUBDOMAIN (Optional)"
fi

echo ""

# ============ SSL Certificate Tests ============
log_info "Checking SSL Certificates..."
echo ""

# Check root domain certificate
log_info "Certificate: $DOMAIN"
if timeout 5 openssl s_client -connect $DOMAIN:443 -servername $DOMAIN </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    log_success "Valid SSL certificate"
    if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
        true
    fi
else
    log_warning "SSL certificate check (may be normal if domain not fully set up)"
fi

echo ""

# Check MAYA subdomain certificate
log_info "Certificate: $SUBDOMAIN"
if timeout 5 openssl s_client -connect $SUBDOMAIN:443 -servername $SUBDOMAIN </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    log_success "Valid SSL certificate"
else
    log_warning "SSL certificate not found (generate with certbot)"
fi

echo ""

# ============ HTTP/HTTPS Connectivity Tests ============
log_info "Checking HTTP/HTTPS Connectivity..."
echo ""

# Test HTTP redirect
log_info "HTTP Redirect: $DOMAIN"
if timeout 10 curl -I -L http://$DOMAIN 2>/dev/null | grep -q "200\|301\|302"; then
    log_success "HTTP connection working (redirects to HTTPS)"
else
    log_warning "HTTP connection failed (may be normal if SSL not set up)"
fi

echo ""

# Test HTTPS root domain
log_info "HTTPS: $DOMAIN"
if timeout 10 curl -s -k https://$DOMAIN --max-time 5 > /dev/null 2>&1; then
    log_success "HTTPS connection successful"
else
    log_warning "HTTPS connection failed (SSL not ready or not redirecting)"
fi

echo ""

# Test HTTPS MAYA subdomain
log_info "HTTPS: $SUBDOMAIN"
if timeout 10 curl -s -k https://$SUBDOMAIN --max-time 5 > /dev/null 2>&1; then
    log_success "HTTPS connection successful"
else
    log_warning "HTTPS connection failed"
fi

echo ""

# ============ Application Health Checks ============
log_info "Checking Application Health..."
echo ""

# Health check endpoint
log_info "Health Check: $SUBDOMAIN/health"
if timeout 10 curl -s -k https://$SUBDOMAIN/health --max-time 5 | grep -q "healthy"; then
    log_success "Application healthy"
else
    log_warning "Health check endpoint not responding (services may not be running)"
fi

echo ""

# API health check
log_info "API Health: $SUBDOMAIN/health/services"
if timeout 10 curl -s -k https://$SUBDOMAIN/health/services --max-time 5 | grep -q "watchdog_running\|services"; then
    log_success "API responding"
else
    log_warning "API health endpoint not responding (backend may not be running)"
fi

echo ""

# ============ Configuration Verification ============
log_info "Checking Local Configuration..."
echo ""

# Check .env file
if [ -f "/root/maya-soc-enterprise/.env" ]; then
    log_success ".env file exists"
    
    if grep -q "DOMAIN=$DOMAIN\|DOMAIN=maya.vaultrap.com" /root/maya-soc-enterprise/.env 2>/dev/null; then
        log_success ".env has correct domain configuration"
    else
        log_warning ".env domain may need updating - should be: maya.vaultrap.com"
    fi
else
    log_warning ".env file not found (expected at /root/maya-soc-enterprise/.env)"
fi

echo ""

# Check SSL certificates on server
log_info "Checking Server SSL Certificates..."
if [ -d "/etc/letsencrypt/live" ]; then
    if [ -d "/etc/letsencrypt/live/$SUBDOMAIN" ]; then
        log_success "SSL certificate found for $SUBDOMAIN"
    else
        log_warning "SSL certificate NOT found for $SUBDOMAIN"
        echo "  Generate with: certbot certonly --standalone -d $SUBDOMAIN"
    fi
    
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        log_success "SSL certificate found for $DOMAIN"
    else
        log_warning "SSL certificate NOT found for $DOMAIN (optional)"
    fi
else
    log_warning "Certbot not installed (needed for SSL)"
fi

echo ""

# ============ Docker Services Check ============
log_info "Checking Docker Services..."
echo ""

if command -v docker &> /dev/null; then
    if docker compose -f /root/maya-soc-enterprise/docker-compose.yml ps 2>/dev/null | grep -q "Up"; then
        log_success "Docker services running"
        docker compose -f /root/maya-soc-enterprise/docker-compose.yml ps 2>/dev/null | tail -n +2 | while read line; do
            if echo "$line" | grep -q "Up"; then
                log_success "  $(echo $line | awk '{print $1}' | sed 's/-//')"
            else
                log_error "  $(echo $line | awk '{print $1}' | sed 's/-//')"
            fi
        done
    else
        log_error "Docker services not running"
        echo "  Start with: docker compose up -d"
    fi
else
    log_warning "Docker not found (may be running on different system)"
fi

echo ""

# ============ Summary ============
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  VERIFICATION COMPLETE                                      ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "Checklist:"
echo "  [ ] DNS resolves for $DOMAIN"
echo "  [ ] DNS resolves for $SUBDOMAIN"
echo "  [ ] SSL certificate for $SUBDOMAIN"
echo "  [ ] HTTPS connection to $SUBDOMAIN"
echo "  [ ] Application health check passing"
echo "  [ ] API responding"
echo "  [ ] .env configured correctly"
echo "  [ ] Docker services running"
echo ""

log_info "Next steps if issues found:"
echo "  1. DNS not working: Wait 30 minutes, check registrar settings"
echo "  2. SSL error: Run 'certbot certonly --standalone -d $SUBDOMAIN'"
echo "  3. Services not running: Run 'docker compose up -d'"
echo "  4. Still failing: Check logs with 'docker compose logs -f'"
echo ""

log_success "Domain verification script complete!"
