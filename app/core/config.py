"""Application configuration constants."""
from __future__ import annotations

import os

WSL_DISTRO: str = os.getenv("DASHBOARD_WSL_DISTRO", "Ubuntu")
"""Default WSL distribution used to build exec commands."""
