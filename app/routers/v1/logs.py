"""Routes for viewing container logs (v1)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from docker import DockerClient

from app.core.config import APP_LOCALE, APP_TITLE, LOG_DEFAULT_TAIL, LOG_MAX_TAIL, LOG_REFRESH_SECONDS
from app.core.docker import get_docker_client
from app.core.i18n import get_messages
from app.services.docker_service import get_container_logs
from app.views.logs import render_logs_page

router = APIRouter()
MESSAGES = get_messages(APP_LOCALE)


@router.get("/logs/{name}", response_class=HTMLResponse)
def container_logs(
    name: str,
    tail: int = Query(default=LOG_DEFAULT_TAIL, ge=1, le=LOG_MAX_TAIL),
) -> HTMLResponse:
    """Return the HTML page that auto-refreshes container logs."""
    return HTMLResponse(
        render_logs_page(
            name,
            tail,
            LOG_REFRESH_SECONDS,
            LOG_MAX_TAIL,
            APP_TITLE,
            MESSAGES,
            base_path="/v1",
        )
    )


@router.get("/logs_raw/{name}", response_class=PlainTextResponse)
def container_logs_raw(
    name: str,
    tail: int = Query(default=LOG_DEFAULT_TAIL, ge=1, le=LOG_MAX_TAIL),
    client: DockerClient = Depends(get_docker_client),
) -> PlainTextResponse:
    """Return the textual logs used by the HTML view."""
    logs = get_container_logs(client, name, tail)
    return PlainTextResponse(logs)


__all__ = ["router"]
