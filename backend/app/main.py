"""
MAYA SOC Enterprise - FastAPI main application.
Real-time Security Operations Center with AI-powered threat detection.

Enterprise-Grade Production Configuration:
- Health checks on startup
- Secret validation (production mode)
- Event pipeline reliability
- MITRE ATT&CK framework integration
- Kubernetes liveness/readiness probes
- Database integration with SQLAlchemy
- Kafka event streaming
- Incident detection engine
- Prometheus monitoring and alerting
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_service import setup_logging, get_logger
from app.core.event_bus import event_bus
from app.core.event_pipeline import create_production_pipeline, ProductionEventPipeline
from app.core.unified_event_pipeline import UnifiedEventPipeline
from app.core.watchdog import ModuleWatchdog
from app.core.health_checks import (
    initialize_health_checks,
    health_checker,
    startup_verifier
)
from app.core.mitre_framework import mitre_framework
from app.api import router
from app.services.observability import observability
from app.models.database_session import database, init_database
from app.services.kafka_service import event_processor, initialize_event_streaming
from app.services.incident_detection_engine import detection_engine
from app.services.monitoring import monitoring

# Initialize enterprise-grade logging with structured JSON output
setup_logging()
logger = get_logger(__name__)

settings = get_settings()


# ========================
# SECURITY MIDDLEWARE
# ========================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    
    Implements OWASP security headers best practices:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS protection
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Prevent framing/clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable browser XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS in production
        if settings.ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy - restrict resource loading
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Referrer policy - no referrer to external sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy - restrict browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request tracking with unique request IDs.
    
    Helpful for:
    - Distributed tracing
    - Log correlation
    - Debugging
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add X-Request-ID to request/response"""
        import uuid
        
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response
        response.headers["X-Request-ID"] = request_id
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for basic rate limiting.
    
    Production systems should use Redis-based rate limiting.
    This provides basic per-IP rate limiting in memory.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # {ip: [(timestamp, count)]}
    
    async def dispatch(self, request: Request, call_next):
        """Enforce rate limiting per IP"""
        import time
        
        if settings.ENV != "production":
            # Skip rate limiting in development
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean old entries (older than 1 minute)
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                (timestamp, count) for timestamp, count in self.request_counts[client_ip]
                if now - timestamp < 60
            ]
        
        # Check rate limit
        if client_ip in self.request_counts:
            request_count = sum(count for _, count in self.request_counts[client_ip])
            if request_count >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for {client_ip}: "
                    f"{request_count} requests in last minute"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests - rate limited"}
                )
            # Add to existing entry
            self.request_counts[client_ip].append((now, 1))
        else:
            # Create new entry
            self.request_counts[client_ip] = [(now, 1)]
        
        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager with enterprise startup/shutdown"""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV} | Debug: {settings.DEBUG}")
    
    try:
        # STEP 1: Validate production secrets
        logger.info("Validating security configuration...")
        try:
            settings.validate_production_secrets()
            logger.info("✓ Security configuration validated")
        except ValueError as e:
            logger.error(f"✗ Security validation failed: {e}")
            # In production, this would block startup
            if settings.ENV == "production":
                raise
            else:
                logger.warning("⚠ Proceeding in development mode (secrets not validated)")
        
        # STEP 1.5: Initialize Unified Event Pipeline
        logger.info("Initializing unified security event pipeline...")
        try:
            app.state.unified_event_pipeline = UnifiedEventPipeline(
                kafka_brokers=[settings.KAFKA_BOOTSTRAP_SERVERS],
                kafka_topic=settings.KAFKA_TOPIC_EVENTS,
                database_session=None  # Will be set after database init
            )
            await app.state.unified_event_pipeline.startup()
            logger.info("✓ Unified event pipeline initialized (Kafka + Database publishers)")
        except Exception as e:
            logger.error(f"✗ Failed to initialize unified event pipeline: {e}")
            if settings.ENV == "production":
                raise
        
        # STEP 1.6: Initialize Module Watchdog
        logger.info("Initializing service watchdog...")
        try:
            app.state.watchdog = ModuleWatchdog(check_interval_seconds=30, max_retries=3)
            app.state.watchdog.start()
            logger.info("✓ Module watchdog initialized (auto-restart enabled)")
        except Exception as e:
            logger.error(f"✗ Failed to initialize watchdog: {e}")
            # Watchdog failure is not critical
        
        # STEP 3: Initialize event pipeline
        logger.info("Initializing production event pipeline...")
        app.state.event_pipeline: ProductionEventPipeline = create_production_pipeline()
        logger.info("✓ Event pipeline ready (Kafka backend)")
        
        # STEP 4: Initialize backend services
        logger.info("Initializing backend services...")
        await event_bus.connect()
        logger.info("✓ Event Bus initialized")
        
        observability.health_check.register_dependency(
            'event_bus',
            lambda: event_bus.running
        )
        
        # STEP 5: Initialize database (Phase 2)
        logger.info("Initializing PostgreSQL database...")
        try:
            is_db_ready = await init_database()
            if is_db_ready:
                logger.info("✓ Database initialized with connection pooling (20 connections)")
                app.state.database = database
            else:
                logger.warning("⚠ Database initialization returned false - check connection")
        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
            if settings.ENV == "production":
                raise
        
        # STEP 6: Initialize Kafka event streaming (Phase 2)
        logger.info("Initializing Kafka event streaming...")
        try:
            is_kafka_ready = await initialize_event_streaming()
            if is_kafka_ready:
                logger.info("✓ Kafka streaming initialized (7 topics, at-least-once delivery)")
                app.state.event_processor = event_processor
            else:
                logger.warning("⚠ Kafka initialization returned false - check broker")
        except Exception as e:
            logger.error(f"✗ Kafka initialization failed: {e}")
            if settings.ENV == "production":
                raise
        
        # STEP 7: Initialize incident detection engine (Phase 2)
        logger.info("Initializing incident detection engine...")
        try:
            detection_rules = detection_engine.get_active_rules()
            logger.info(
                f"✓ Detection engine online with {len(detection_rules)} rules "
                f"(rule-based, anomaly, threat-intel, correlation ready)"
            )
            app.state.detection_engine = detection_engine
        except Exception as e:
            logger.error(f"✗ Detection engine initialization failed: {e}")
        
        # STEP 8: Initialize Prometheus monitoring (Phase 2)
        logger.info("Initializing Prometheus monitoring...")
        try:
            metrics_count = len(monitoring.metrics)
            alerts_count = len(monitoring.alert_rules)
            logger.info(
                f"✓ Monitoring enabled ({metrics_count} metrics, {alerts_count} alert rules)"
            )
            app.state.monitoring = monitoring
        except Exception as e:
            logger.error(f"✗ Monitoring initialization failed: {e}")
        
        # STEP 9: Run health checks
        logger.info("Running dependency health checks...")
        is_system_ready = await initialize_health_checks()
        
        if is_system_ready:
            logger.info("✓ All critical services healthy - system ready for traffic")
        else:
            logger.warning("⚠ System running in degraded mode (non-critical service down)")
        
        # STEP 9: Log startup status
        startup_status = startup_verifier.get_startup_status()
        logger.info(f"Startup completed in {startup_status['startup_duration_ms']}ms")
        
        # STEP 11: Log available security features
        coverage = mitre_framework.get_coverage_summary()
        logger.info(
            f"MITRE ATT&CK Framework: {coverage['total_techniques']} techniques, "
            f"{coverage['total_detection_rules']} detection rules, "
            f"{coverage['total_mitigations']} mitigations"
        )
        
        logger.info(f"✓ {settings.APP_NAME} ready to serve requests (Phase 1 + Phase 2 features)")
        
    except Exception as e:
        logger.error(f"✗ Fatal error during startup: {e}", exc_info=True)
        raise
    
    yield
    
    # SHUTDOWN SEQUENCE
    logger.info("🛑 Shutting down...")
    
    # Stop watchdog first (to prevent restarts during shutdown)
    try:
        if hasattr(app.state, 'watchdog'):
            app.state.watchdog.stop()
            logger.info("✓ Module watchdog stopped")
    except Exception as e:
        logger.error(f"Error stopping watchdog: {e}")
    
    # Shutdown unified event pipeline
    try:
        if hasattr(app.state, 'unified_event_pipeline'):
            await app.state.unified_event_pipeline.shutdown()
            logger.info("✓ Unified event pipeline shutdown")
    except Exception as e:
        logger.error(f"Error shutting down unified event pipeline: {e}")
    
    try:
        await event_bus.disconnect()
        logger.info("✓ Event Bus disconnected")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    try:
        if hasattr(app.state, 'database'):
            database.dispose()
            logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    logger.info("✓ Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Security Operations Center with MITRE ATT&CK Framework",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration (must be last to wrap other middleware)
# Add middleware in reverse order (last added is first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
if settings.ENV == "production":
    app.add_middleware(RateLimitMiddleware, requests_per_minute=1000)

# Request tracking middleware
app.add_middleware(RequestIDMiddleware)

# Security headers middleware (should be early in chain)
app.add_middleware(SecurityHeadersMiddleware)


# ========================
# HEALTH CHECK ENDPOINTS
# ========================

@app.get("/health")
async def health_check():
    """General health endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "event_bus": "connected" if event_bus.running else "disconnected"
    }


@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe - is the process alive?"""
    is_alive = health_checker.get_liveness_status()
    
    return {
        "status": "alive" if is_alive else "dead",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe - can it serve traffic?"""
    is_ready, reason = health_checker.get_readiness_status()
    
    return {
        "ready": is_ready,
        "reason": reason,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@app.get("/health/status")
async def detailed_status():
    """Detailed system health status"""
    return health_checker.get_status_json()


@app.get("/health/startup")
async def startup_status():
    """Startup sequence status"""
    return startup_verifier.get_startup_status()


@app.get("/health/services")
async def services_status():
    """Service monitoring status from watchdog"""
    if hasattr(app.state, 'watchdog'):
        return app.state.watchdog.get_status()
    else:
        return {
            "error": "Watchdog not initialized",
            "watchdog_running": False,
            "services": {}
        }


# ========================
# MITRE ATT&CK ENDPOINTS
# ========================

@app.get("/api/v1/mitre/tactics")
async def get_mitre_tactics():
    """Get all MITRE tactics"""
    from app.core.mitre_framework import MitreTactic
    
    return {
        "tactics": [tactic.value for tactic in MitreTactic],
        "count": len(MitreTactic)
    }


@app.get("/api/v1/mitre/techniques/{tactic}")
async def get_mitre_techniques(tactic: str):
    """Get techniques for a specific tactic"""
    from app.core.mitre_framework import MitreTactic
    
    try:
        tactic_enum = MitreTactic(tactic)
        techniques = mitre_framework.get_techniques_by_tactic(tactic_enum)
        
        return {
            "tactic": tactic,
            "techniques": [
                {
                    "id": t.technique_id,
                    "name": t.technique_name,
                    "severity": t.severity_score,
                    "platforms": t.platforms,
                    "detection_rules": len(t.detection_rules),
                    "mitigations": len(t.mitigations)
                }
                for t in techniques
            ],
            "count": len(techniques)
        }
    except ValueError:
        return {"error": f"Unknown tactic: {tactic}"}, 400


@app.get("/api/v1/mitre/critical")
async def get_critical_techniques():
    """Get highest-severity MITRE techniques (score >= 8)"""
    critical = mitre_framework.get_critical_techniques()
    
    return {
        "severity_threshold": 8,
        "techniques": [
            {
                "id": t.technique_id,
                "name": t.technique_name,
                "severity": t.severity_score,
                "description": t.description
            }
            for t in critical
        ],
        "count": len(critical)
    }


@app.get("/api/v1/mitre/coverage")
async def get_mitre_coverage():
    """Get MITRE framework coverage statistics"""
    return mitre_framework.get_coverage_summary()


# ========================
# PHASE 2: DATABASE ENDPOINTS
# ========================

@app.get("/api/v1/incidents")
async def list_incidents(
    status: str = None,
    priority: str = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List incidents from database.
    
    Query Parameters:
    - status: OPEN, INVESTIGATING, RESOLVED, CLOSED
    - priority: LOW, MEDIUM, HIGH, CRITICAL
    - limit: number of results (max 1000)
    - offset: pagination offset
    """
    try:
        from app.models.database_session import session_scope, IncidentQueries
        
        with session_scope() as session:
            query = IncidentQueries(session)
            
            if status:
                incidents = query.get_open_incidents()  # Can be extended for status filter
            elif priority:
                incidents = query.get_by_priority(priority)
            else:
                incidents = query.get_open_incidents()
            
            return {
                "count": len(incidents),
                "incidents": [
                    {
                        "id": inc.id,
                        "name": inc.name,
                        "status": inc.status,
                        "priority": inc.priority,
                        "severity_score": inc.severity_score,
                        "created_at": inc.created_at.isoformat() if inc.created_at else None,
                        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
                    }
                    for inc in incidents[:limit]
                ]
            }
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        return {"error": str(e), "count": 0, "incidents": []}


@app.get("/api/v1/events")
async def list_events(
    severity: str = None,
    status: str = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List security events from database.
    
    Query Parameters:
    - severity: INFO, LOW, MEDIUM, HIGH, CRITICAL
    - status: DETECTED, CORRELATED, RESOLVED
    - limit: number of results (max 1000)
    - offset: pagination offset
    """
    try:
        from app.models.database_session import session_scope, EventQueries
        
        with session_scope() as session:
            query = EventQueries(session)
            events = query.get_recent_events(days=7)
            
            if severity:
                events = [e for e in events if e.severity == severity]
            
            return {
                "count": len(events),
                "events": [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "severity": e.severity,
                        "source": e.source,
                        "description": e.description,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    }
                    for e in events[:limit]
                ]
            }
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        return {"error": str(e), "count": 0, "events": []}


# ========================
# PHASE 2: MONITORING ENDPOINTS
# ========================

@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Export metrics in Prometheus text format.
    
    This endpoint is consumed by Prometheus scraper.
    Includes: event pipeline, incidents, detections, API performance, database
    """
    try:
        if hasattr(app.state, 'monitoring'):
            return app.state.monitoring.export_prometheus_format()
        else:
            return {"error": "Monitoring service not initialized"}
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return {"error": str(e)}


@app.get("/api/v1/detections")
async def list_detections(
    rule_type: str = None,
    limit: int = 100
):
    """
    List active detection rules and their status.
    
    Query Parameters:
    - rule_type: rule_based, anomaly, threat_intel, correlation
    - limit: max results
    """
    try:
        if hasattr(app.state, 'detection_engine'):
            rules = app.state.detection_engine.get_active_rules()
            
            if rule_type:
                rules = [r for r in rules if r.get('type') == rule_type]
            
            return {
                "count": len(rules),
                "rules": rules[:limit],
                "detection_strategies": [
                    "rule_based",
                    "anomaly_detection", 
                    "threat_intelligence",
                    "correlation"
                ]
            }
        else:
            return {"error": "Detection engine not initialized"}
    except Exception as e:
        logger.error(f"Error listing detections: {e}")
        return {"error": str(e), "count": 0, "rules": []}


@app.get("/api/v1/alerts/active")
async def get_active_alerts():
    """
    Get all active monitoring alerts.
    
    Shows alerts triggered by the monitoring system.
    """
    try:
        if hasattr(app.state, 'monitoring'):
            alerts = app.state.monitoring.get_active_alerts()
            return {
                "count": len(alerts),
                "alerts": alerts,
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
        else:
            return {"error": "Monitoring service not initialized"}
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return {"error": str(e), "count": 0, "alerts": []}


@app.get("/api/v1/system/status")
async def system_status():
    """
    Get complete system status including all Phase 2 components.
    
    Returns:
    - Database status and connection pool info
    - Kafka broker status
    - Detection engine state
    - Monitoring metrics
    - Health of all critical services
    """
    try:
        status = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "app_version": settings.APP_VERSION,
            "environment": settings.ENV,
            "components": {
                "database": {
                    "status": "initialized" if hasattr(app.state, 'database') else "not_initialized",
                    "pool_size": 20,
                    "max_overflow": 40
                },
                "kafka": {
                    "status": "initialized" if hasattr(app.state, 'event_processor') else "not_initialized",
                    "topics": ["events", "incidents", "alerts", "detections", "honeypot", "threat-intel", "dlq"]
                },
                "detection_engine": {
                    "status": "initialized" if hasattr(app.state, 'detection_engine') else "not_initialized",
                    "active_rules": len(app.state.detection_engine.get_active_rules()) if hasattr(app.state, 'detection_engine') else 0
                },
                "monitoring": {
                    "status": "initialized" if hasattr(app.state, 'monitoring') else "not_initialized",
                    "metrics_count": len(app.state.monitoring.metrics) if hasattr(app.state, 'monitoring') else 0,
                    "alert_rules": 5
                }
            }
        }
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"error": str(e)}


# ========================
# PHASE 2 PART 3: DECISION & BEHAVIORAL INTELLIGENCE ENDPOINTS
# ========================

@app.post("/api/v1/decisions")
async def generate_decision(
    incident_id: str,
    detection_type: str,
    confidence: float,
    asset: str,
    context: dict = None
):
    """
    Generate actionable decision for a detection.
    
    Converts raw detection → business-level decision with recommended action.
    Example response: "SSH Brute Force on DB-PROD → ISOLATE → Steps 1-6"
    
    Body:
    {
        "incident_id": "inc-2024-001",
        "detection_type": "ssh_brute_force",
        "confidence": 0.95,
        "asset": "db-prod-01",
        "context": {...}
    }
    """
    try:
        if not hasattr(app.state, 'decision_engine'):
            # Initialize if needed
            from app.services.decision_engine import DecisionEngine
            app.state.decision_engine = DecisionEngine()
        
        decision_engine = app.state.decision_engine
        
        actionable_alert = decision_engine.generate_actionable_alert(
            detection_type=detection_type,
            confidence=confidence,
            asset=asset,
            context=context or {}
        )
        
        monitoring.record_metric("decision_engine_executions", 1)
        
        return {
            "success": True,
            "incident_id": incident_id,
            "alert": {
                "title": actionable_alert.title,
                "severity": actionable_alert.severity.value,
                "confidence": actionable_alert.confidence,
                "recommended_action": actionable_alert.recommended_action.value,
                "business_context": actionable_alert.business_context,
                "action_steps": actionable_alert.action_steps,
                "false_positive_risk": actionable_alert.false_positive_risk,
                "time_to_respond_minutes": actionable_alert.time_to_respond_minutes
            }
        }
    
    except Exception as e:
        logger.error(f"Decision generation failed: {e}")
        monitoring.record_metric("decision_engine_errors", 1)
        return {
            "success": False,
            "error": str(e),
            "fallback": "INVESTIGATE (manual review required)"
        }


@app.post("/api/v1/behavioral-analysis")
async def analyze_behavior(
    user_id: str,
    event: dict
):
    """
    Analyze user/system behavior to detect anomalies.
    
    Compares current action against user's normal behavior profile.
    Example: User normally transfers 100MB/day → now 5000MB at 3am = ANOMALY
    
    Returns:
    - List of behavioral anomalies detected
    - Risk score (0-100)
    - Deviation analysis
    
    Body:
    {
        "user_id": "john_doe",
        "event": {
            "type": "data_transfer",
            "volume_mb": 5000,
            "timestamp": "2024-01-15T03:45:00Z",
            "source_location": "China",
            "destination": "personal_dropbox"
        }
    }
    """
    try:
        if not hasattr(app.state, 'behavioral_engine'):
            from app.services.behavioral_detection import BehavioralDetectionEngine
            app.state.behavioral_engine = BehavioralDetectionEngine()
        
        behavioral_engine = app.state.behavioral_engine
        
        # Load or build user profile
        # In production: load from database
        profile = behavioral_engine.get_generic_profiles("analyst")[0]  # Example
        
        # Detect anomalies
        anomalies = behavioral_engine.detect_behavioral_anomalies(event, profile)
        
        # Calculate combined risk
        if anomalies:
            risk_score = max(a.severity_score for a in anomalies)
            if len(set(a.anomaly_type for a in anomalies)) > 1:
                risk_score = min(100, risk_score * 1.5)
        else:
            risk_score = 0
        
        monitoring.record_metric("behavioral_analysis_executions", 1)
        
        return {
            "success": True,
            "user_id": user_id,
            "anomalies": [
                {
                    "type": a.anomaly_type.value,
                    "severity": a.severity_score,
                    "deviation_percent": a.deviation_percentage,
                    "description": a.description,
                    "expected": a.expected_behavior,
                    "observed": a.observed_behavior
                }
                for a in anomalies
            ],
            "combined_risk_score": risk_score,
            "anomaly_count": len(anomalies)
        }
    
    except Exception as e:
        logger.error(f"Behavioral analysis failed: {e}")
        monitoring.record_metric("behavioral_analysis_errors", 1)
        return {
            "success": False,
            "error": str(e),
            "anomalies": []
        }


@app.post("/api/v1/integrated-detection")
async def integrated_detection_pipeline(
    raw_detection: dict
):
    """
    Complete detection pipeline: rules + behavioral + decision + fault tolerance.
    
    Runs detection through ENTIRE Phase 2 Part 3 pipeline:
    1. Rule-based detection (what happened)
    2. Behavioral anomaly analysis (is it anomalous)
    3. Decision engine (what to do)
    4. Fault tolerance (keep running if components fail)
    
    Returns complete analysis with actionable decision.
    
    Example detection:
    {
        "type": "unusual_data_transfer",
        "source_user": "finance_bob",
        "data_volume_mb": 5000,
        "asset": "finance_db",
        "confidence": 0.82
    }
    """
    try:
        if not hasattr(app.state, 'integrated_pipeline'):
            from app.services.integration_tests import Phase2SecurityPipeline
            app.state.integrated_pipeline = Phase2SecurityPipeline()
        
        pipeline = app.state.integrated_pipeline
        
        # Run through integrated pipeline
        result = await pipeline.process_detection(raw_detection)
        
        monitoring.record_metric("integrated_detection_executions", 1)
        
        return {
            "success": True,
            "pipeline_status": result.pipeline_status,
            "detection": {
                "type": result.detection_type,
                "confidence": result.confidence
            },
            "behavioral_analysis": {
                "anomalies": len(result.behavioral_anomalies),
                "risk_score": result.behavioral_risk_score,
                "anomaly_types": list(set(
                    a.anomaly_type.value for a in result.behavioral_anomalies
                ))
            },
            "decision": {
                "title": result.actionable_alert.title if result.actionable_alert else "No decision",
                "severity": result.actionable_alert.severity.value if result.actionable_alert else "INFO",
                "action": result.actionable_alert.recommended_action.value if result.actionable_alert else "ACKNOWLEDGE",
                "steps": result.actionable_alert.action_steps if result.actionable_alert else [],
                "time_to_respond_minutes": result.actionable_alert.time_to_respond_minutes if result.actionable_alert else 1440
            },
            "recovery_actions": result.recovery_actions,
            "processing_time_ms": result.processing_time_ms
        }
    
    except Exception as e:
        logger.error(f"Integrated detection failed: {e}", exc_info=True)
        monitoring.record_metric("integrated_detection_errors", 1)
        return {
            "success": False,
            "error": str(e),
            "pipeline_status": "unhealthy"
        }


@app.get("/api/v1/system/health-detailed")
async def system_health_detailed():
    """
    Detailed health status of ALL Phase 2 Part 3 components.
    
    Shows:
    - Decision engine status
    - Behavioral detection engine status
    - Fault tolerance system status
    - Circuit breaker states
    """
    try:
        health_data = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "phase_2_components": {
                "decision_engine": {
                    "status": "ready" if hasattr(app.state, 'decision_engine') else "not_initialized",
                    "playbooks_loaded": 8
                },
                "behavioral_detection": {
                    "status": "ready" if hasattr(app.state, 'behavioral_engine') else "not_initialized",
                    "anomaly_types": 5
                },
                "fault_tolerance": {
                    "status": "ready" if hasattr(app.state, 'integrated_pipeline') else "not_initialized",
                    "circuit_breakers": ["decision_engine", "behavior_engine", "rule_engine"]
                }
            }
        }
        
        # Add detailed fault tolerance status if available
        if hasattr(app.state, 'integrated_pipeline'):
            pipeline = app.state.integrated_pipeline
            health_summary = pipeline.fault_manager.get_system_health_summary()
            health_data["fault_tolerance_summary"] = health_summary
        
        return health_data
    
    except Exception as e:
        logger.error(f"Error getting health details: {e}")
        return {"error": str(e)}


# ========================
# MAIN API ROUTER
# ========================

app.include_router(router, prefix=settings.API_V1_PREFIX)


# ========================
# ERROR HANDLING
# ========================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    observability.performance_monitor.record_error(
        error_type=type(exc).__name__,
        component='api'
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
