"""
Incident model - Security incident correlation and tracking.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class IncidentStatus(str, Enum):
    """Incident lifecycle states"""
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class IncidentType(str, Enum):
    """Incident types"""
    RECONNAISSANCE = "RECONNAISSANCE"
    INITIAL_ACCESS = "INITIAL_ACCESS"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"


class IncidentBase(BaseModel):
    """Base incident schema"""
    title: str
    description: str
    incident_type: IncidentType
    status: IncidentStatus = IncidentStatus.DETECTED
    severity: str
    affected_systems: List[str] = []
    related_events: List[str] = []
    metadata: Dict[str, Any] = {}


class IncidentCreate(IncidentBase):
    """Incident creation request"""
    pass


class Incident(IncidentBase):
    """Incident response"""
    incident_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
