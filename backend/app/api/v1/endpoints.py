"""API v1 endpoints"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from app.core.security import TokenManager, get_current_user, get_admin_user
from app.core.config import get_settings
from app.core.event_bus import event_bus, SecurityEvent
from app.models.event import EventCreate
from app.models.incident import IncidentCreate

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if request.username == settings.INIT_ADMIN_USERNAME and request.password == settings.INIT_ADMIN_PASSWORD:
        token = TokenManager.create_access_token({"sub": request.username, "scopes": ["admin"]})
        return LoginResponse(access_token=token)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/events")
async def get_events(current_user: dict = Depends(get_current_user)):
    return {"total": 0, "events": []}


@router.post("/events", status_code=201)
async def create_event(event: EventCreate, current_user: dict = Depends(get_current_user)):
    event_id = str(uuid.uuid4())
    sec_event = SecurityEvent(
        event_id=event_id,
        event_type=event.event_type.value,
        severity=event.severity.value,
        source_ip=event.source_ip,
        destination_ip=event.destination_ip,
        timestamp=datetime.utcnow().isoformat(),
        description=event.description,
        metadata=event.metadata,
        module=event.module
    )
    await event_bus.publish_event(settings.KAFKA_TOPIC_EVENTS, sec_event)
    return {"event_id": event_id, "status": "published"}


@router.get("/incidents")
async def get_incidents(current_user: dict = Depends(get_current_user)):
    return {"total": 0, "incidents": []}


@router.post("/incidents", status_code=201)
async def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_admin_user)):
    return {"incident_id": str(uuid.uuid4()), "status": "created"}


@router.get("/health")
async def health():
    return {"status": "ok"}
