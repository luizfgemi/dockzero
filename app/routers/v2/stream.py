"""WebSocket endpoints for v2 container streaming."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.containers_stream import containers_stream

router = APIRouter()


@router.websocket("/containers/stream")
async def containers_stream_ws(websocket: WebSocket) -> None:
    """Stream container updates over a WebSocket connection."""
    await containers_stream.register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await containers_stream.unregister(websocket)


__all__ = ["router"]
