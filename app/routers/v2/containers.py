"""REST endpoints for v2 container operations."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from docker.errors import NotFound

from app.core.docker import get_docker_client
from app.services.containers_stream import containers_stream
from app.services.docker_service import (
    get_containers_metrics,
    list_container_summaries,
    perform_container_action,
)

router = APIRouter()


def _list_containers_sync(include_metrics: bool) -> list[dict[str, Any]]:
    """Fetch container summaries synchronously."""
    return list_container_summaries(get_docker_client(), include_metrics=include_metrics)


def _metrics_sync(names: list[str] | None) -> dict[str, dict[str, float | None]]:
    """Fetch metrics synchronously."""
    return get_containers_metrics(get_docker_client(), names=names)


async def _perform_action(name: str, action: str) -> None:
    """Run container action on a worker thread."""
    loop = asyncio.get_running_loop()

    def _runner() -> None:
        perform_container_action(get_docker_client(), name, action)

    await loop.run_in_executor(None, _runner)


@router.get("/containers", response_class=JSONResponse)
async def list_containers(include_metrics: bool = Query(default=True)) -> JSONResponse:
    """Return container summaries (optionally with metrics)."""
    if include_metrics:
        data = await containers_stream.get_snapshot()
        return JSONResponse(data)

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _list_containers_sync, False)
    return JSONResponse(data)


@router.get("/containers/metrics", response_class=JSONResponse)
async def container_metrics(names: list[str] | None = Query(default=None)) -> JSONResponse:
    """Return CPU and memory metrics for the requested containers."""
    loop = asyncio.get_running_loop()
    metrics = await loop.run_in_executor(None, _metrics_sync, names)
    return JSONResponse(metrics)


@router.post("/containers/{name}/{action}", response_class=JSONResponse)
async def container_action(name: str, action: str) -> JSONResponse:
    """Execute an action on the requested container."""
    try:
        await _perform_action(name, action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await containers_stream.poke()
    return JSONResponse({"ok": True})


__all__ = ["router"]
