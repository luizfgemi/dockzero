"""FastAPI routers bundled by the application."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from .v1 import router as v1_router
from .v2 import router as v2_router

root_router = APIRouter()
api_router = APIRouter()
api_router.include_router(v1_router)
api_router.include_router(v2_router)


@root_router.get("/", include_in_schema=False)
async def redirect_to_v1() -> RedirectResponse:
    """Redirect the base URL to the v1 dashboard."""
    return RedirectResponse(url="/v1/")


ROUTERS = [root_router, api_router]

__all__ = [
    "ROUTERS",
    "api_router",
    "root_router",
    "v1_router",
    "v2_router",
]
