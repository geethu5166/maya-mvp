# 🌐 MAYA SOC Enterprise - Domain & DNS Configuration Guide

**Date**: April 9, 2026  
**IP Address**: 64.227.137.81  
**Domain**: vaultrap.com  
**Subdomain**: maya.vaultrap.com (or app.vaultrap.com)

---

## 📋 DNS Records to Create

### Your Droplet Information
- **IP Address**: 64.227.137.81
- **Domain**: vaultrap.com
- **Subdomain Setup**: maya.vaultrap.com → 64.227.137.81

---

## ✅ Step 1: Configure DNS Records with Your Registrar

### Option A: Simple Setup (Recommended for Testing)

**DNS Record 1 - Point Root Domain to IP**
```
Type: A
Name: @  (or leave blank for root)
Value: 64.227.137.81
TTL: 3600
```

**DNS Record 2 - Point maya subdomain to IP**
```
Type: A
Name: maya
Value: 64.227.137.81
TTL: 3600
```

**DNS Record 3 - Point app subdomain to IP (Optional)**
```
Type: A
Name: app
Value: 64.227.137.81
TTL: 3600
```

### DNS Records Summary

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 64.227.137.81 | 3600 |
| A | maya | 64.227.137.81 | 3600 |
| A | app | 64.227.137.81 | 3600 |
| A | www | 64.227.137.81 | 3600 |

---

## 🔧 Step 2: Update Your .env Configuration

Edit `/root/maya-soc-enterprise/.env`:

```env
# Domain Configuration
DOMAIN=vaultrap.com
FRONTEND_URL=https://maya.vaultrap.com
API_URL=https://maya.vaultrap.com/api
WEBSOCKET_URL=wss://maya.vaultrap.com/ws

# CORS Configuration
CORS_ORIGINS=["https://maya.vaultrap.com", "https://vaultrap.com", "https://www.vaultrap.com"]

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🔐 Step 3: Update SSL Certificate Generation

When you have the DNS records set up, generate SSL certificates:

```bash
# For maya subdomain
certbot certonly --standalone \
  -d maya.vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive

# For root domain
certbot certonly --standalone \
  -d vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive

# For app subdomain (if using)
certbot certonly --standalone \
  -d app.vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive
```

---

## 🌗 Step 4: Update Nginx Configuration

Edit `/root/maya-soc-enterprise/deployment/nginx.conf`:

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 768;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # HTTP Redirect to HTTPS
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name vaultrap.com maya.vaultrap.com app.vaultrap.com www.vaultrap.com;

        # Let's Encrypt verification
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all HTTP to HTTPS
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS Server - Main Domain
    server {
        listen 443 ssl http2 default_server;
        listen [::]:443 ssl http2 default_server;
        server_name vaultrap.com www.vaultrap.com;

        # SSL Certificates
        ssl_certificate /etc/letsencrypt/live/vaultrap.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/vaultrap.com/privkey.pem;

        # SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Root domain redirects to maya subdomain
        location / {
            return 301 https://maya.vaultrap.com$request_uri;
        }
    }

    # HTTPS Server - MAYA Subdomain
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name maya.vaultrap.com;

        # SSL Certificates
        ssl_certificate /etc/letsencrypt/live/maya.vaultrap.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/maya.vaultrap.com/privkey.pem;

        # SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Frontend
        location / {
            proxy_pass http://frontend:5173;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # API Backend
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # WebSocket
        location /ws {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }

    # HTTPS Server - APP Subdomain (Optional)
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name app.vaultrap.com;

        # SSL Certificates
        ssl_certificate /etc/letsencrypt/live/app.vaultrap.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/app.vaultrap.com/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Redirect to maya subdomain
        location / {
            return 301 https://maya.vaultrap.com$request_uri;
        }
    }
}
```

---

## 📝 Step 5: Docker Compose Update

Update `docker-compose.yml` environment variables:

```yaml
services:
  backend:
    environment:
      - DOMAIN=maya.vaultrap.com
      - FRONTEND_URL=https://maya.vaultrap.com
      - CORS_ORIGINS=["https://maya.vaultrap.com"]
      - API_PORT=8000

  frontend:
    environment:
      - VITE_API_URL=https://maya.vaultrap.com/api
      - VITE_WS_URL=wss://maya.vaultrap.com/ws
```

---

## ✅ Step 6: Verification Checklist

### DNS Verification
```bash
# Check DNS is resolving
nslookup vaultrap.com
nslookup maya.vaultrap.com

# Should return: 64.227.137.81

# Alternative check
dig vaultrap.com
dig maya.vaultrap.com

# Alternative check
host vaultrap.com
host maya.vaultrap.com
```

### DNS Propagation Check
```bash
# Using online tools (visit in browser):
# https://www.whatsmydns.net/
# Search for: vaultrap.com or maya.vaultrap.com
```

### Certificate Verification
```bash
# Check certificates are valid
certbot certificates

# Expected output:
# - Certificate for maya.vaultrap.com found
# - Certificate for vaultrap.com found

# Test certificate
openssl s_client -connect maya.vaultrap.com:443 -servername maya.vaultrap.com

# Test with curl
curl -v https://maya.vaultrap.com
```

### Nginx Configuration Verification
```bash
# SSH to droplet
ssh root@64.227.137.81

# Go to project
cd /root/maya-soc-enterprise

# Test Nginx config syntax
docker compose exec nginx nginx -t

# Should show: "successful" or "test is successful"
```

### Service Verification
```bash
# Check all services running
docker compose ps

# All should show "Up"

# Test backend health
curl https://maya.vaultrap.com/health

# Test API
curl https://maya.vaultrap.com/api/v1/health

# Test frontend (should return HTML)
curl https://maya.vaultrap.com
```

---

## 🚨 Common Errors & Solutions

### ❌ Error: "Connection refused"
**Cause**: Nginx not running or port blocked  
**Solution**:
```bash
docker compose restart nginx
docker compose logs nginx
```

### ❌ Error: "SSL certificate problem"
**Cause**: Certificate not found or misconfigured  
**Solution**:
```bash
# List certificates
certbot certificates

# If missing, generate:
certbot certonly --standalone -d maya.vaultrap.com

# Update Nginx config path if needed
```

### ❌ Error: "Bad gateway" (502)
**Cause**: Backend/Frontend not running  
**Solution**:
```bash
docker compose ps
docker compose restart backend frontend
docker compose logs backend
docker compose logs frontend
```

### ❌ Error: "This site can't be reached"
**Cause**: DNS not propagated yet  
**Solution**:
```bash
# Wait 15-30 minutes for DNS to propagate
# Check DNS resolution:
nslookup maya.vaultrap.com

# Should resolve to: 64.227.137.81
```

### ❌ Error: "Name does not resolve"
**Cause**: DNS misconfigured  
**Solution**:
1. Check DNS records at registrar (GoDaddy, Namecheap, etc.)
2. Verify A records point to 64.227.137.81
3. Wait 30 minutes for propagation
4. Test with: `nslookup maya.vaultrap.com`

### ❌ Error: "ERR_SSL_PROTOCOL_ERROR"
**Cause**: SSL/TLS issue  
**Solution**:
```bash
# Check certificate
openssl s_client -connect maya.vaultrap.com:443

# Update certificate if needed
certbot renew --force-renewal
docker compose restart nginx
```

---

## 🔄 Step 7: Full Deployment with New Domain

```bash
# 1. SSH to droplet
ssh root@64.227.137.81

# 2. Navigate to project
cd /root/maya-soc-enterprise

# 3. Update .env with new domain
nano .env

# 4. Update Nginx config
nano deployment/nginx.conf

# 5. Generate SSL certificates
certbot certonly --standalone -d vaultrap.com -d maya.vaultrap.com -d www.vaultrap.com

# 6. Restart services with new config
docker compose down
docker compose up -d

# 7. Verify everything
docker compose ps
curl https://maya.vaultrap.com/health

# 8. View logs
docker compose logs -f nginx
```

---

## 📊 Domain Configuration Summary

```
┌─────────────────────────────────────────────────┐
│ Domain Structure                                │
├─────────────────────────────────────────────────┤
│                                                  │
│  vaultrap.com → Redirects to → maya.vaultrap.com │
│  │                                               │
│  ├── DNS A Record: 64.227.137.81               │
│  ├── SSL: Separate certificate                  │
│  └── Routes: → HTTPS redirect to maya           │
│                                                  │
│  maya.vaultrap.com (MAIN APPLICATION)           │
│  │                                               │
│  ├── DNS A Record: 64.227.137.81               │
│  ├── SSL: Primary certificate                   │
│  ├── Port 443: HTTPS                            │
│  ├── Routes:                                    │
│  │   ├── / → Frontend (React)                  │
│  │   ├── /api → Backend (FastAPI)              │
│  │   └── /ws → WebSocket                       │
│  └── Status: https://maya.vaultrap.com/health │
│                                                  │
│  app.vaultrap.com (Optional alias)              │
│  │                                               │
│  └── Redirects to → maya.vaultrap.com          │
│                                                  │
│  www.vaultrap.com (Optional alias)              │
│  │                                               │
│  └── Redirects to → maya.vaultrap.com          │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## ✨ Access URLs

After setup, your application is accessible at:

| URL | Purpose | Status |
|-----|---------|--------|
| https://maya.vaultrap.com | Main application | 🟢 Primary |
| https://maya.vaultrap.com/health | Health check | 🟢 Monitor |
| https://maya.vaultrap.com/api/v1 | API endpoint | 🟢 REST API |
| https://maya.vaultrap.com/api/v1/health | API health | 🟢 Status |
| https://vaultrap.com | Root domain | 🟡 Redirect |
| https://app.vaultrap.com | App alias | 🟡 Redirect |

---

## 🔍 DNS Propagation Timeline

| Time | Status |
|------|--------|
| 0-5 min | DNS changes made |
| 5-15 min | Some checks pass |
| 15-30 min | Most checks pass |
| 30-48 hours | Full propagation (usually 1-2 hours) |

**Check propagation**: https://www.whatsmydns.net/

---

## 🚀 Complete Deployment Command

After DNS is set up, run this complete deployment:

```bash
# SSH to droplet
ssh root@64.227.137.81

# Navigate to project
cd /root/maya-soc-enterprise

# Run complete deployment script
sudo ./deployment/deploy.sh
```

The script will:
✅ Backup database  
✅ Pull latest code  
✅ Build Docker images  
✅ Start services  
✅ Test health endpoints  
✅ Verify configuration  

---

## 📞 Quick Support

**DNS not resolving?**
- Wait 30 minutes for propagation
- Check registrar DNS settings
- Verify A records point to 64.227.137.81

**SSL certificate error?**
```bash
certbot certificates
certbot renew --force-renewal
docker compose restart nginx
```

**Can't access application?**
```bash
# Check services
docker compose ps

# Check logs
docker compose logs -f nginx
docker compose logs -f backend

# Test connectivity
curl https://maya.vaultrap.com/health
```

**Need help?**
- See: [deployment/TROUBLESHOOTING.md](../deployment/TROUBLESHOOTING.md)
- Reference: [COMPLETE_DEPLOYMENT_GUIDE.md](../COMPLETE_DEPLOYMENT_GUIDE.md)

---

**Your MAYA SOC Enterprise is now configured for production with vaultrap.com! 🚀**

Next steps:
1. ✅ Set DNS records with registrar
2. ✅ Wait for DNS propagation (30 min)
3. ✅ Generate SSL certificates
4. ✅ Run deployment script
5. ✅ Access at https://maya.vaultrap.com
