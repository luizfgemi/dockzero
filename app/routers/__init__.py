"""FastAPI routers bundled by the application."""
from __future__ import annotations

from .containers import router as containers_router
from .dashboard import router as dashboard_router
from .logs import router as logs_router
from .terminal import router as terminal_router

ROUTERS = [dashboard_router, containers_router, logs_router, terminal_router]

__all__ = [
    "ROUTERS",
    "containers_router",
    "dashboard_router",
    "logs_router",
    "terminal_router",
]
