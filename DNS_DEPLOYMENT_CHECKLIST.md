# MAYA SOC Enterprise - Domain & DNS Configuration Checklist

**Date**: April 9, 2026  
**IP Address**: 64.227.137.81  
**Domain**: vaultrap.com  
**Primary Subdomain**: maya.vaultrap.com  
**Status**: ✅ Configuration Guide Complete

---

## 📋 Pre-Deployment Checklist

### Phase 1: Domain & DNS Setup (30 minutes)

#### 1.1: Registrar DNS Configuration
- [ ] Log in to domain registrar (GoDaddy, Namecheap, Route53, etc.)
- [ ] Navigate to DNS settings for vaultrap.com
- [ ] Clear/delete any existing DNS records (if needed)
- [ ] Create A Record for root domain (@)
  - Name: @ (or leave blank)
  - Type: A
  - Value: 64.227.137.81
  - TTL: 3600
- [ ] Create A Record for maya subdomain
  - Name: maya
  - Type: A
  - Value: 64.227.137.81
  - TTL: 3600
- [ ] Create A Record for www subdomain (optional)
  - Name: www
  - Type: A
  - Value: 64.227.137.81
  - TTL: 3600
- [ ] Create A Record for app subdomain (optional)
  - Name: app
  - Type: A
  - Value: 64.227.137.81
  - TTL: 3600
- [ ] Save all DNS changes
- [ ] Note timestamp (for propagation tracking)

**DNS Propagation Checklist**:
- [ ] Wait 5 minutes
  ```bash
  nslookup vaultrap.com
  # Should show: 64.227.137.81 (may not show yet)
  ```
- [ ] Wait 15 minutes
  ```bash
  nslookup maya.vaultrap.com
  # Should show: 64.227.137.81 (may not show yet)
  ```
- [ ] Wait 30 minutes
  ```bash
  nslookup maya.vaultrap.com
  # Should show: 64.227.137.81 (usually resolves by now)
  ```
- [ ] Check propagation online: https://www.whatsmydns.net/
- [ ] All DNS checks show 64.227.137.81

#### 1.2: Verify DNS Resolution Locally
On your local machine, test DNS:

**Windows PowerShell**:
```powershell
# Test DNS resolution
nslookup vaultrap.com
nslookup maya.vaultrap.com
nslookup app.vaultrap.com

# Expected: Address: 64.227.137.81
```

**MacOS/Linux**:
```bash
# Test DNS resolution
nslookup vaultrap.com
dig vaultrap.com
host vaultrap.com

# Expected: 64.227.137.81
```

---

### Phase 2: Server Configuration (20 minutes)

#### 2.1: SSH to Droplet
```bash
# Connect to your droplet by IP (before DNS is updated)
ssh root@64.227.137.81

# Or use domain (after DNS is updated)
ssh root@maya.vaultrap.com
```

Checklist:
- [ ] SSH connection successful
- [ ] You're logged in as root

#### 2.2: Update .env Configuration
```bash
# Navigate to project
cd /root/maya-soc-enterprise

# Edit .env file
nano .env
```

**Update these variables**:
```env
# Domain Configuration
DOMAIN=vaultrap.com
FRONTEND_URL=https://maya.vaultrap.com
API_URL=https://maya.vaultrap.com/api
WEBSOCKET_URL=wss://maya.vaultrap.com/ws

# CORS Configuration
CORS_ORIGINS=["https://maya.vaultrap.com", "https://vaultrap.com", "https://www.vaultrap.com"]

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

Checklist:
- [ ] .env opened successfully
- [ ] DOMAIN set to vaultrap.com
- [ ] FRONTEND_URL set to https://maya.vaultrap.com
- [ ] CORS_ORIGINS includes maya.vaultrap.com
- [ ] File saved

#### 2.3: Update Nginx Configuration
```bash
# Edit nginx configuration
nano /root/maya-soc-enterprise/deployment/nginx.conf
```

Key sections to update:
- [ ] Server name in HTTP section: vaultrap.com maya.vaultrap.com
- [ ] Server name in first HTTPS section: vaultrap.com www.vaultrap.com
- [ ] Server name in maya HTTPS section: maya.vaultrap.com
- [ ] SSL certificate paths:
  - `/etc/letsencrypt/live/vaultrap.com/`
  - `/etc/letsencrypt/live/maya.vaultrap.com/`
- [ ] All proxy settings pointing to correct services
- [ ] WebSocket configuration included

Checklist:
- [ ] File edited successfully
- [ ] All domain names updated
- [ ] SSL paths correct
- [ ] File saved

---

### Phase 3: SSL Certificate Generation (10 minutes)

#### 3.1: Generate SSL Certificates
```bash
# SSH to droplet if not already
ssh root@64.227.137.81

# Or wait until DNS propagates, then use domain
ssh root@maya.vaultrap.com

# Navigate to project
cd /root/maya-soc-enterprise

# Generate MAYA subdomain certificate
certbot certonly --standalone \
  -d maya.vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive

# Generate root domain certificate
certbot certonly --standalone \
  -d vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive

# (Optional) Generate app subdomain certificate
certbot certonly --standalone \
  -d app.vaultrap.com \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive
```

Checklist:
- [ ] Certbot installed (should be from setup.sh)
- [ ] Certificate for maya.vaultrap.com generated
- [ ] Certificate for vaultrap.com generated
- [ ] Certificates saved to /etc/letsencrypt/live/

#### 3.2: Verify Certificates
```bash
# List all certificates
certbot certificates

# Should show:
# - Certificate for maya.vaultrap.com
# - Certificate for vaultrap.com
#   Expiry date: <future date>
```

Checklist:
- [ ] Certificates listed successfully
- [ ] Expiry dates in future (usually 90 days)
- [ ] All domains covered

---

### Phase 4: Docker Services Deployment (5 minutes)

#### 4.1: Deploy Services
```bash
# Ensure you're in project directory
cd /root/maya-soc-enterprise

# Run deployment script
sudo ./deployment/deploy.sh
```

What the script does:
- ✅ Backs up existing database (if any)
- ✅ Pulls latest code
- ✅ Builds Docker images
- ✅ Starts all services
- ✅ Waits for services to be healthy
- ✅ Tests endpoints
- ✅ Cleans up old backups

Checklist:
- [ ] Script ran without errors
- [ ] No "ERROR" messages in output
- [ ] All services started

#### 4.2: Verify Services Running
```bash
# Check all services
docker compose ps

# Expected output (all "Up"):
# CONTAINER ID   IMAGE      NAMES           STATUS
# xxx            postgres   db              Up 2 minutes (healthy)
# yyy            redis      redis           Up 2 minutes (healthy)
# zzz            backend    backend         Up 1 minute (healthy)
# aaa            frontend   frontend        Up 1 minute
# bbb            nginx      nginx           Up 30 seconds
```

Checklist:
- [ ] All containers running (STATUS shows "Up")
- [ ] No "Restarting" or "Exited" status
- [ ] No critical services missing

---

### Phase 5: Verification & Testing (15 minutes)

#### 5.1: Local Verification

**Windows PowerShell** (on your computer):
```powershell
# 1. Test DNS Resolution
nslookup maya.vaultrap.com
# Expected: 64.227.137.81

# 2. Test HTTP (should redirect to HTTPS)
curl -I http://maya.vaultrap.com
# Expected: 301, 302, or 307 redirect

# 3. Test HTTPS
curl -k https://maya.vaultrap.com
# Expected: HTML content from frontend

# 4. Test Health Check
curl -k https://maya.vaultrap.com/health
# Expected: "healthy" response

# 5. Test API
curl -k https://maya.vaultrap.com/api/v1/health
# Expected: JSON status response
```

Checklist:
- [ ] DNS resolves to 64.227.137.81
- [ ] HTTP connection works (redirects)
- [ ] HTTPS connection works
- [ ] Health check responds
- [ ] API responds

**Access in Browser**:
- [ ] Visit https://maya.vaultrap.com in browser
  - Should show MAYA SOC Enterprise frontend
  - May warn about SSL (depending on browser) - this is ok
- [ ] Can see login screen
- [ ] Try login with credentials from .env

Checklist:
- [ ] Frontend loads (no blank page)
- [ ] Login screen visible
- [ ] No "Connection refused" errors
- [ ] No "SSL certificate error" (or acceptable warning)

#### 5.2: Server-Side Verification

**On Droplet** via SSH:
```bash
# SSH to droplet
ssh root@64.227.137.81

# Navigate to project
cd /root/maya-soc-enterprise

# Check service status
docker compose ps

# Check logs for errors
docker compose logs | grep -i error

# Test health endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:5173

# Test Nginx configuration
docker compose exec nginx nginx -t
# Expected: "successful" or "test is successful"

# Check SSL certificates
certbot certificates
# Should show certificates for both domains
```

Checklist:
- [ ] All services running
- [ ] No "error" in logs
- [ ] Health endpoints responding
- [ ] Nginx config valid
- [ ] SSL certificates present

#### 5.3: Run Verification Script (Optional)
```bash
# SSH to droplet
ssh root@64.227.137.81

# Run verification script
cd /root/maya-soc-enterprise
bash deployment/verify-domain.sh

# Should show:
# [✓] DNS resolves to 64.227.137.81
# [✓] SSL certificate valid
# [✓] HTTPS connection successful
# [✓] Application healthy
# [✓] API responding
```

Checklist:
- [ ] Script ran successfully
- [ ] Most checks passed (✓)
- [ ] Any warnings explained
- [ ] No critical errors

---

### Phase 6: Post-Deployment Configuration (20 minutes)

#### 6.1: Change Admin Password
```bash
# Access application
# URL: https://maya.vaultrap.com
# Username: admin
# Password: (from .env - INIT_ADMIN_PASSWORD)

# After login:
1. Click Settings (top right)
2. Account Settings
3. Change Password
4. Use strong password (min 12 chars, mix of types)
5. Save
6. Logout and login with new password
```

Checklist:
- [ ] Logged into application successfully
- [ ] Admin password changed
- [ ] Can login with new password

#### 6.2: Test Core Features
```bash
# Test in browser at https://maya.vaultrap.com:

1. Dashboard
   [ ] Page loads
   [ ] No console errors
   [ ] Charts render

2. Incidents
   [ ] Page loads
   [ ] Can view incidents (if any exist)
   [ ] Real-time updates working

3. Alerts
   [ ] Alert table visible
   [ ] Can filter/search
   [ ] No errors in console

4. Real-time Data
   [ ] WebSocket connection working
   [ ] Data updating in real-time
   [ ] No connection errors in console
```

Checklist:
- [ ] Dashboard loads
- [ ] All pages accessible
- [ ] No console errors
- [ ] Real-time features working

#### 6.3: Configure Monitoring
```bash
# Enable monitoring script
ssh root@64.227.137.81
cd /root/maya-soc-enterprise

# Run monitoring
./deployment/monitor.sh

# Should show:
# - All services healthy
# - Resource usage normal
# - No recent errors
# - API responding
```

Checklist:
- [ ] Monitoring script running
- [ ] All services healthy
- [ ] Resource usage normal (<50% CPU, <60% Memory)
- [ ] No errors in output

#### 6.4: Set Up Backups
**Backups should be automatic** (set up by setup.sh at 2 AM daily)

Verify:
```bash
# Check cron job
crontab -l | grep backup

# Should show:
# 0 2 * * * /root/maya-soc-enterprise/deployment/backup.sh >> /root/logs/backup.log 2>&1

# Check backup directory
ls -lah /root/backups/

# Should show backup files created
```

Checklist:
- [ ] Cron job scheduled
- [ ] Backup directory exists
- [ ] Backups created (at 2 AM)

---

## ✅ Final Verification Checklist

### DNS & Domain
- [ ] DNS records created in registrar
- [ ] DNS propagated worldwide
- [ ] nslookup resolves to 64.227.137.81
- [ ] All subdomains resolve

### SSL & Security
- [ ] SSL certificates generated
- [ ] Certbot shows valid certificates
- [ ] HTTPS accessible
- [ ] No SSL errors in browser (or acceptable warnings)

### Application
- [ ] Frontend loads at https://maya.vaultrap.com
- [ ] API responding at /api/v1/health
- [ ] Can login with admin credentials
- [ ] Admin password changed to new strong password

### Services
- [ ] All Docker containers running
- [ ] Database accessible
- [ ] Backend API working
- [ ] Frontend working
- [ ] Nginx reverse proxy working

### Monitoring & Backups
- [ ] Monitoring script working
- [ ] Backups scheduled (daily at 2 AM)
- [ ] Resource usage normal
- [ ] No critical errors in logs

### Documentation
- [ ] Domain configuration documented
- [ ] Admin password securely stored
- [ ] Access instructions recorded
- [ ] Maintenance procedures understood

---

## 🚨 Common Issues & Quick Fixes

### DNS Not Resolving
```bash
# Issue: nslookup returns "Host not found"
# Solution 1: Wait 30 minutes for propagation
# Solution 2: Check registrar DNS settings
# Solution 3: Use online tool: https://www.whatsmydns.net/
```

### SSL Certificate Error
```bash
# Issue: "ERR_SSL_PROTOCOL_ERROR" or certificate warning
# Solution: 
certbot renew --force-renewal
docker compose restart nginx
```

### 502 Bad Gateway
```bash
# Issue: Backend not responding
# Solution:
docker compose ps | grep backend
docker compose logs backend
docker compose restart backend
```

### Connection Refused
```bash
# Issue: Can't connect to domain
# Solution 1: Check DNS resolved first
# Solution 2: Check droplet firewall allows port 443
# Solution 3: Check Nginx is running
docker compose ps | grep nginx
```

### Slow Loading
```bash
# Issue: Application loads slowly
# Solution:
docker stats  # Check CPU/Memory
docker compose logs backend | grep -i error  # Check errors
```

---

## 📞 Support Commands

```bash
# SSH to droplet
ssh root@64.227.137.81
ssh root@maya.vaultrap.com

# Project directory
cd /root/maya-soc-enterprise

# Check services
docker compose ps

# View logs
docker compose logs -f
docker compose logs backend
docker compose logs nginx

# Monitor resources
docker stats
./deployment/monitor.sh

# Test connectivity
curl https://maya.vaultrap.com/health
nslookup maya.vaultrap.com

# Create backup
./deployment/backup.sh

# Deploy updates
sudo ./deployment/deploy.sh
```

---

## 📝 Notes & Custom Settings

### Your Configuration
```
IP Address:      64.227.137.81
Root Domain:     vaultrap.com
Primary Domain:  maya.vaultrap.com
Email:           [your-email@gmail.com]
Admin User:      admin
Admin Password:  [CHANGE SIZE AFTER FIRST LOGIN]
```

### Important Files
```
.env                          - Configuration (NEVER COMMIT)
nginx.conf                    - Web server config
docker-compose.yml            - Service definitions
deployment/deploy.sh          - Deployment command
deployment/backup.sh          - Backup command
deployment/monitor.sh         - Monitoring command
```

---

## ✨ Success Indicators

✅ **You'll know it's working when:**
- DNS resolves to 64.227.137.81
- Browser shows HTTPS lock (or acceptable warnings)
- Frontend loads with MAYA SOC logo
- Can log in with admin credentials
- Dashboard shows real-time data
- All services in `docker compose ps` show "Up"

---

**Status**: ✅ **READY FOR DEPLOYMENT**

**Next Steps**:
1. Configure DNS records with registrar
2. Wait for DNS propagation (30 minutes to 2 hours)
3. Follow "Phase 2" through "Phase 6" above
4. Test all endpoints
5. Change admin password
6. Your application is LIVE! 🚀

---

**Questions?** See [DNS_AND_DOMAIN_SETUP.md](../DNS_AND_DOMAIN_SETUP.md) or [deployment/TROUBLESHOOTING.md](../deployment/TROUBLESHOOTING.md)
