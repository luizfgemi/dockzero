"""Routes for viewing container logs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from docker import DockerClient

from app.core.docker import get_docker_client
from app.services.docker_service import get_container_logs
from app.views.logs import render_logs_page

router = APIRouter()


@router.get("/logs/{name}", response_class=HTMLResponse)
def container_logs(name: str, tail: int = Query(default=200, ge=1, le=5000)) -> HTMLResponse:
    """Return the HTML page that auto-refreshes container logs."""
    return HTMLResponse(render_logs_page(name, tail))


@router.get("/logs_raw/{name}", response_class=PlainTextResponse)
def container_logs_raw(
    name: str,
    tail: int = Query(default=200, ge=1, le=5000),
    client: DockerClient = Depends(get_docker_client),
) -> PlainTextResponse:
    """Return the textual logs used by the HTML view."""
    logs = get_container_logs(client, name, tail)
    return PlainTextResponse(logs)
