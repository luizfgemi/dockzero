"""Application configuration constants."""
from __future__ import annotations

import os

APP_TITLE: str = os.getenv("APP_TITLE", "Docker Dashboard")
"""Display title used across the web UI."""

APP_LOCALE: str = os.getenv("APP_LOCALE", "en").lower()
"""Locale used to select translated UI messages."""

WSL_DISTRO: str = os.getenv("WSL_DISTRO", "Ubuntu")
"""Default WSL distribution used to build exec commands."""

EXEC_SHELL: str = os.getenv("EXEC_SHELL", "bash")
"""Shell used when opening a container exec session from host-based profiles."""

EXEC_COMMAND_PROFILES: str = os.getenv("EXEC_COMMAND_PROFILES", "all")
"""Comma separated list indicating which exec command profiles to expose."""


def _get_int_env(name: str, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
    """Return an integer environment variable with optional bounds."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _get_float_env(name: str, default: float, *, minimum: float | None = None) -> float:
    """Return a float environment variable with an optional lower bound."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(value, minimum)
    return value


LINK_SCHEME: str = os.getenv("LINK_SCHEME", "http")
"""Scheme used to build external links for mapped container ports."""

LINK_HOST: str = os.getenv("LINK_HOST", "localhost")
"""Host used to build external links for mapped container ports."""

AUTO_REFRESH_SECONDS: int = _get_int_env("AUTO_REFRESH_SECONDS", 10, minimum=1)
"""Refresh interval (in seconds) for the dashboard polling loop."""

LOG_REFRESH_SECONDS: int = _get_int_env("LOG_REFRESH_SECONDS", 5, minimum=1)
"""Refresh interval (in seconds) for the logs page polling loop."""

_LOG_DEFAULT_TAIL = _get_int_env("LOG_DEFAULT_TAIL", 200, minimum=1)
_LOG_MAX_TAIL = _get_int_env("LOG_MAX_TAIL", 5000, minimum=1)

LOG_MAX_TAIL: int = _LOG_MAX_TAIL
"""Maximum number of log lines that can be tailed via the API."""

LOG_DEFAULT_TAIL: int = min(_LOG_DEFAULT_TAIL, LOG_MAX_TAIL)
"""Default number of log lines returned when not specified by the user."""

ACTION_DELAY_SECONDS: float = _get_float_env("ACTION_DELAY_SECONDS", 0.1, minimum=0.0)
"""Sleep duration after container actions to let Docker settle."""

__all__ = [
    "APP_TITLE",
    "APP_LOCALE",
    "WSL_DISTRO",
    "LINK_SCHEME",
    "LINK_HOST",
    "AUTO_REFRESH_SECONDS",
    "LOG_REFRESH_SECONDS",
    "LOG_MAX_TAIL",
    "LOG_DEFAULT_TAIL",
    "ACTION_DELAY_SECONDS",
    "EXEC_SHELL",
    "EXEC_COMMAND_PROFILES",
]
