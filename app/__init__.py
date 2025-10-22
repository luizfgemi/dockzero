"""Expose the FastAPI application instance for ASGI servers."""
from __future__ import annotations

from .main import app

__all__ = ["app"]
