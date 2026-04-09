# 🚀 PHASE 2 QUICK REFERENCE GUIDE

## New API Endpoints (All Ready to Use)

### 1. List Incidents
```bash
GET /api/v1/incidents?status=OPEN&priority=HIGH&limit=100
```
**Response**:
```json
{
  "count": 23,
  "incidents": [
    {
      "id": "uuid",
      "name": "SSH Brute Force Attack",
      "status": "OPEN",
      "priority": "HIGH",
      "severity_score": 85,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

### 2. List Security Events
```bash
GET /api/v1/events?severity=HIGH&limit=100
```
**Response**:
```json
{
  "count": 156,
  "events": [
    {
      "id": "uuid",
      "event_type": "failed_login",
      "severity": "HIGH",
      "source": "10.0.1.45",
      "description": "5 failed SSH attempts in 60 seconds",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 3. Export Prometheus Metrics
```bash
GET /api/v1/metrics
```
**Response** (Prometheus format):
```
# HELP events_received_total Total security events received
# TYPE events_received_total counter
events_received_total 1250

# HELP events_processed_total Total events processed
# TYPE events_processed_total counter
events_processed_total 1240

# HELP events_failed_total Failed event processing
# TYPE events_failed_total counter
events_failed_total 10

# HELP incidents_created_total Total incidents created
# TYPE incidents_created_total counter
incidents_created_total 45

# ... 20 metrics total
```

---

### 4. List Active Detection Rules
```bash
GET /api/v1/detections?rule_type=rule_based&limit=10
```
**Response**:
```json
{
  "count": 5,
  "rules": [
    {
      "name": "ssh_brute_force",
      "type": "rule_based",
      "description": "Detects SSH brute force attacks",
      "threshold": "5 failures in 60 seconds",
      "severity": "HIGH",
      "mitre_tactics": ["credential_access"],
      "confidence": 0.95
    },
    {
      "name": "sql_injection",
      "type": "rule_based",
      "description": "Detects SQL injection attempts",
      "threshold": "Pattern: ' OR '1'='1",
      "severity": "CRITICAL",
      "mitre_tactics": ["initial_access"],
      "confidence": 0.98
    }
  ],
  "detection_strategies": [
    "rule_based",
    "anomaly_detection",
    "threat_intelligence",
    "correlation"
  ]
}
```

---

### 5. Get Active Alerts
```bash
GET /api/v1/alerts/active
```
**Response**:
```json
{
  "count": 2,
  "alerts": [
    {
      "name": "high_event_latency",
      "severity": "WARNING",
      "message": "Event processing latency exceeded 1000ms",
      "triggered_at": "2024-01-15T10:32:00Z",
      "value": 1250,
      "threshold": 1000
    },
    {
      "name": "critical_incidents",
      "severity": "CRITICAL",
      "message": "More than 5 high priority incidents detected",
      "triggered_at": "2024-01-15T10:31:00Z",
      "value": 8,
      "threshold": 5
    }
  ],
  "alert_rules": [
    {
      "name": "high_event_latency",
      "threshold": "1000ms",
      "severity": "WARNING"
    },
    {
      "name": "incident_backlog",
      "threshold": ">50 open",
      "severity": "WARNING"
    },
    {
      "name": "critical_incidents",
      "threshold": ">5 high priority",
      "severity": "CRITICAL"
    },
    {
      "name": "api_error_rate",
      "threshold": ">5%",
      "severity": "WARNING"
    },
    {
      "name": "db_connection_exhaustion",
      "threshold": ">18/20",
      "severity": "CRITICAL"
    }
  ]
}
```

---

### 6. Get System Status
```bash
GET /api/v1/system/status
```
**Response**:
```json
{
  "timestamp": "2024-01-15T10:35:00Z",
  "app_version": "2.0.0",
  "environment": "production",
  "components": {
    "database": {
      "status": "initialized",
      "pool_size": 20,
      "max_overflow": 40
    },
    "kafka": {
      "status": "initialized",
      "topics": [
        "events",
        "incidents",
        "alerts",
        "detections",
        "honeypot",
        "threat-intel",
        "dlq"
      ]
    },
    "detection_engine": {
      "status": "initialized",
      "active_rules": 5
    },
    "monitoring": {
      "status": "initialized",
      "metrics_count": 20,
      "alert_rules": 5
    }
  }
}
```

---

## Environment Configuration

Create `.env` file in backend directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/maya_soc
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=maya_soc

# Kafka Configuration
KAFKA_BROKERS=localhost:9092
KAFKA_TOPIC_EVENTS=events
KAFKA_TOPIC_INCIDENTS=incidents
KAFKA_CONSUMER_GROUP=maya-soc-consumer

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENV=production
DEBUG=False
```

---

## Features by Component

### 🗄️ Database (12 Tables)

| Table | Rows Tracked | Purpose |
|-------|--------------|---------|
| events | All security events | Raw event storage |
| incidents | Correlated events | Incident tracking |
| detections | Detection results | Detection records |
| alerts | Actionable alerts | Analyst alerts |
| incident_actions | Response actions | Incident response |
| honeypot_interactions | Deception hits | Honeypot tracking |
| threat_intelligence | Threat feeds | Threat feeds |
| users | System users | RBAC |
| audit_logs | All changes | Compliance |
| metric_snapshots | Time-series data | Metrics |
| detections_metrics | Metric relations | Analytics |
| event_incidents | M2M relations | Correlations |

### 📨 Kafka (7 Topics)

| Topic | Format | Purpose |
|-------|--------|---------|
| events | JSON Event | Raw security events |
| incidents | JSON Incident | Created incidents |
| alerts | JSON Alert | Analyst alerts |
| detections | JSON Detection | Detection results |
| honeypot | JSON Interaction | Deception tracking |
| threat-intel | JSON TI | Threat feeds |
| dead-letter-queue | JSON | Failed messages |

### 🎯 Detection Engine (5 Rules)

| Rule | Trigger | Risk Score | Priority |
|------|---------|-----------|----------|
| SSH Brute Force | 5 failures / 60s | 80 | HIGH |
| Web Exploit | SQL/XSS patterns | 85 | CRITICAL |
| Suspicious PowerShell | iex/invoke-expression | 75 | HIGH |
| Unusual Data Transfer | >100MB transfer | 70 | MEDIUM |
| File Integrity | Protected files modified | 90 | CRITICAL |

### 📊 Monitoring (20 Metrics)

```
Event Pipeline (5):
  • events_received_total
  • events_processed_total
  • events_failed_total
  • event_queue_size
  • event_processing_latency_ms

Incidents (4):
  • incidents_created_total
  • incidents_open
  • incidents_high_priority
  • incident_resolution_time_seconds

Detection (3):
  • detections_triggered_total
  • active_detection_rules
  • detection_confidence_scores

API (4):
  • api_requests_total
  • api_errors_total
  • api_request_latency_ms
  • api_requests_in_flight

Database (2):
  • db_connections_open
  • db_query_latency_ms

System (2):
  • system_cpu_percent
  • system_memory_percent
```

---

## Startup Verification

### Check Application Health
```bash
curl http://localhost:8000/health
```

### View System Status
```bash
curl http://localhost:8000/api/v1/system/status
```

### Export Prometheus Metrics
```bash
curl http://localhost:8000/api/v1/metrics > metrics.txt
```

### List Incidents
```bash
curl http://localhost:8000/api/v1/incidents
```

### Get Active Alerts
```bash
curl http://localhost:8000/api/v1/alerts/active
```

---

## Common Use Cases

### Monitor High-Priority Incidents
```bash
curl "http://localhost:8000/api/v1/incidents?priority=HIGH&status=OPEN"
```

### Find Critical Events
```bash
curl "http://localhost:8000/api/v1/events?severity=CRITICAL&limit=50"
```

### Check System Health
```bash
curl http://localhost:8000/health
```

### Monitor for Active Alerts
```bash
curl http://localhost:8000/api/v1/alerts/active | jq '.alerts[].severity'
```

### Check Detection Rules
```bash
curl http://localhost:8000/api/v1/detections | jq '.rules[] | {name, severity}'
```

### Export to Prometheus Server
```bash
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'maya-soc'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics'
```

---

## Performance Tips

### For High Volume Events
- Increase Kafka partition count
- Increase database connection pool
- Enable caching for frequent queries

### For Real-time Monitoring
- Use Prometheus scrape interval of 15s
- Subscribe to Kafka alert topic
- Configure alert webhooks for critical events

### For Database Optimization
- Create indexes on frequently queried columns (already done)
- Archive old events monthly
- Use EXPLAIN ANALYZE for slow queries

---

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
psql -U postgres -h localhost

# Verify connection string in .env
# Format: postgresql://user:password@host:port/database
```

### Kafka Connection Issues
```bash
# Check Kafka broker is running
kafka-console-producer --broker-list localhost:9092 --topic test

# Verify Kafka brokers in .env
# Format: localhost:9092 or kafka-1:9092,kafka-2:9092
```

### Detection Rules Not Triggering
```bash
# Check active rules
curl http://localhost:8000/api/v1/detections

# Verify event format matches rule patterns
# Check logs for detection engine errors
```

### Metrics Not Appearing
```bash
# Verify monitoring service initialized
curl http://localhost:8000/api/v1/system/status

# Check /api/v1/metrics endpoint
curl http://localhost:8000/api/v1/metrics | head -20
```

---

## Next Steps

### Phase 2 Part 2 (Coming Next)
- [ ] Security headers middleware
- [ ] Rate limiting
- [ ] API authentication
- [ ] Docker configuration
- [ ] CI/CD pipeline

### Phase 3 (Future)
- [ ] Advanced detection rules
- [ ] Behavioral analysis
- [ ] ML-based anomaly detection
- [ ] Honeypot integration
- [ ] Advanced threat intelligence

---

**Quick Stats**:
- 📊 20 Prometheus metrics ready to collect
- 🎯 5 detection rules configured and active
- 🚨 5 alert rules for automated alerting
- 💾 12 database tables with relationships
- 📨 7 Kafka topics for event streaming
- 🔌 6 new API endpoints integrated

**Status**: ✅ Phase 2 Part 1 Complete - Ready for Phase 2 Part 2
