"""Business logic for interacting with Docker containers."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any

from docker import DockerClient
from docker.errors import NotFound
from docker.models.containers import Container

from app.core.config import ACTION_DELAY_SECONDS, EXEC_SHELL, LINK_HOST, LINK_SCHEME, LOG_MAX_TAIL

VALID_ACTIONS = {"start", "stop", "restart"}
_STATS_CACHE_TTL_SECONDS = 2.0
_STATS_CACHE: dict[str, tuple[float, dict[str, Any] | None]] = {}
_STATS_CACHE_LOCK = Lock()


def first_mapped_port_from_summary(port_mappings: list[dict[str, Any]] | None) -> str | None:
    """Return the first mapped host port from a container summary entry."""
    if not port_mappings:
        return None
    for mapping in port_mappings:
        host_port = mapping.get("PublicPort")
        if host_port:
            return str(host_port)
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


def _get_cached_stats(container_id: str) -> dict[str, Any] | None:
    """Return cached stats if they are still within the TTL window."""
    now = time.monotonic()
    with _STATS_CACHE_LOCK:
        cached = _STATS_CACHE.get(container_id)
        if not cached:
            return None
        ts, data = cached
        if now - ts <= _STATS_CACHE_TTL_SECONDS:
            return data
        _STATS_CACHE.pop(container_id, None)
        return None


def _set_cached_stats(container_id: str, stats: dict[str, Any] | None) -> None:
    """Store stats in the cache."""
    with _STATS_CACHE_LOCK:
        _STATS_CACHE[container_id] = (time.monotonic(), stats)


def _collect_stats(containers: list[Container]) -> dict[str, dict[str, Any] | None]:
    """Return a mapping of container id -> stats using caching and parallel calls."""
    stats_map: dict[str, dict[str, Any] | None] = {}
    to_fetch: list[Container] = []

    for container in containers:
        if container.status != "running":
            stats_map[container.id] = None
            continue

        cached = _get_cached_stats(container.id)
        if cached is not None:
            stats_map[container.id] = cached
        else:
            to_fetch.append(container)

    if not to_fetch:
        return stats_map

    max_workers = min(4, len(to_fetch))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_stats, container): container.id for container in to_fetch}
        for future, container_id in futures.items():
            stats = future.result()
            _set_cached_stats(container_id, stats)
            stats_map[container_id] = stats

    return stats_map


def _fetch_stats(container: Container) -> dict[str, Any] | None:
    """Fetch stats for a container, returning None on failure."""
    try:
        return container.stats(stream=False)
    except Exception:
        return None


def _status_from_summary(summary: dict[str, Any]) -> str:
    """Normalize the container state string from a Docker summary."""
    state = (summary.get("State") or "").lower()
    if not state:
        status = (summary.get("Status") or "").lower()
        if status.startswith("up"):
            return "running"
        if status.startswith("exited") or status.startswith("created"):
            return "stopped"
        return status or "unknown"
    return state


def list_container_summaries(client: DockerClient, *, include_metrics: bool = True) -> list[dict[str, Any]]:
    """Return the dashboard payload for all containers."""
    summaries = client.api.containers(all=True)

    metrics_by_name: dict[str, dict[str, float | None]] = {}
    if include_metrics:
        container_objs = [client.containers.get(summary["Id"]) for summary in summaries]
        stats_map = _collect_stats(container_objs)
        for container in container_objs:
            stats = stats_map.get(container.id)
            cpu = calc_cpu_percent(stats) if stats else None
            mem = calc_mem_mb(stats) if stats else None
            metrics_by_name[container.name] = {
                "cpu": round(cpu, 1) if cpu is not None else None,
                "mem_mb": round(mem, 0) if mem is not None else None,
            }

    result: list[dict[str, Any]] = []
    for summary in summaries:
        raw_name = (summary.get("Names") or [""])[0]
        name = raw_name.lstrip("/") if raw_name else summary.get("Id", "")[:12]
        host_port = first_mapped_port_from_summary(summary.get("Ports"))
        link = f"{LINK_SCHEME}://{LINK_HOST}:{host_port}" if host_port else None
        status = _status_from_summary(summary)
        metrics = metrics_by_name.get(name, {"cpu": None, "mem_mb": None})

        result.append(
            {
                "name": name,
                "status": status,
                "link": link,
                "cpu": metrics["cpu"],
                "mem_mb": metrics["mem_mb"],
            }
        )
    return result


def get_containers_metrics(client: DockerClient, names: list[str] | None = None) -> dict[str, dict[str, float | None]]:
    """Return CPU and memory metrics for the requested containers."""
    containers = client.containers.list(all=True)
    if names:
        requested = {name: None for name in names}
        containers = [c for c in containers if c.name in requested]
    stats_map = _collect_stats(containers)

    metrics: dict[str, dict[str, float | None]] = {}
    for container in containers:
        stats = stats_map.get(container.id)
        cpu = calc_cpu_percent(stats) if stats else None
        mem = calc_mem_mb(stats) if stats else None
        metrics[container.name] = {
            "cpu": round(cpu, 1) if cpu is not None else None,
            "mem_mb": round(mem, 0) if mem is not None else None,
        }

    return metrics


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
