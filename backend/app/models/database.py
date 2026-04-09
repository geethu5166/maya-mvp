"""
DATABASE SCHEMA - MAYA SOC ENTERPRISE
======================================

PostgreSQL schema design for production SIEM:
- Events, Incidents, Alerts, Detections
- Users, Roles, Permissions (RBAC)
- Deception tracking, Threat intelligence
- Audit logging, Performance metrics

Author: MAYA SOC Enterprise
Version: 1.0 - Production Schema
"""

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Enum, UniqueConstraint, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime
from enum import Enum as PyEnum
import uuid

Base = declarative_base()


# ==========================================
# ENUMS - Security Classification
# ==========================================

class EventSeverity(PyEnum):
    """Event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EventStatus(PyEnum):
    """Event processing status"""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSED = "PROCESSED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class IncidentStatus(PyEnum):
    """Incident lifecycle status"""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    REMEDIATED = "REMEDIATED"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class IncidentPriority(PyEnum):
    """Incident priority for response"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DetectionType(PyEnum):
    """Detection mechanism used"""
    RULE_BASED = "RULE_BASED"
    ANOMALY_ML = "ANOMALY_ML"
    BEHAVIORAL = "BEHAVIORAL"
    THREAT_INTEL = "THREAT_INTEL"
    DECEPTION = "DECEPTION"
    MITRE_ATT_CK = "MITRE_ATT_CK"


class UserRole(PyEnum):
    """User role levels"""
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    RESPONDER = "RESPONDER"
    VIEWER = "VIEWER"


# ==========================================
# CORE TABLES - Events & Incidents
# ==========================================

class Event(Base):
    """
    Raw security event from any source
    
    - Network traffic inspection
    - Log ingestion (Windows, Linux, applications)
    - Honeypot captures
    - API alerts
    - Threat intelligence feeds
    """
    
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_event_timestamp", "timestamp"),
        Index("idx_event_severity", "severity"),
        Index("idx_event_source", "source"),
        Index("idx_event_status", "status"),
    )
    
    # Primary key
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event classification
    event_type = Column(String(50), nullable=False)  # SECURITY_ALERT, ANOMALY, DECEPTION, etc.
    severity = Column(Enum(EventSeverity), nullable=False, default=EventSeverity.MEDIUM)
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.RECEIVED)
    
    # Timeline
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    received_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_timestamp = Column(DateTime, nullable=True)
    
    # Source identification
    source = Column(String(100), nullable=False)  # "ssh_honeypot", "web_firewall", "endpoint", etc.
    source_ip = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    source_hostname = Column(String(255), nullable=True)
    
    # Event content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True)  # Original event payload
    
    # Enrichment
    enrichment_data = Column(JSON, nullable=True)  # Geolocation, reputation, etc.
    is_enriched = Column(Boolean, default=False)
    
    # Multi-tenancy & organization
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Relationships
    incidents = relationship("Incident", secondary="event_incidents", back_populates="events")
    detections = relationship("Detection", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event {self.event_id} - {self.event_type} ({self.severity.value})>"


class Incident(Base):
    """
    Correlated security incident
    
    - Created from multiple events
    - Manual creation by analysts
    - Automated detection
    - Tracks investigation and response
    """
    
    __tablename__ = "incidents"
    __table_args__ = (
        Index("idx_incident_status", "status"),
        Index("idx_incident_priority", "priority"),
        Index("idx_incident_created", "created_at"),
        Index("idx_incident_tenant", "tenant_id"),
    )
    
    # Primary key
    incident_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Classification
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)
    priority = Column(Enum(IncidentPriority), nullable=False, default=IncidentPriority.MEDIUM)
    
    # MITRE ATT&CK mapping
    mitre_tactics = Column(JSON, nullable=True)  # ["initial_access", "execution"]
    mitre_techniques = Column(JSON, nullable=True)  # ["T1566", "T1059"]
    
    # Timeline
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Assignment & responsibility
    assigned_analyst_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    analyst_notes = Column(Text, nullable=True)
    
    # Impact assessment
    affected_assets = Column(JSON, nullable=True)  # List of IP/hostnames
    asset_count = Column(Integer, default=0)
    affected_users = Column(JSON, nullable=True)  # List of usernames
    user_count = Column(Integer, default=0)
    estimated_impact = Column(String(50), nullable=True)  # "high", "medium", "low"
    
    # Response tracking
    containment_actions = Column(JSON, nullable=True)
    remediation_status = Column(String(100), nullable=True)
    
    # Multi-tenancy
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Relationships
    events = relationship("Event", secondary="event_incidents", back_populates="incidents")
    assigned_analyst = relationship("User", back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("IncidentAction", back_populates="incident", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Incident {self.incident_id} - {self.status.value}>"


class Detection(Base):
    """
    Record of how an event was detected/classified
    
    Links events to:
    - Detection rules (SIGMA, Yara, custom)
    - ML models
    - Behavioral profiles
    - Threat intelligence
    - Deception systems
    """
    
    __tablename__ = "detections"
    __table_args__ = (
        Index("idx_detection_type", "detection_type"),
        Index("idx_detection_event", "event_id"),
    )
    
    detection_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("events.event_id"), nullable=False)
    
    # Detection mechanism
    detection_type = Column(Enum(DetectionType), nullable=False)
    rule_id = Column(String(100), nullable=True)  # SIGMA rule ID, Yara rule ID, etc.
    rule_name = Column(String(255), nullable=True)
    
    # Confidence metrics
    confidence_score = Column(Float, default=0.0)  # 0.0 - 1.0
    risk_score = Column(Float, default=0.0)  # 0.0 - 100.0
    
    # Detection metadata
    detection_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    detector_name = Column(String(100), nullable=False)  # "sigma_engine", "ml_model_v2", etc.
    
    # Relationships
    event = relationship("Event", back_populates="detections")
    
    def __repr__(self):
        return f"<Detection {self.detection_id} - {self.detection_type.value}>"


class Alert(Base):
    """
    Actionable alert for SOC analysts
    
    - Derived from incidents
    - Escalation mechanism
    - Tracks analyst notifications
    """
    
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alert_incident", "incident_id"),
        Index("idx_alert_created", "created_at"),
    )
    
    alert_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), nullable=False)
    
    # Alert content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(EventSeverity), nullable=False)
    
    # Alert status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Timeline
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Notification channels
    sent_via_email = Column(Boolean, default=False)
    sent_via_slack = Column(Boolean, default=False)
    sent_via_webhook = Column(Boolean, default=False)
    
    # Relationships
    incident = relationship("Incident", back_populates="alerts")
    acknowledged_by = relationship("User")
    
    def __repr__(self):
        return f"<Alert {self.alert_id}>"


# ==========================================
# INCIDENT RESPONSE TRACKING
# ==========================================

class IncidentAction(Base):
    """
    Track all actions taken during incident response
    
    - Containment measures
    - Remediation steps
    - Escalations
    - Investigation progress
    """
    
    __tablename__ = "incident_actions"
    __table_args__ = (
        Index("idx_incident_action_incident", "incident_id"),
        Index("idx_incident_action_timestamp", "timestamp"),
    )
    
    action_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), nullable=False)
    
    # Action details
    action_type = Column(String(100), nullable=False)  # "contained", "remediated", "escalated", etc.
    description = Column(Text, nullable=False)
    
    # Who & when
    performed_by_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Evidence
    evidence = Column(JSON, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="actions")
    performed_by = relationship("User")
    
    def __repr__(self):
        return f"<IncidentAction {self.action_id} - {self.action_type}>"


# ==========================================
# DECEPTION & THREAT TRACKING
# ==========================================

class HoneypotInteraction(Base):
    """
    Track interactions with deception resources
    
    - SSH honeypot logins
    - Web honeypot access
    - Database honeypot queries
    - Fake file shares
    """
    
    __tablename__ = "honeypot_interactions"
    __table_args__ = (
        Index("idx_honeypot_type", "honeypot_type"),
        Index("idx_honeypot_timestamp", "timestamp"),
    )
    
    interaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Honeypot identification
    honeypot_type = Column(String(50), nullable=False)  # "ssh", "web", "database", "smb", etc.
    honeypot_id = Column(String(100), nullable=False)
    
    # Attacker information
    source_ip = Column(String(45), nullable=False, index=True)
    source_port = Column(Integer, nullable=True)
    
    # Interaction details
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    protocol = Column(String(50), nullable=False)  # "SSH", "HTTP", "HTTPS", "SMB", etc.
    credentials_attempted = Column(JSON, nullable=True)  # {"username": "...", "password": "..."}
    commands_executed = Column(JSON, nullable=True)  # List of commands
    files_accessed = Column(JSON, nullable=True)
    
    # Severity
    severity = Column(Enum(EventSeverity), nullable=False, default=EventSeverity.HIGH)
    
    # Analysis
    attacker_profile = Column(String(100), nullable=True)  # "APT29", "unknown", etc.
    is_legitimate = Column(Boolean, default=False)
    
    # Multi-tenancy
    tenant_id = Column(String(100), nullable=False, index=True)
    
    def __repr__(self):
        return f"<HoneypotInteraction {self.interaction_id}>"


class ThreatIntelligence(Base):
    """
    Threat intelligence feeds and enrichment
    
    - External threat feeds (abuse.ch, OTX, etc.)
    - IP reputation
    - Domain reputation
    - File hashes
    - C&C tracking
    """
    
    __tablename__ = "threat_intelligence"
    __table_args__ = (
        Index("idx_ti_indicator", "indicator"),
        Index("idx_ti_type", "indicator_type"),
        Index("idx_ti_updated", "last_updated"),
    )
    
    ti_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Indicator details
    indicator_type = Column(String(50), nullable=False)  # "ip", "domain", "hash", "url", "email"
    indicator = Column(String(500), nullable=False, index=True)
    
    # Reputation
    malicious_score = Column(Float, default=0.0)  # 0.0-1.0 (0=clean, 1=definitely malicious)
    sources = Column(JSON, default=[])  # ["AbuseIPDB", "VirusTotal", ...]
    
    # Context
    threat_name = Column(String(255), nullable=True)  # "Emotet", "TrickBot", etc.
    threat_type = Column(String(100), nullable=True)  # "botnet", "malware", "spyware", etc.
    last_seen = Column(DateTime, nullable=True)
    
    # Feed management
    source_feed = Column(String(100), nullable=True)  # Source of intelligence
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    events = relationship(
        "Event",
        primaryjoin="and_(foreign(Event.source_ip)==remote(ThreatIntelligence.indicator))",
        viewonly=True
    )
    
    def __repr__(self):
        return f"<ThreatIntel {self.indicator_type} - {self.indicator}>"


# ==========================================
# USER & AUTHORIZATION
# ==========================================

class User(Base):
    """
    SOC analyst and operator accounts
    
    - Role-based access control
    - Activity tracking
    - Team assignment
    """
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", "tenant_id", name="uq_user_tenant"),
        Index("idx_user_active", "is_active"),
    )
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identity
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    mfa_enabled = Column(Boolean, default=True)
    mfa_secret = Column(String(100), nullable=True)
    
    # Authorization
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Organization
    tenant_id = Column(String(100), nullable=False, index=True)
    team = Column(String(100), nullable=True)
    
    # Relationships
    incidents = relationship("Incident", back_populates="assigned_analyst", foreign_keys=[Incident.assigned_analyst_id])
    
    def __repr__(self):
        return f"<User {self.username}>"


# ==========================================
# AUDIT & COMPLIANCE
# ==========================================

class AuditLog(Base):
    """
    Comprehensive audit trail for compliance
    
    - User actions
    - Data access
    - Configuration changes
    - Incident modifications
    """
    
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_timestamp", "timestamp"),
    )
    
    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Who & When
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # What
    action = Column(String(100), nullable=False)  # "view_incident", "modify_incident", "export_data", etc.
    resource_type = Column(String(100), nullable=False)  # "incident", "event", "alert", "user", etc.
    resource_id = Column(String(36), nullable=True)
    
    # How
    details = Column(JSON, nullable=True)  # Detailed information about the action
    old_values = Column(JSON, nullable=True)  # For modifications
    new_values = Column(JSON, nullable=True)  # For modifications
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default="SUCCESS")  # "SUCCESS", "FAILURE", etc.
    error_message = Column(Text, nullable=True)
    
    # Tenancy
    tenant_id = Column(String(100), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.log_id} - {self.action}>"


# ==========================================
# JUNCTION TABLES (Many-to-Many)
# ==========================================

class EventIncidents(Base):
    """
    Many-to-many relationship between events and incidents
    """
    __tablename__ = "event_incidents"
    
    event_id = Column(String(36), ForeignKey("events.event_id"), primary_key=True)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), primary_key=True)
    
    # When this event was linked to the incident
    linked_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ==========================================
# METRICS & PERFORMANCE (Phase 3)
# ==========================================

class MetricSnapshot(Base):
    """
    Time-series metrics for performance monitoring
    
    - Event ingestion rate
    - Detection latency
    - Incident resolution time
    - System health
    """
    
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        Index("idx_metric_timestamp", "timestamp"),
        Index("idx_metric_name", "metric_name"),
    )
    
    snapshot_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metric identification
    metric_name = Column(String(255), nullable=False)  # "events_per_sec", "avg_detection_latency_ms", etc.
    metric_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)  # "events/sec", "ms", "%", etc.
    
    # Timeline
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Tags for grouping
    tags = Column(JSON, nullable=True)  # {"service": "api", "endpoint": "/incidents"}
    
    # Tenancy
    tenant_id = Column(String(100), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Metric {self.metric_name} - {self.metric_value}{self.unit}>"


def create_all_tables(engine, echo=False):
    """Create all tables in the database"""
    Base.metadata.create_all(engine, checkfirst=True)
    print("✅ All database tables created successfully")


def drop_all_tables(engine):
    """Drop all tables (for testing/reset only)"""
    Base.metadata.drop_all(engine)
    print("✅ All database tables dropped")
