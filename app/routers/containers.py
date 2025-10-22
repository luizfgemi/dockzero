"""Routes that expose container data and actions."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from docker import DockerClient
from docker.errors import NotFound

from app.core.docker import get_docker_client
from app.services.docker_service import list_container_summaries, perform_container_action

router = APIRouter()


@router.get("/containers", response_class=JSONResponse)
def list_containers(client: DockerClient = Depends(get_docker_client)) -> JSONResponse:
    """Return the list of containers displayed on the dashboard."""
    data = list_container_summaries(client)
    return JSONResponse(data)


@router.post("/action/{name}/{action}", response_class=JSONResponse)
def container_action(
    name: str,
    action: str,
    client: DockerClient = Depends(get_docker_client),
) -> JSONResponse:
    """Execute an action on the requested container."""
    try:
        perform_container_action(client, name, action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"ok": True})
