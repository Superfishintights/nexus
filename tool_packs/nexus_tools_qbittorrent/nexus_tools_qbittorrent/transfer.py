"""qBittorrent transfer tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Get global transfer information.",
    examples=[
        "load_tool(\"qbittorrent.transfer_get_info\")(...)",
    ],
)
def transfer_get_info() -> Any:
    """Get global transfer information."""
    client = get_client()
    return client.get("transfer/info")

@register_tool(
    namespace="qbittorrent",
    description="Get whether alternative speed limits are enabled.",
    examples=[
        "load_tool(\"qbittorrent.transfer_get_speed_limits_mode\")(...)",
    ],
)
def transfer_get_speed_limits_mode() -> Any:
    """Get whether alternative speed limits are enabled."""
    client = get_client()
    return client.get("transfer/speedLimitsMode")

@register_tool(
    namespace="qbittorrent",
    description="Toggle alternative speed limits mode. This changes global transfer throttling.",
    examples=[
        "load_tool(\"qbittorrent.transfer_toggle_speed_limits_mode\")(...)",
    ],
    tool_class="write",
)
def transfer_toggle_speed_limits_mode() -> Any:
    """Toggle alternative speed limits mode. This changes global transfer throttling."""
    client = get_client()
    return client.post("transfer/toggleSpeedLimitsMode", {})

@register_tool(
    namespace="qbittorrent",
    description="Get the global download speed limit in bytes per second.",
    examples=[
        "load_tool(\"qbittorrent.transfer_get_download_limit\")(...)",
    ],
)
def transfer_get_download_limit() -> Any:
    """Get the global download speed limit in bytes per second."""
    client = get_client()
    return client.get("transfer/downloadLimit")

@register_tool(
    namespace="qbittorrent",
    description="Set the global download speed limit in bytes per second. This changes global transfer throttling.",
    examples=[
        "load_tool(\"qbittorrent.transfer_set_download_limit\")(...)",
    ],
    tool_class="write",
)
def transfer_set_download_limit(limit: int) -> Any:
    """Set the global download speed limit in bytes per second. This changes global transfer throttling."""
    client = get_client()
    return client.post("transfer/setDownloadLimit", {"limit": limit})

@register_tool(
    namespace="qbittorrent",
    description="Get the global upload speed limit in bytes per second.",
    examples=[
        "load_tool(\"qbittorrent.transfer_get_upload_limit\")(...)",
    ],
)
def transfer_get_upload_limit() -> Any:
    """Get the global upload speed limit in bytes per second."""
    client = get_client()
    return client.get("transfer/uploadLimit")

@register_tool(
    namespace="qbittorrent",
    description="Set the global upload speed limit in bytes per second. This changes global transfer throttling.",
    examples=[
        "load_tool(\"qbittorrent.transfer_set_upload_limit\")(...)",
    ],
    tool_class="write",
)
def transfer_set_upload_limit(limit: int) -> Any:
    """Set the global upload speed limit in bytes per second. This changes global transfer throttling."""
    client = get_client()
    return client.post("transfer/setUploadLimit", {"limit": limit})

@register_tool(
    namespace="qbittorrent",
    description="Ban one or more peers globally. This blocks the supplied peers from connecting.",
    examples=[
        "load_tool(\"qbittorrent.transfer_ban_peers\")(...)",
    ],
    tool_class="write",
)
def transfer_ban_peers(peers: str) -> Any:
    """Ban one or more peers globally. This blocks the supplied peers from connecting."""
    client = get_client()
    return client.post("transfer/banPeers", {"peers": peers})
