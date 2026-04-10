# 🔧 MAYA SOC ENTERPRISE - Troubleshooting Guide

## 🚨 Quick Diagnosis

### Check Everything Works
```bash
cd /root/maya-mvp

# See all service status
docker compose ps

# View all logs
docker compose logs

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:5173
```

---

## Common Issues & Solutions

### ❌ Services Not Starting

**Problem**: Containers exit immediately or fail to start

**Diagnosis**:
```bash
docker compose logs
docker compose ps
```

**Solutions**:

1. **Check logs for specific errors**
   ```bash
   docker compose logs backend
   docker compose logs frontend
   docker compose logs db
   ```

2. **Restart all services**
   ```bash
   docker compose restart
   ```

3. **Full restart with cleanup**
   ```bash
   docker compose down
   docker system prune -a
   docker compose up -d
   ```

4. **Check ports are available**
   ```bash
   lsof -i :80
   lsof -i :443
   lsof -i :8000
   lsof -i :5173
   ```

---

### ❌ Database Connection Failed

**Problem**: `psycopg2.OperationalError` or database won't connect

**Diagnosis**:
```bash
docker compose ps db
docker compose logs db
```

**Solutions**:

1. **Check database is running**
   ```bash
   docker compose exec db psql -U soc_user -d maya_soc -c "SELECT 1;"
   ```

2. **Verify credentials in .env**
   ```bash
   # Check these variables in .env:
   POSTGRES_USER=soc_user
   POSTGRES_PASSWORD=[should not be blank]
   POSTGRES_DB=maya_soc
   ```

3. **Reinitialize database**
   ```bash
   docker compose down
   docker volume rm maya-mvp_postgres_data
   docker compose up -d db
   ```

4. **Reset database from backup**
   ```bash
   # Restore from latest backup
   LATEST_BACKUP=$(ls -t /root/backups/*.sql.gz | head -1)
   docker compose exec -T db psql -U soc_user < <(gunzip -c $LATEST_BACKUP)
   ```

---

### ❌ Backend API Not Responding

**Problem**: `curl: (7) Failed to connect` or 502 Bad Gateway

**Diagnosis**:
```bash
docker compose logs backend
docker compose ps backend
curl http://localhost:8000/health
```

**Solutions**:

1. **Check backend is running**
   ```bash
   docker compose exec backend curl http://localhost:8000/health
   ```

2. **Check backend logs for errors**
   ```bash
   docker compose logs -f backend | grep -i error
   ```

3. **Verify environment variables**
   ```bash
   docker compose exec backend env | grep -i database
   docker compose exec backend env | grep -i redis
   ```

4. **Restart backend**
   ```bash
   docker compose restart backend
   ```

5. **Check dependencies**
   ```bash
   # All these should be "Up"
   docker compose ps | grep -E "db|redis|kafka|backend"
   ```

---

### ❌ Frontend Not Loading

**Problem**: Blank page or cannot reach maya.vaultrap.com

**Diagnosis**:
```bash
docker compose logs frontend
curl http://localhost:5173
curl https://maya.vaultrap.com
```

**Solutions**:

1. **Check frontend is running**
   ```bash
   docker compose ps frontend
   docker compose logs frontend
   ```

2. **Check Nginx configuration**
   ```bash
   docker compose ps nginx
   docker compose logs nginx
   ```

3. **Verify DNS/Domain**
   ```bash
   nslookup maya.vaultrap.com
   ping maya.vaultrap.com
   curl -v https://maya.vaultrap.com
   ```

4. **Check SSL certificate**
   ```bash
   certbot certificates
   ls -la /etc/letsencrypt/live/maya.vaultrap.com/
   ```

5. **Restart Nginx**
   ```bash
   docker compose restart nginx
   ```

---

### ❌ High Memory/CPU Usage

**Problem**: Services running slowly or consuming excessive resources

**Diagnosis**:
```bash
docker stats
top
docker compose logs backend | grep -i "memory\|cpu"
```

**Solutions**:

1. **Check what's using resources**
   ```bash
   docker stats --no-stream
   ```

2. **Clean up Docker**
   ```bash
   docker system prune -a
   docker volume prune
   ```

3. **Restart resource-heavy services**
   ```bash
   docker compose restart backend
   docker compose restart db
   ```

4. **Check for memory leaks in logs**
   ```bash
   docker compose logs backend | grep -i "memory"
   ```

5. **Query optimization**
   ```bash
   # Check slow queries
   docker compose exec db psql -U soc_user -d maya_soc << EOF
   SELECT * FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;
   EOF
   ```

---

### ❌ Out of Disk Space

**Problem**: `No space left on device` or docker container exits

**Diagnosis**:
```bash
df -h
du -sh /root/*
docker system df
```

**Solutions**:

1. **Check what's using space**
   ```bash
   du -sh /root/backups
   du -sh /var/lib/docker
   ```

2. **Clean docker**
   ```bash
   docker system prune -a --volumes
   ```

3. **Remove old backups**
   ```bash
   find /root/backups -mtime +30 -delete
   ```

4. **Compress old backups**
   ```bash
   find /root/backups -mtime +7 -exec gzip {} \;
   ```

5. **Move backups to external storage**
   ```bash
   # Upload to cloud storage or another server
   ```

---

### ❌ Kafka/Redis Connection Issues

**Problem**: `ConnectionError` or service timeout

**Diagnosis**:
```bash
docker compose logs kafka
docker compose logs redis
docker compose ps kafka redis
```

**Solutions**:

1. **Check Kafka**
   ```bash
   docker compose exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
   ```

2. **Check Redis**
   ```bash
   docker compose exec redis redis-cli ping
   ```

3. **Restart message services**
   ```bash
   docker compose restart kafka redis zookeeper
   ```

4. **Clear message queue**
   ```bash
   docker compose exec kafka kafka-topics.sh --delete --bootstrap-server localhost:9092 --topic security_events
   docker compose exec kafka kafka-topics.sh --create --bootstrap-server localhost:9092 --topic security_events --partitions 1 --replication-factor 1
   ```

---

### ❌ SSL Certificate Issues

**Problem**: `ERR_SSL_CERT_AUTHORITY_INVALID` or 403 errors

**Diagnosis**:
```bash
certbot certificates
ls -la /etc/letsencrypt/live/maya.vaultrap.com/
ssl_client -connect maya.vaultrap.com:443
```

**Solutions**:

1. **Check certificate is valid**
   ```bash
   certbot certificates
   openssl x509 -in /etc/letsencrypt/live/maya.vaultrap.com/fullchain.pem -text -noout
   ```

2. **Manually renew certificate**
   ```bash
   certbot renew --force-renewal
   ```

3. **Test renewal**
   ```bash
   certbot renew --dry-run
   ```

4. **Restart Nginx after certificate update**
   ```bash
   docker compose restart nginx
   ```

5. **Check Nginx config syntax**
   ```bash
   nginx -t
   ```

---

### ❌ Login Not Working

**Problem**: "Invalid credentials" or stuck on login screen

**Diagnosis**:
```bash
docker compose logs backend | grep -i "auth\|login"
curl -X POST http://localhost:8000/api/v1/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}'
```

**Solutions**:

1. **Check default credentials**
   - Username: `admin`
   - Password: Check your `.env` file (INIT_ADMIN_PASSWORD)

2. **Reset admin password**
   ```bash
   docker compose exec backend python -c "
   from app.core.security import hash_password
   import os
   os.system('sqlite3 app.db \"UPDATE users SET password=\\\"' + hash_password('your_new_password') + '\\\" WHERE username=\\\"admin\\\"\"')
   "
   ```

3. **Check authentication service logs**
   ```bash
   docker compose logs backend | grep -i "jwt\|token"
   ```

---

### ❌ WebSocket Connections Failing

**Problem**: Real-time data not updating, WebSocket errors in console

**Diagnosis**:
```bash
curl -v -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws
```

**Solutions**:

1. **Check WebSocket endpoint is working**
   ```bash
   docker compose exec backend curl http://localhost:8000/ws
   ```

2. **Check Nginx WebSocket configuration**
   ```bash
   grep -A 5 "location /ws" deployment/nginx.conf
   ```

3. **Verify connection headers**
   - Frontend should send: `Upgrade: websocket`
   - Backend should accept connections on `/ws`

4. **Restart backend**
   ```bash
   docker compose restart backend
   ```

---

## 🔍 Advanced Debugging

### Enable Debug Logging
```bash
# Edit .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart services
docker compose restart backend
```

### Database Performance Analysis
```bash
# Connect to database
docker compose exec db psql -U soc_user -d maya_soc

# List slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Analyze query plan
EXPLAIN ANALYZE SELECT * FROM events WHERE timestamp > NOW() - INTERVAL '24 hours';
```

### Monitor Real-Time Activity
```bash
# Watch Docker stats
watch -n 1 docker stats

# Check file handles
lsof -p $(docker inspect -f '{{.State.Pid}}' maya-backend)

# Monitor network connections
netstat -tulpn | grep LISTEN
```

### Collect Debug Information
```bash
# Create debug bundle
mkdir -p /root/debug
docker compose ps > /root/debug/services.txt
docker compose logs > /root/debug/logs.txt
docker stats --no-stream > /root/debug/resources.txt
df -h > /root/debug/disk.txt
docker system df > /root/debug/docker-df.txt

echo "Debug bundle created in /root/debug/"
```

---

## 📝 Getting Help

### Information to Provide

1. **Error message** (full, from logs)
2. **When it started** (after deploy? update?)
3. **Steps to reproduce**
4. **Service status** (`docker compose ps`)
5. **Recent logs** (`docker compose logs --tail 50`)
6. **System info** (`df -h`, `free -h`)

### Useful Commands for Support

```bash
# Create support package
tar -czf /root/maya-support-$(date +%Y%m%d_%H%M%S).tar.gz \
  /root/maya-mvp/docker-compose.yml \
  /root/maya-mvp/.env.example \
  /var/lib/docker/containers/*/config.v2.json
```

---

## 🆘 Emergency Recovery

### Complete Service Reset
```bash
# WARNING: This will delete all data!
docker compose down
docker volume rm maya-mvp_postgres_data
docker volume rm maya-mvp_redis_data
docker system prune -a
docker compose up -d
```

### Restore from Backup
```bash
# List available backups
ls -lah /root/backups/

# Restore latest
LATEST=$(ls -t /root/backups/*.sql.gz | head -1)
gunzip -c $LATEST | docker compose exec -T db psql -U soc_user -d maya_soc
```

### Restart from Clean State
```bash
cd /root/maya-mvp
git reset --hard origin/main
git pull
docker compose build --no-cache
docker compose up -d
```

---

## ✅ Verification Checklist

After making changes, verify everything works:

- [ ] All containers running: `docker compose ps` (all "UP")
- [ ] Backend responding: `curl http://localhost:8000/health`
- [ ] Frontend loading: `curl http://localhost:5173`
- [ ] Database connecting: `docker compose exec db psql -U soc_user -d maya_soc -c "SELECT 1;"`
- [ ] Logs clean: `docker compose logs | grep -i error` (no errors)
- [ ] No high resource usage: `docker stats --no-stream`
- [ ] Disk space available: `df -h` (>10% free)
- [ ] Application accessible: `curl https://maya.vaultrap.com`

---

For additional support, check COMPLETE_DEPLOYMENT_GUIDE.md or contact your administrator.
