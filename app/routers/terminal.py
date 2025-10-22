"""Routes related to opening containers in a terminal."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import WSL_DISTRO
from app.services.docker_service import build_exec_command
from app.views.terminal import render_terminal_page

router = APIRouter()


@router.get("/exec/{name}", response_class=HTMLResponse)
def open_in_terminal(name: str) -> HTMLResponse:
    """Render the helper page with the docker exec command."""
    command = build_exec_command(name, WSL_DISTRO)
    return HTMLResponse(render_terminal_page(name, command))
