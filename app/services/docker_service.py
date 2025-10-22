"""Business logic for interacting with Docker containers."""
from __future__ import annotations

import time
from typing import Any

from docker import DockerClient
from docker.errors import NotFound
from docker.models.containers import Container

from app.core.config import ACTION_DELAY_SECONDS, EXEC_SHELL, LINK_HOST, LINK_SCHEME, LOG_MAX_TAIL

VALID_ACTIONS = {"start", "stop", "restart"}


def first_mapped_port(container: Container) -> str | None:
    """Return the first mapped host port for a container, if any."""
    ports = (container.attrs.get("NetworkSettings", {}) or {}).get("Ports", {}) or {}
    for mappings in ports.values():
        if mappings:
            host_port = mappings[0].get("HostPort")
            if host_port:
                return host_port
    return None


def calc_cpu_percent(stats: dict[str, Any]) -> float | None:
    """Calculate CPU usage percentage based on Docker stats output."""
    try:
        cpu_stats = stats.get("cpu_stats", {})
        precpu = stats.get("precpu_stats", {})
        cpu_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        pre_total = precpu.get("cpu_usage", {}).get("total_usage", 0)
        sys_total = cpu_stats.get("system_cpu_usage", 0)
        pre_sys = precpu.get("system_cpu_usage", 0)
        online_cpus = cpu_stats.get("online_cpus")
        if online_cpus is None:
            percpu = cpu_stats.get("cpu_usage", {}).get("percpu_usage") or []
            online_cpus = len(percpu) or 1

        cpu_delta = cpu_total - pre_total
        sys_delta = sys_total - pre_sys
        if cpu_delta > 0 and sys_delta > 0 and online_cpus:
            return (cpu_delta / sys_delta) * online_cpus * 100.0
    except Exception:
        return None
    return None


def calc_mem_mb(stats: dict[str, Any]) -> float | None:
    """Return memory usage in megabytes based on Docker stats output."""
    try:
        mem_stats = stats.get("memory_stats", {}) or {}
        usage = float(mem_stats.get("usage", 0.0))
        return usage / (1024 * 1024)
    except Exception:
        return None


def list_container_summaries(client: DockerClient) -> list[dict[str, Any]]:
    """Return the dashboard payload for all containers."""
    result: list[dict[str, Any]] = []
    containers = client.containers.list(all=True)
    for container in containers:
        host_port = first_mapped_port(container)
        link = f"{LINK_SCHEME}://{LINK_HOST}:{host_port}" if host_port else None

        cpu = None
        mem = None
        try:
            stats = container.stats(stream=False)
        except Exception:
            stats = None

        if stats:
            cpu = calc_cpu_percent(stats)
            mem = calc_mem_mb(stats)

        result.append(
            {
                "name": container.name,
                "status": container.status,
                "link": link,
                "cpu": round(cpu, 1) if cpu is not None else None,
                "mem_mb": round(mem, 0) if mem is not None else None,
            }
        )
    return result


def perform_container_action(client: DockerClient, name: str, action: str) -> None:
    """Execute an action (start/stop/restart) on a container."""
    if action not in VALID_ACTIONS:
        raise ValueError("invalid operation")

    try:
        container = client.containers.get(name)
    except NotFound as exc:  # pragma: no cover - passthrough for FastAPI
        raise exc

    if action == "restart":
        container.restart()
    elif action == "stop":
        container.stop()
    elif action == "start":
        container.start()

    if ACTION_DELAY_SECONDS > 0:
        time.sleep(ACTION_DELAY_SECONDS)


def get_container_logs(client: DockerClient, name: str, tail: int) -> str:
    """Return the textual logs for a container."""
    tail = max(1, min(tail, LOG_MAX_TAIL))
    container = client.containers.get(name)
    try:
        logs = container.logs(tail=tail)
    except Exception as exc:
        return f"[error] {exc}"
    return logs.decode("utf-8", errors="ignore")


def build_exec_command(name: str, distro: str) -> str:
    """Build the Windows Terminal command for opening a shell in the container."""
    return f"wsl -d {distro} docker exec -it {name} {EXEC_SHELL}"
