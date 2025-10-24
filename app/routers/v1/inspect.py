"""Routes for viewing detailed container information (v1)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from docker import DockerClient
from docker.errors import NotFound

from app.core.config import APP_LOCALE, APP_TITLE, AUTO_REFRESH_SECONDS
from app.core.docker import get_docker_client
from app.core.i18n import get_messages
from app.services.docker_service import get_container_inspect
from app.views.inspect import render_inspect_page

router = APIRouter()
MESSAGES = get_messages(APP_LOCALE)


@router.get("/inspect/{name}", response_class=HTMLResponse)
def inspect_container(
    name: str,
    client: DockerClient = Depends(get_docker_client),
) -> HTMLResponse:
    """Render the inspect page for a container."""
    try:
        data = get_container_inspect(client, name)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    html = render_inspect_page(
        name,
        data,
        AUTO_REFRESH_SECONDS,
        APP_TITLE,
        MESSAGES,
        base_path="/v1",
    )
    return HTMLResponse(html)


@router.get("/inspect_raw/{name}", response_class=JSONResponse)
def inspect_container_raw(
    name: str,
    client: DockerClient = Depends(get_docker_client),
) -> JSONResponse:
    """Return raw inspect data for async refresh."""
    try:
        data = get_container_inspect(client, name)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(data)


__all__ = ["router"]
