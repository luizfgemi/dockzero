"""Helpers for interacting with the Docker daemon."""
from __future__ import annotations

from functools import lru_cache

import docker
from docker import DockerClient


@lru_cache
def get_docker_client() -> DockerClient:
    """Return a cached Docker client instance."""
    return docker.from_env()
