"""Routes related to opening containers in a terminal."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import APP_LOCALE, APP_TITLE, WSL_DISTRO
from app.core.i18n import get_messages
from app.services.docker_service import build_exec_command
from app.views.terminal import render_terminal_page

router = APIRouter()
MESSAGES = get_messages(APP_LOCALE)


@router.get("/exec/{name}", response_class=HTMLResponse)
def open_in_terminal(name: str) -> HTMLResponse:
    """Render the helper page with the docker exec command."""
    command = build_exec_command(name, WSL_DISTRO)
    return HTMLResponse(render_terminal_page(name, command, APP_TITLE, MESSAGES))
