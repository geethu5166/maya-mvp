# 📋 MAYA SOC ENTERPRISE - Deployment Checklist

**Project**: MAYA SOC Enterprise v3.0  
**Status**: Ready for Production  
**Date**: April 9, 2026  

---

## ✅ Pre-Deployment Checklist

### Infrastructure Setup
- [ ] DigitalOcean account created
- [ ] Droplet provisioned (minimum $5/month)
- [ ] Domain registered (app.vaultrap.com)
- [ ] DNS records pointing to droplet IP
- [ ] SSH access configured
- [ ] Firewall rules configured (22, 80, 443 open)

### Code Preparation
- [ ] All code pushed to GitHub main branch
- [ ] No secrets in .env or config files
- [ ] .env.example updated with all variables
- [ ] docker-compose.yml tested locally
- [ ] All tests passing
- [ ] README.md and documentation updated

### Security
- [ ] Strong passwords generated (min 32 chars)
- [ ] JWT secret key generated
- [ ] Database password set
- [ ] Redis password set
- [ ] No hardcoded secrets in code
- [ ] SSL certificate plan (Let's Encrypt)
- [ ] Firewall rules reviewed
- [ ] HTTPS enforced

---

## 🚀 Deployment Steps

### Day 1: Initial Server Setup

**Step 1: Access Server** (5 min)
- [ ] SSH into droplet
- [ ] Update system
- [ ] Install essential tools

**Step 2: Run Setup Script** (15 min)
```bash
sudo bash /root/maya-soc-enterprise/deployment/setup.sh
```
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Repository cloned
- [ ] Backup automation configured
- [ ] Cron jobs scheduled

**Step 3: Configure Environment** (10 min)
```bash
nano /root/maya-soc-enterprise/.env
```
- [ ] Set POSTGRES_PASSWORD
- [ ] Set REDIS_PASSWORD  
- [ ] Set SECRET_KEY
- [ ] Set DOMAIN=app.vaultrap.com
- [ ] Save and exit

**Step 4: Generate SSL Certificate** (10 min)
```bash
certbot certonly --standalone -d app.vaultrap.com --email your-email@example.com --agree-tos
```
- [ ] Certificate generated successfully
- [ ] Located at /etc/letsencrypt/live/app.vaultrap.com/

**Step 5: Start Deployment** (30 min)
```bash
sudo /root/maya-soc-enterprise/deployment/deploy.sh
```
- [ ] All services starting
- [ ] No critical errors in logs
- [ ] Database initialized

**Result**: ✅ Application should be accessible at https://app.vaultrap.com

---

### Day 2: Verification & Testing

**Step 1: Verify Services** (10 min)
```bash
docker compose ps
docker compose logs -f
```
- [ ] All containers running (docker compose ps shows "Up")
- [ ] No error messages in logs
- [ ] Services are healthy

**Step 2: Test Frontend** (5 min)
- [ ] Access https://app.vaultrap.com
- [ ] Login with admin/admin123
- [ ] Dashboard loads
- [ ] Real-time data flowing
- [ ] WebSocket connection working

**Step 3: Test API** (5 min)
```bash
curl https://app.vaultrap.com/api/v1/health
curl https://app.vaultrap.com/api/v1/incidents
```
- [ ] API endpoints responding
- [ ] Authentication working
- [ ] Data retrievable

**Step 4: Test Database** (5 min)
```bash
docker compose exec db psql -U maya_user -d maya_soc -c "SELECT count(*) FROM incidents;"
```
- [ ] Database connections working
- [ ] Data persisting
- [ ] Queries executing

**Step 5: Test Backups** (5 min)
```bash
/root/maya-soc-enterprise/deployment/backup.sh
ls -lh /root/backups/
```
- [ ] Backup created successfully
- [ ] Backup file size reasonable (>1MB)
- [ ] Cron job will run automatically

**Step 6: Monitoring** (5 min)
```bash
/root/maya-soc-enterprise/deployment/monitor.sh
```
- [ ] All services healthy
- [ ] Resource usage normal
- [ ] No errors displayed

**Result**: ✅ Application fully operational

---

### Day 3: Post-Deployment Configuration

**Step 1: Change Default Admin Password**
- [ ] Login to application
- [ ] Go to Settings
- [ ] Change admin password
- [ ] Use strong password (min 12 chars)

**Step 2: Configure Alerts (Optional)**
- [ ] Set up email alerts
- [ ] Configure Slack integration
- [ ] Set up PagerDuty (if applicable)

**Step 3: Load Initial Data**
- [ ] Import sample security events (if needed)
- [ ] Configure data sources
- [ ] Set up real-time connections

**Step 4: Test Access Controls**
- [ ] Create additional users
- [ ] Test role-based access
- [ ] Verify permissions working

**Step 5: Documentation**
- [ ] Document admin password (in secure location)
- [ ] Create runbook for common tasks
- [ ] Document incident escalation procedures

---

## 🔄 Post-Deployment Tasks

### Weekly
- [ ] Review logs for errors
- [ ] Check disk space usage
- [ ] Monitor resource usage
- [ ] Test backup restoration
- [ ] Review security alerts

### Monthly
- [ ] Review user access
- [ ] Update documentation
- [ ] Performance tuning
- [ ] Capacity planning
- [ ] Security audit

### Quarterly
- [ ] Major version updates
- [ ] Infrastructure optimization
- [ ] Disaster recovery drill
- [ ] Security assessment
- [ ] Cost review

---

## 🆔 Access Credentials

### Initial Login
- **URL**: https://app.vaultrap.com
- **Username**: admin
- **Password**: (from INIT_ADMIN_PASSWORD in .env)

### Server Access
```bash
ssh root@app.vaultrap.com
# Or via DigitalOcean console
```

### Database (if needed)
```bash
docker exec -it maya-db psql -U maya_user -d maya_soc
```

---

## 📊 Service URLs

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| Frontend | https://app.vaultrap.com | 443 | Web interface |
| API | https://app.vaultrap.com/api/v1 | 443 | REST API |
| Health | https://app.vaultrap.com/health | 443 | Status check |
| Backend (internal) | http://localhost:8000 | 8000 | FastAPI |
| Frontend (internal) | http://localhost:5173 | 5173 | Vite dev |
| PostgreSQL | localhost | 5432 | Database |
| Redis | localhost | 6379 | Cache |
| Kafka | localhost | 9092 | Message broker |

---

## 🚨 Emergency Contacts

- **Administrator**: [Your Contact]
- **Backup Admin**: [Backup Contact]
- **Vendor Support**: [Support Email]

---

## 📞 Support Resources

- **Documentation**: `/root/maya-soc-enterprise/COMPLETE_DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: `/root/maya-soc-enterprise/deployment/TROUBLESHOOTING.md`
- **Logs**: `docker compose logs -f`
- **Status**: `docker compose ps`
- **Commands**: See Quick Reference below

---

## ⚡ Quick Reference Commands

### Deployment
```bash
cd /root/maya-soc-enterprise
sudo /root/maya-soc-enterprise/deployment/deploy.sh
```

### Start/Stop Services
```bash
docker compose up -d          # Start all services
docker compose down           # Stop all services
docker compose restart        # Restart all services
docker compose restart backend # Restart specific service
```

### View Logs
```bash
docker compose logs           # All logs
docker compose logs -f        # Follow new logs
docker compose logs backend   # Specific service
docker compose logs --tail 50 # Last 50 lines
```

### Status & Monitoring
```bash
docker compose ps             # Service status
docker stats                  # Resource usage
/root/maya-soc-enterprise/deployment/monitor.sh
df -h                        # Disk space
free -h                      # Memory
```

### Database
```bash
docker compose exec db psql -U maya_user -d maya_soc
# Inside psql:
SELECT count(*) FROM incidents;
\dt                          # List tables
\du                          # List users
```

### Backups
```bash
/root/maya-soc-enterprise/deployment/backup.sh
ls -lah /root/backups/
```

### Troubleshooting
```bash
docker compose logs backend | grep -i error
docker compose exec backend curl http://localhost:8000/health
curl https://app.vaultrap.com/health
```

---

## 📈 Success Metrics

### Availability
- [ ] 99.9% uptime (20 min downtime/month)
- [ ] <5 second response times
- [ ] <100ms WebSocket latency

### Performance
- [ ] <100ms page load
- [ ] <500ms API response
- [ ] <10% CPU average
- [ ] <300MB memory per service

### Security
- [ ] SSL/TLS A+ rating
- [ ] No security warnings
- [ ] All passwords changed
- [ ] Automated backups working

---

## ✅ Deployment Complete!

**Date Deployed**: ______________  
**Deployed By**: ______________  
**Verified By**: ______________  

### Notes
```


```

---

## 🎉 Next Training Topics

1. **Performance Tuning**
   - Database optimization
   - Caching strategies
   - Load testing

2. **Advanced Monitoring**
   - Prometheus integration
   - Grafana dashboards
   - Alert configuration

3. **Scaling**
   - Multi-server setup
   - Load balancing
   - Database sharding

4. **Security Hardening**
   - Network policies
   - Access controls
   - Compliance

---

**You did it! 🚀 Your MAYA SOC Enterprise is now LIVE!**
