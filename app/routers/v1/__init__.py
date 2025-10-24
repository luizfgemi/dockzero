"""Version 1 router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.auth import require_v1_basic_auth

from .containers import router as containers_router
from .dashboard import router as dashboard_router
from .inspect import router as inspect_router
from .logs import router as logs_router
from .terminal import router as terminal_router

router = APIRouter(prefix="/v1", dependencies=[require_v1_basic_auth])

for child in (
    dashboard_router,
    containers_router,
    logs_router,
    terminal_router,
    inspect_router,
):
    router.include_router(child)

__all__ = [
    "router",
    "containers_router",
    "dashboard_router",
    "inspect_router",
    "logs_router",
    "terminal_router",
]
