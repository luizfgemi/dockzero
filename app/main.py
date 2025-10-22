"""Application entry point for the Docker dashboard."""
from __future__ import annotations

from fastapi import FastAPI

from app.routers import ROUTERS

app = FastAPI(title="Docker Dashboard")

for router in ROUTERS:
    app.include_router(router)

__all__ = ["app"]
