# 🎯 MAYA SOC ENTERPRISE - Quick Reference Card

Quick command reference for production deployment and management.

---

## 📋 Table of Contents
1. [Deployment](#deployment)
2. [Service Management](#service-management)
3. [Database Management](#database-management)
4. [Monitoring & Logs](#monitoring--logs)
5. [Backup & Recovery](#backup--recovery)
6. [Troubleshooting](#troubleshooting)
7. [Emergency](#emergency)

---

## 🚀 Deployment

### Initial Setup (First Time Only)
```bash
# Run on fresh DigitalOcean droplet
sudo bash <(curl -s https://raw.githubusercontent.com/YOUR_USERNAME/maya-mvp/main/deployment/setup.sh)

# Then edit configuration
nano /root/maya-mvp/.env

# Generate SSL certificate
certbot certonly --standalone -d maya.vaultrap.com --email your-email@example.com

# Deploy application
sudo /root/maya-mvp/deployment/deploy.sh
```

### Redeployment (Updates)
```bash
# Pull latest code and redeploy
sudo /root/maya-mvp/deployment/deploy.sh

# What it does:
# - Backups database
# - Pulls latest code
# - Rebuilds Docker images
# - Restarts services
# - Verifies health
```

---

## 🎮 Service Management

### Status
```bash
# See all services
docker compose ps

# Expected output: All services should be "Up"
CONTAINER ID   IMAGE              NAMES         STATUS
xxx            postgres:latest    db            Up 5 minutes (healthy)
yyy            redis:latest       redis         Up 5 minutes (healthy)
zzz            backend            backend       Up 4 minutes (healthy)
aaa            frontend           frontend      Up 4 minutes
```

### Start/Stop
```bash
docker compose up -d              # Start all
docker compose down               # Stop all
docker compose restart            # Restart all
docker compose restart backend    # Restart specific service
```

### Update Single Service
```bash
# Pull and rebuild one service
docker compose build --no-cache backend
docker compose up -d backend
```

---

## 🗄️ Database Management

### Connect to Database
```bash
docker compose exec db psql -U soc_user -d maya_soc

# Useful commands inside psql:
\dt                               # List tables
\du                               # List users
SELECT count(*) FROM incidents;   # Count records
\q                                # Quit
```

### Database Size
```bash
docker compose exec db psql -U soc_user -d maya_soc -c \
  "SELECT pg_size_pretty(pg_database_size('maya_soc'));"
```

### Active Connections
```bash
docker compose exec db psql -U soc_user -d maya_soc -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

### Reset Administrator Password
```bash
# Interactive reset
docker compose exec backend python -c "
from app.core.security import hash_password
import getpass
pwd = getpass.getpass('Enter new password: ')
print(repr(hash_password(pwd)))
"
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend
docker compose logs db

# Follow new logs (real-time)
docker compose logs -f

# Last 50 lines
docker compose logs --tail 50

# Last 10 minutes
docker compose logs --since 10m
```

### Search Logs
```bash
# Find errors
docker compose logs | grep -i error

# Find warnings
docker compose logs | grep -i warning

# Find patterns in backend
docker compose logs backend | grep "database"
```

### Resource Usage
```bash
# Real-time stats
docker stats

# One-time snapshot
docker stats --no-stream

# Specific service
docker stats backend

# Output format
CONTAINER   CPU%    MEM%    MEM     NET I/O
backend     2.5%    150MiB  15%     1.2MiB / 890KiB
frontend    0.1%    45MiB   4%      234KiB / 156KiB
db          5.2%    256MiB  25%     2.1MiB / 1.8MiB
```

### System Health
```bash
# Disk space
df -h

# Memory
free -h

# Process CPU
top -o %CPU

# I/O
iostat 1 5

# Network
netstat -tulpn | grep LISTEN
```

---

## 💾 Backup & Recovery

### Manual Backup
```bash
/root/maya-mvp/deployment/backup.sh

# Creates: /root/backups/maya_soc_YYYYMMDD_HHMMSS.sql.gz
```

### List Backups
```bash
ls -lah /root/backups/
```

### Restore from Backup
```bash
# Restore latest backup
LATEST=$(ls -t /root/backups/*.sql.gz | head -1)
gunzip -c $LATEST | docker compose exec -T db psql -U soc_user -d maya_soc

# Restore specific backup
BACKUP="/root/backups/maya_soc_20260409_020000.sql.gz"
gunzip -c $BACKUP | docker compose exec -T db psql -U soc_user -d maya_soc
```

### Schedule Automatic Backup
```bash
# Already configured by setup script
# Check cron job
crontab -l | grep backup

# Should output:
# 0 2 * * * /root/maya-mvp/deployment/backup.sh >> /root/logs/backup.log 2>&1
```

---

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs backend

# Common fixes
docker compose restart backend
docker compose down && docker compose up -d

# Full reset
docker compose down
docker system prune -a
docker compose up -d --build
```

### Database Connection Error
```bash
# Check database is running
docker compose ps db

# Test connection
docker compose exec db psql -U soc_user -d maya_soc -c "SELECT 1;"

# Check credentials in .env
grep POSTGRES /root/maya-mvp/.env
```

### Out of Disk Space
```bash
# Check space
df -h

# Clean docker
docker system prune -a

# Clean logs
docker compose logs --tail 0 > /dev/null
```

### High Memory Usage
```bash
# Show memory hogs
docker stats --no-stream | sort -k 5 -hr

# Restart service
docker compose restart backend
```

### API Not Responding
```bash
# Check backend running
curl http://localhost:8000/health

# View errors
docker compose logs backend | grep -i error

# Restart
docker compose restart backend
```

### Frontend Blank Page
```bash
# Check frontend running
curl http://localhost:5173

# Check Nginx
docker compose ps nginx

# View errors
docker compose logs nginx

# Check domain/SSL
curl -v https://maya.vaultrap.com
```

---

## 🚨 Emergency

### Stop Everything (Emergency Stop)
```bash
docker compose down
```

### Kill Stuck Process
```bash
# Find PID
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Complete Reset (Data Loss!)
```bash
docker compose down
docker volume rm maya-mvp_postgres_data
docker volume rm maya-mvp_redis_data
docker system prune -a
docker compose up -d
```

### Restore Full Backup (Recovery)
```bash
# Restore database
BACKUP="/root/backups/maya_soc_20260409_020000.sql.gz"
gunzip -c $BACKUP | docker compose exec -T db psql -U soc_user -d maya_soc

# Restart services
docker compose restart backend
```

---

## 🔗 Important URLs

| Service | URL | Check Command |
|---------|-----|---|
| Frontend | https://maya.vaultrap.com | curl -k https://maya.vaultrap.com |
| API | https://maya.vaultrap.com/api | curl -k https://maya.vaultrap.com/health |
| Health Check | https://maya.vaultrap.com/health | curl -k https://maya.vaultrap.com/health |
| Backend Internal | http://localhost:8000 | curl http://localhost:8000/health |
| Database | localhost:5432 | telnet localhost 5432 |
| Redis | localhost:6379 | redis-cli ping |

---

## 🔐 Important Locations

```
/root/maya-mvp/          # Main project
  .env                              # Configuration (NEVER COMMIT)
  docker-compose.yml                # Service definitions
  deployment/
    deploy.sh                        # Deployment script
    backup.sh                        # Backup script
    monitor.sh                       # Monitoring tool
    nginx.conf                       # Web server config
    setup.sh                         # Server setup
    TROUBLESHOOTING.md              # Help guide
    DEPLOYMENT_CHECKLIST.md         # This checklist

/root/backups/                       # Database backups
/root/logs/                          # Application logs
/etc/letsencrypt/                    # SSL certificates
/var/lib/docker/                     # Docker data
```

---

## 📞 Common Support Questions

**Q: How do I see what's failing?**
```bash
docker compose logs
```

**Q: How do I restart the app?**
```bash
docker compose restart
```

**Q: How do I check if it's working?**
```bash
docker compose ps
curl https://maya.vaultrap.com/health
```

**Q: How do I get my data back?**
```bash
/root/maya-mvp/deployment/backup.sh  # Create backup
# Backups auto-restore on deployment
```

**Q: Why is it slow?**
```bash
docker stats
```

**Q: Why is it using lots of disk?**
```bash
df -h
ls -lah /root/backups/
```

---

## ⏱️ Quick Actions

| Task | Command | Time |
|------|---------|------|
| Check status | docker compose ps | 1 sec |
| View logs | docker compose logs -f | 1 sec |
| Restart app | docker compose restart | 10 sec |
| Backup database | /root/maya-mvp/deployment/backup.sh | 30 sec |
| Deploy update | sudo /root/maya-mvp/deployment/deploy.sh | 2 min |
| Full reset | docker compose down && docker compose up -d | 1 min |

---

**Need more help? See COMPLETE_DEPLOYMENT_GUIDE.md and TROUBLESHOOTING.md**
