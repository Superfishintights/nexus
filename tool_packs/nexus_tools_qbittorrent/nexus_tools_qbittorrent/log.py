"""qBittorrent log tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Get qBittorrent main log entries.",
    examples=[
        "load_tool(\"qbittorrent.log_get_main\")(...)",
    ],
)
def log_get_main(normal: Optional[bool] = None, info: Optional[bool] = None, warning: Optional[bool] = None, critical: Optional[bool] = None, last_known_id: Optional[int] = None) -> Any:
    """Get qBittorrent main log entries."""
    client = get_client()
    params = {"normal": normal, "info": info, "warning": warning, "critical": critical, "last_known_id": last_known_id}
    return client.get("log/main")

@register_tool(
    namespace="qbittorrent",
    description="Get qBittorrent peer log entries.",
    examples=[
        "load_tool(\"qbittorrent.log_get_peers\")(...)",
    ],
)
def log_get_peers(last_known_id: Optional[int] = None) -> Any:
    """Get qBittorrent peer log entries."""
    client = get_client()
    return client.get("log/peers", params={"last_known_id": last_known_id})
