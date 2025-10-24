"""Routes for dashboard-related pages (v1)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import APP_LOCALE, APP_TITLE, AUTO_REFRESH_SECONDS
from app.core.i18n import get_messages
from app.views.dashboard import render_dashboard

router = APIRouter()
MESSAGES = get_messages(APP_LOCALE)


@router.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    """Render the main dashboard page."""
    return HTMLResponse(
        content=render_dashboard(
            AUTO_REFRESH_SECONDS,
            APP_TITLE,
            MESSAGES,
            base_path="/v1",
        )
    )


__all__ = ["router"]
