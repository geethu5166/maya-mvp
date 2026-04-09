"""API v1 router"""

from fastapi import APIRouter
from . import endpoints

router = APIRouter()
router.include_router(endpoints.router, tags=["API"])
"""
API v1 router - Combines all endpoints
"""

from fastapi import APIRouter
from . import endpoints, websocket

router = APIRouter()

# Include regular endpoints
router.include_router(endpoints.router, tags=["API"])

# WebSocket already handles its own routing
