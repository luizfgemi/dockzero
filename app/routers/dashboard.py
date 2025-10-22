"""Routes for dashboard-related pages."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.views.dashboard import render_dashboard

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    """Render the main dashboard page."""
    return HTMLResponse(content=render_dashboard())
