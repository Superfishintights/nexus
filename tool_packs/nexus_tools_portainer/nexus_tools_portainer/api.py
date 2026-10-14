"""Focused Portainer status and container control tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="portainer",
    name="get_health",
    description="Get the public Portainer status payload for a cheap health check.",
    examples=['load_tool("portainer.get_health")()'],
)
def get_health() -> Dict[str, Any]:
    """Return Portainer `/status` information."""
    return get_client().health()


@register_tool(
    namespace="portainer",
    name="get_system_status",
    description="Get authenticated Portainer system status.",
    examples=['load_tool("portainer.get_system_status")()'],
)
def get_system_status() -> Dict[str, Any]:
    """Return Portainer `/system/status` information."""
    return get_client().system_status()


@register_tool(
    namespace="portainer",
    name="get_system_version",
    description="Get the Portainer server version.",
    examples=['load_tool("portainer.get_system_version")()'],
)
def get_system_version() -> Dict[str, Any]:
    """Return Portainer `/system/version` information."""
    return get_client().system_version()


@register_tool(
    namespace="portainer",
    name="list_environments",
    description="List Portainer environments/endpoints available to the configured credential.",
    examples=['load_tool("portainer.list_environments")()'],
)
def list_environments(
    group_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """List environments/endpoints so callers can choose a Docker endpoint."""
    return get_client().list_environments(group_id=group_id, tag_ids=tag_ids)


@register_tool(
    namespace="portainer",
    name="inspect_environment",
    description="Inspect one Portainer environment/endpoint by id.",
    examples=['load_tool("portainer.inspect_environment")(1)'],
)
def inspect_environment(endpoint_id: int) -> Dict[str, Any]:
    """Inspect a Portainer environment/endpoint."""
    return get_client().inspect_environment(endpoint_id)


@register_tool(
    namespace="portainer",
    name="list_containers",
    description="List Docker containers for a Portainer endpoint, optionally filtering to Plex/media services.",
    examples=[
        'load_tool("portainer.list_containers")(1)',
        'load_tool("portainer.list_containers")(1, search="plex", media_only=True)',
    ],
)
def list_containers(
    endpoint_id: int,
    *,
    all_containers: bool = True,
    search: Optional[str] = None,
    media_only: bool = False,
) -> List[Dict[str, Any]]:
    """List containers through Portainer's Docker proxy."""
    return get_client().list_containers(
        endpoint_id,
        all_containers=all_containers,
        search=search,
        media_only=media_only,
    )


@register_tool(
    namespace="portainer",
    name="search_containers",
    description="Search containers by id, name, image, status, command, or label text on a Portainer endpoint.",
    examples=['load_tool("portainer.search_containers")(1, "plex")'],
)
def search_containers(
    endpoint_id: int,
    query: str,
    *,
    media_only: bool = False,
) -> List[Dict[str, Any]]:
    """Search containers on one endpoint."""
    return get_client().list_containers(endpoint_id, search=query, media_only=media_only)


@register_tool(
    namespace="portainer",
    name="inspect_container",
    description="Inspect a Docker container through Portainer by endpoint id and container id/name.",
    examples=['load_tool("portainer.inspect_container")(1, "plex")'],
)
def inspect_container(endpoint_id: int, container_id: str) -> Dict[str, Any]:
    """Inspect a Docker container through Portainer's Docker proxy."""
    return get_client().inspect_container(endpoint_id, container_id)


@register_tool(
    namespace="portainer",
    name="get_container_status",
    description="Get a compact status summary for one Docker container through Portainer.",
    examples=['load_tool("portainer.get_container_status")(1, "plex")'],
)
def get_container_status(endpoint_id: int, container_id: str) -> Dict[str, Any]:
    """Return compact container status fields."""
    return get_client().container_status(endpoint_id, container_id)


@register_tool(
    namespace="portainer",
    name="resolve_container",
    description="Resolve one container by exact name or id prefix, failing if the match is missing or ambiguous.",
    examples=['load_tool("portainer.resolve_container")(1, "plex", media_only=True)'],
)
def resolve_container(endpoint_id: int, name: str, *, media_only: bool = False) -> Dict[str, Any]:
    """Resolve a single container safely before control operations."""
    return get_client().resolve_container(endpoint_id, name, media_only=media_only)


@register_tool(
    namespace="portainer",
    name="start_container",
    description="Start a Docker container through Portainer.",
    examples=['load_tool("portainer.start_container")(1, "plex")'],
    tool_class="admin",
)
def start_container(endpoint_id: int, container_id: str) -> Dict[str, Any]:
    """Start a Docker container through Portainer."""
    return get_client().control_container("start", endpoint_id, container_id)


@register_tool(
    namespace="portainer",
    name="stop_container",
    description="Stop a Docker container through Portainer, optionally with Docker timeout seconds.",
    examples=['load_tool("portainer.stop_container")(1, "plex", timeout_s=30)'],
    tool_class="admin",
)
def stop_container(endpoint_id: int, container_id: str, *, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    """Stop a Docker container through Portainer."""
    return get_client().control_container("stop", endpoint_id, container_id, timeout_s=timeout_s)


@register_tool(
    namespace="portainer",
    name="restart_container",
    description="Restart a Docker container through Portainer, optionally with Docker timeout seconds.",
    examples=['load_tool("portainer.restart_container")(1, "plex", timeout_s=30)'],
    tool_class="admin",
)
def restart_container(endpoint_id: int, container_id: str, *, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    """Restart a Docker container through Portainer."""
    return get_client().control_container("restart", endpoint_id, container_id, timeout_s=timeout_s)
