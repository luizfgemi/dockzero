"""Version 2 router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from .containers import router as containers_router
from .stream import router as stream_router

router = APIRouter(prefix="/v2")

for child in (containers_router, stream_router):
    router.include_router(child)

__all__ = ["router", "containers_router", "stream_router"]
