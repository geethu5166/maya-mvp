# 🚀 MAYA SOC Enterprise - Deployment Guide

**Welcome!** This folder contains everything you need to deploy MAYA SOC Enterprise to production.

---

## 📂 Files in This Directory

### 📖 Documentation
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step deployment checklist
- **QUICK_REFERENCE.md** - Quick command reference for day-to-day operations
- **TROUBLESHOOTING.md** - Solutions for common issues

### 🔧 Scripts
- **deploy.sh** - Main automated deployment script
- **backup.sh** - Database backup script
- **monitor.sh** - Real-time system monitoring
- **setup.sh** - Initial server setup (run once)

### ⚙️ Configuration
- **nginx.conf** - Web server configuration (SSL, routing, security)

---

## 🎯 Quick Start (5 Minutes)

### First Time: Setup Server
```bash
# 1. SSH into your DigitalOcean droplet
ssh root@maya.vaultrap.com

# 2. Run setup script
sudo bash /root/maya-mvp/deployment/setup.sh

# 3. Configure environment
nano /root/maya-mvp/.env

# 4. Generate SSL certificate
certbot certonly --standalone -d maya.vaultrap.com --email your@email.com

# 5. Deploy application
sudo /root/maya-mvp/deployment/deploy.sh

# ✅ Done! Access at https://maya.vaultrap.com
```

### Subsequent Deployments: Update Application
```bash
# Pull latest code and redeploy
sudo /root/maya-mvp/deployment/deploy.sh
```

---

## 📖 Documentation Files

### Start Here
1. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** (30 min read)
   - Pre-deployment checklist
   - Step-by-step deployment process
   - Post-deployment verification
   - Success metrics

### Day-to-Day Operations
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (2 min read)
   - Common commands
   - Quick lookup for operators
   - Emergency procedures
   - Bookmark this!

### Need Help?
3. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** (search as needed)
   - Common issues and solutions
   - Debugging techniques
   - Emergency recovery
   - Advanced diagnostics

---

## 🔧 Scripts Reference

### 1. setup.sh - Initial Server Setup
**Run once on fresh DigitalOcean droplet**
```bash
sudo bash /root/maya-mvp/deployment/setup.sh
```
**What it does:**
- Updates system packages
- Installs Docker and Docker Compose
- Installs SSL tools
- Creates project directories
- Clones GitHub repository
- Schedules automated backups
- Configures certificate renewal

**Time**: ~15 minutes

---

### 2. deploy.sh - Deploy Application
**Run to deploy/update application**
```bash
sudo /root/maya-mvp/deployment/deploy.sh
```
**What it does:**
- Backs up current database
- Pulls latest code from GitHub
- Builds Docker images
- Starts all services
- Waits for services to be healthy
- Verifies deployment
- Cleans up old backups

**Time**: ~2 minutes

**Safe to run multiple times!**

---

### 3. backup.sh - Create Database Backup
**Run manually or via cron (automatic daily at 2 AM)**
```bash
/root/maya-mvp/deployment/backup.sh
```
**What it does:**
- Creates database dump
- Compresses backup
- Stores in /root/backups/
- Cleans up old backups (>30 days)

**Output**: `/root/backups/maya_soc_YYYYMMDD_HHMMSS.sql.gz`

---

### 4. monitor.sh - Real-Time Monitoring
**Run to monitor services**
```bash
/root/maya-mvp/deployment/monitor.sh
```
**What it shows:**
- Service status
- Resource usage (CPU, Memory, Disk)
- API health checks
- Recent errors
- Database statistics

**Refreshes**: Every 10 seconds (Press Ctrl+C to exit)

---

## ⚙️ Configuration

### nginx.conf - Web Server Configuration
**Location**: `/root/maya-mvp/deployment/nginx.conf`

**What it does:**
- Handles HTTPS/SSL for your domain
- Routes traffic to frontend and backend
- Applies security headers
- Enables gzip compression
- Handles WebSocket connections
- Redirects HTTP to HTTPS

**Key sections:**
- Port 80 (HTTP) → Redirects to HTTPS
- Port 443 (HTTPS) → Serves frontend/API/WebSocket
- Security headers for protection
- SSL certificate configuration

---

## 🏗️ Complete Architecture

```
Your DigitalOcean Droplet (maya.vaultrap.com)
│
├── Nginx (Port 443 HTTPS)
│   ├── Routes / → Frontend (React)
│   ├── Routes /api → Backend (FastAPI)
│   └── Routes /ws → WebSocket
│
├── Frontend (Port 5173)
│   ├── React 18
│   ├── TypeScript
│   ├── Tailwind CSS
│   └── Real-time charts
│
├── Backend (Port 8000)
│   ├── FastAPI
│   ├── ML models
│   ├── Kafka streaming
│   └── REST API
│
├── Database
│   ├── PostgreSQL
│   ├── Redis (cache)
│   └── Kafka (messaging)
│
└── Backups (/root/backups/)
    └── Daily automatic backup
```

---

## 🔄 Deployment Flow

```
1. Edit .env
   ↓
2. Run setup.sh (once)
   ↓
3. Generate SSL certificate
   ↓
4. Run deploy.sh
   ├── Backup database
   ├── Pull code
   ├── Build images
   ├── Start services
   ├── Wait for health
   └── Verify deployment
   ↓
5. ✅ Application live at https://maya.vaultrap.com
```

---

## 📊 Service Details

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| PostgreSQL | postgres:latest | 5432 | Primary database |
| Redis | redis:latest | 6379 | Cache & sessions |
| Kafka | confluentinc/cp-kafka | 9092 | Message streaming |
| Backend | Custom (FastAPI) | 8000 | REST API + WebSocket |
| Frontend | Custom (React) | 5173 | Web interface |
| Nginx | nginx:latest | 443 | Reverse proxy + SSL |

---

## ✨ Features

✅ **Production-Ready**
- Automated deployment
- TLS/SSL encryption
- Database backups
- Health monitoring
- Error logging

✅ **Easy Operations**
- Simple one-command deployment
- Automated backups
- Real-time monitoring
- Troubleshooting guides

✅ **Secure**
- HTTPS enforced
- Security headers
- No hardcoded secrets
- Firewall integration

✅ **Scalable**
- Docker containers
- Kubernetes-ready
- Load balancer compatible
- Horizontal scaling support

---

## 🎓 Common Tasks

### Check Everything Works
```bash
docker compose ps
docker compose logs
curl https://maya.vaultrap.com/health
```

### Restart Application
```bash
docker compose restart
```

### View Logs
```bash
docker compose logs -f
```

### Create Backup
```bash
./backup.sh
```

### Monitor Resources
```bash
./monitor.sh
```

### Stop Application
```bash
docker compose down
```

---

## 🆘 Need Help?

1. **Check Logs**: `docker compose logs`
2. **View Status**: `docker compose ps`
3. **Check QUICK_REFERENCE.md**: Common commands
4. **Check TROUBLESHOOTING.md**: Common issues
5. **Check DEPLOYMENT_CHECKLIST.md**: Step-by-step guide

---

## 🔐 Security Notes

- ✅ SSL/TLS enabled
- ✅ Security headers added
- ✅ Database password required
- ✅ API authentication enabled
- ✅ WebSocket secured
- ✅ Automated backups

**Before production:**
- [ ] Change admin password
- [ ] Update .env with strong passwords
- [ ] Configure firewall rules
- [ ] Enable 2FA if available
- [ ] Review access logs

---

## 📈 Monitoring & Maintenance

### Daily
- Check application is responding
- Review error logs
- Monitor disk space

### Weekly
- Review logs for patterns
- Test backup restoration
- Check resource usage

### Monthly
- Update documentation
- Review security
- Performance tuning
- Capacity planning

---

## 💰 Costs

**Recommended Setup**: ~$5/month
- DigitalOcean Droplet (small): $5
- Domain (yearly): ~$10
- SSL Certificate: Free (Let's Encrypt)

**Scale Up as Needed**
- 2GB Droplet: $12/month
- High-performance: $24/month
- Load balancer: +$10/month
- CDN: +$10/month

---

## 🎯 What's Next?

1. **Deploy** - Follow DEPLOYMENT_CHECKLIST.md
2. **Monitor** - Use monitor.sh regularly
3. **Backup** - Automatic daily, no action needed
4. **Update** - Run deploy.sh for new versions
5. **Scale** - Add more droplets as needed

---

## 📚 Full Documentation

For complete documentation including:
- Architecture details
- Performance tuning
- Scaling guide
- Security hardening
- Troubleshooting deep dives

See: **[../COMPLETE_DEPLOYMENT_GUIDE.md](../COMPLETE_DEPLOYMENT_GUIDE.md)**

---

## 🚀 Ready to Deploy?

Start with [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) →

Good luck! 🎉

---

**Questions?** Check the documentation files above or review the logs with `docker compose logs`
