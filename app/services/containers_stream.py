"""Shared streaming state for v2 container updates."""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import suppress
from typing import Any

from fastapi import WebSocket

from app.core.config import AUTO_REFRESH_SECONDS
from app.core.docker import get_docker_client
from app.services.docker_service import list_container_summaries


def _deep_copy(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a JSON-safe deep copy of the container list."""
    return json.loads(json.dumps(data))


def _collect_snapshot() -> tuple[str, list[dict[str, Any]]]:
    """Fetch container summaries and return serialized payload + raw data."""
    client = get_docker_client()
    data = list_container_summaries(client, include_metrics=True)
    message: dict[str, Any] = {"type": "containers", "containers": data}
    return json.dumps(message, ensure_ascii=False), data


class ContainersStream:
    """Manage cached container data and broadcast updates to WebSocket clients."""

    def __init__(self, interval: float) -> None:
        self._interval = max(0.2, float(interval))
        self._cache_lock = asyncio.Lock()
        self._cached_payload: str | None = None
        self._cached_data: list[dict[str, Any]] | None = None
        self._cached_at: float = 0.0

        self._clients_lock = asyncio.Lock()
        self._clients: set[WebSocket] = set()
        self._task: asyncio.Task[None] | None = None

        self._force_refresh = asyncio.Event()

    async def get_snapshot(self, *, max_age: float | None = None) -> list[dict[str, Any]]:
        """Return a cached snapshot, refreshing if stale."""
        payload, data = await self._ensure_snapshot(max_age=max_age)
        # _ensure_snapshot returns the cache reference; provide a deep copy to callers.
        return _deep_copy(data)

    async def get_payload(self, *, max_age: float | None = None) -> str:
        """Return the serialized payload used by WebSocket clients."""
        payload, _ = await self._ensure_snapshot(max_age=max_age)
        return payload

    async def _ensure_snapshot(
        self,
        *,
        max_age: float | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Ensure there is a fresh snapshot and return (payload, data)."""
        async with self._cache_lock:
            if (
                self._cached_payload is not None
                and self._cached_data is not None
                and (max_age is None or time.monotonic() - self._cached_at <= max_age)
            ):
                return self._cached_payload, self._cached_data

        payload, data = await self._refresh_snapshot()
        return payload, data

    async def _refresh_snapshot(self) -> tuple[str, list[dict[str, Any]]]:
        """Fetch a fresh snapshot and update the cache."""
        loop = asyncio.get_running_loop()
        payload, data = await loop.run_in_executor(None, _collect_snapshot)
        async with self._cache_lock:
            self._cached_payload = payload
            self._cached_data = data
            self._cached_at = time.monotonic()
        return payload, data

    async def register(self, websocket: WebSocket) -> None:
        """Attach a WebSocket client and ensure background updates run."""
        await websocket.accept()

        payload = await self.get_payload()
        with suppress(Exception):
            await websocket.send_text(payload)

        async with self._clients_lock:
            self._clients.add(websocket)
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._run())

    async def unregister(self, websocket: WebSocket) -> None:
        """Detach a WebSocket client."""
        async with self._clients_lock:
            self._clients.discard(websocket)
            if not self._clients and self._task:
                self._task.cancel()
                self._task = None

    async def poke(self) -> None:
        """Request an immediate refresh on the next loop iteration."""
        self._force_refresh.set()

    async def _run(self) -> None:
        """Background loop that keeps pushing updates to WebSocket clients."""
        try:
            while True:
                await self._wait_for_next_cycle()
                payload, _ = await self._refresh_snapshot()

                async with self._clients_lock:
                    clients = list(self._clients)

                stale: list[WebSocket] = []
                for ws in clients:
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        stale.append(ws)

                if stale:
                    async with self._clients_lock:
                        for ws in stale:
                            self._clients.discard(ws)
        except asyncio.CancelledError:
            raise

    async def _wait_for_next_cycle(self) -> None:
        """Wait for either the interval to elapse or an explicit poke."""
        if self._force_refresh.is_set():
            self._force_refresh.clear()
            return
        try:
            await asyncio.wait_for(self._force_refresh.wait(), timeout=self._interval)
        except asyncio.TimeoutError:
            return
        finally:
            self._force_refresh.clear()


containers_stream = ContainersStream(interval=AUTO_REFRESH_SECONDS)

__all__ = ["containers_stream"]
