"""Routes related to opening containers in a terminal."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import APP_LOCALE, APP_TITLE
from app.core.i18n import get_messages
from app.services.docker_service import build_exec_commands
from app.views.terminal import render_terminal_page

router = APIRouter()
MESSAGES = get_messages(APP_LOCALE)


@router.get("/exec/{name}", response_class=HTMLResponse)
def open_in_terminal(name: str) -> HTMLResponse:
    """Render the helper page with the docker exec command."""
    commands = build_exec_commands(name)
    return HTMLResponse(render_terminal_page(name, commands, APP_TITLE, MESSAGES))
