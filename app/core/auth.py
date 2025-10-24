"""Authentication helpers for API routes."""
from __future__ import annotations

import secrets
from ipaddress import ip_address

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import V1_AUTH_ALLOW_LOOPBACK, V1_AUTH_ENABLED, V1_AUTH_PASSWORD, V1_AUTH_USERNAME

_basic_security = HTTPBasic(auto_error=False)


def _is_loopback(host: str | None) -> bool:
    """Return True if the client host is a loopback address."""
    if not host:
        return False
    if host in {"localhost", "127.0.0.1"}:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def build_basic_auth_dependency(
    *,
    enabled: bool,
    username: str | None,
    password: str | None,
    allow_loopback: bool = True,
) -> Depends:
    """Return a dependency that enforces HTTP Basic authentication with optional loopback bypass."""

    async def _dependency(
        request: Request,
        credentials: HTTPBasicCredentials | None = Depends(_basic_security),
    ) -> None:
        if not enabled:
            return

        client = request.client
        if allow_loopback and client and _is_loopback(client.host):
            return

        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"},
            )

        username_ok = secrets.compare_digest(credentials.username, username or "")
        password_ok = secrets.compare_digest(credentials.password, password or "")
        if not (username_ok and password_ok):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

    return Depends(_dependency)


require_v1_basic_auth = build_basic_auth_dependency(
    enabled=V1_AUTH_ENABLED,
    username=V1_AUTH_USERNAME,
    password=V1_AUTH_PASSWORD,
    allow_loopback=V1_AUTH_ALLOW_LOOPBACK,
)

__all__ = ["build_basic_auth_dependency", "require_v1_basic_auth"]
