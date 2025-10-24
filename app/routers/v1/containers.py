"""Routes that expose container data and actions (v1)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from docker import DockerClient
from docker.errors import NotFound

from app.core.docker import get_docker_client
from app.services.docker_service import (
    get_containers_metrics,
    list_container_summaries,
    perform_container_action,
)

router = APIRouter()


@router.get("/containers", response_class=JSONResponse)
def list_containers(
    include_metrics: bool = Query(default=True),
    client: DockerClient = Depends(get_docker_client),
) -> JSONResponse:
    """Return the list of containers displayed on the dashboard."""
    data = list_container_summaries(client, include_metrics=include_metrics)
    return JSONResponse(data)


@router.get("/containers/metrics", response_class=JSONResponse)
def container_metrics(
    names: list[str] | None = Query(default=None),
    client: DockerClient = Depends(get_docker_client),
) -> JSONResponse:
    """Return CPU and memory metrics for the requested containers."""
    metrics = get_containers_metrics(client, names=names)
    return JSONResponse(metrics)


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


__all__ = ["router"]
