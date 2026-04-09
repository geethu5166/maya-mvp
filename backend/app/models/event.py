"""
Event model - Unified security event schema.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class EventType(str, Enum):
    """Security event types"""
    SSH_BRUTE_FORCE = "SSH_BRUTE_FORCE"
    WEB_SCAN = "WEB_SCAN"
    DB_PROBE = "DB_PROBE"
    CANARY_TRIGGER = "CANARY_TRIGGER"
    ANOMALY = "ANOMALY"
    HONEYPOT_INTERACTION = "HONEYPOT_INTERACTION"


class SeverityLevel(str, Enum):
    """Event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EventBase(BaseModel):
    """Base event schema"""
    event_type: EventType
    severity: SeverityLevel
    source_ip: str
    destination_ip: str
    payload_short: str = Field(..., max_length=500)
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    """Event creation request"""
    module: str


class Event(EventBase):
    """Event response"""
    event_id: str
    timestamp: datetime
    module: str
    
    class Config:
        from_attributes = True
