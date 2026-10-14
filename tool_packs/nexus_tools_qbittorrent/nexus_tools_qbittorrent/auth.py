"""qBittorrent authentication tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Log in to qBittorrent WebUI and store the returned SID cookie.",
    examples=[
        "load_tool(\"qbittorrent.auth_login\")(...)",
    ],
    tool_class="write",
)
def auth_login(username: Optional[str] = None, password: Optional[str] = None) -> Any:
    """Log in to qBittorrent WebUI and store the returned SID cookie."""
    client = get_client()
    return client.login(username=username, password=password)

@register_tool(
    namespace="qbittorrent",
    description="Log out of qBittorrent WebUI and clear the stored SID cookie.",
    examples=[
        "load_tool(\"qbittorrent.auth_logout\")(...)",
    ],
    tool_class="write",
)
def auth_logout() -> Any:
    """Log out of qBittorrent WebUI and clear the stored SID cookie."""
    client = get_client()
    return client.logout()
