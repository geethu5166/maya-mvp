"""API v1 endpoints"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from app.core.security import TokenManager, get_current_user, get_admin_user
from app.core.config import get_settings
from app.core.event_bus import event_bus, SecurityEvent
from app.models.event import EventCreate
from app.models.incident import IncidentCreate

router = APIRouter()
settings = get_settings()

_INCIDENT_STORE: List[Dict[str, Any]] = []
_EVENT_STORE: List[Dict[str, Any]] = []


def _paginate(items: List[Dict[str, Any]], page: int, limit: int) -> Dict[str, Any]:
    safe_page = max(page, 1)
    safe_limit = max(min(limit, 100), 1)
    total = len(items)
    start = (safe_page - 1) * safe_limit
    end = start + safe_limit
    pages = (total + safe_limit - 1) // safe_limit
    return {
        "items": items[start:end],
        "total": total,
        "page": safe_page,
        "per_page": safe_limit,
        "pages": pages,
    }


class LoginRequest(BaseModel):
    username: str
    password: str


class UserData(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserData


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if request.username == settings.INIT_ADMIN_USERNAME and request.password == settings.INIT_ADMIN_PASSWORD:
        token = TokenManager.create_access_token({"sub": request.username, "scopes": ["admin"]})
        user_data = UserData(
            user_id="admin-001",
            username=request.username,
            email="admin@maya-soc.local",
            roles=["admin"]
        )
        return LoginResponse(access_token=token, user=user_data)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/events")
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    items = list(reversed(_EVENT_STORE))
    return _paginate(items, page, limit)


@router.post("/events", status_code=201)
async def create_event(event: EventCreate, current_user: dict = Depends(get_current_user)):
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    sec_event = SecurityEvent(
        event_id=event_id,
        event_type=event.event_type.value,
        severity=event.severity.value,
        source_ip=event.source_ip,
        destination_ip=event.destination_ip,
        timestamp=timestamp,
        description=event.description,
        metadata=event.metadata,
        module=event.module,
    )
    if event_bus.running:
        await event_bus.publish_event(settings.KAFKA_TOPIC_EVENTS, sec_event)

    event_item = {
        "event_id": event_id,
        "event_type": event.event_type.value,
        "severity": event.severity.value,
        "timestamp": timestamp,
        "source_ip": event.source_ip,
        "destination_ip": event.destination_ip,
        "description": event.description,
        "details": event.metadata,
        "module": event.module,
    }
    _EVENT_STORE.append(event_item)
    return event_item


@router.get("/incidents")
async def get_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    items = list(reversed(_INCIDENT_STORE))
    return _paginate(items, page, limit)


@router.post("/incidents", status_code=201)
async def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_admin_user)):
    incident_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    incident_item = {
        "incident_id": incident_id,
        "title": incident.title,
        "description": incident.description,
        "severity": str(incident.severity).upper(),
        "status": incident.status.value if hasattr(incident.status, "value") else str(incident.status),
        "created_at": timestamp,
        "updated_at": timestamp,
        "events": [],
        "assignee": None,
        "tags": [],
    }
    _INCIDENT_STORE.append(incident_item)
    return incident_item


@router.get("/health")
async def health():
    return {"status": "ok"}
