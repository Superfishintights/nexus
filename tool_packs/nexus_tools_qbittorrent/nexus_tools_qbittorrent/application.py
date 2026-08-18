"""qBittorrent application tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Get the qBittorrent application version.",
    examples=[
        "load_tool(\"qbittorrent.app_get_version\")(...)",
    ],
)
def app_get_version() -> Any:
    """Get the qBittorrent application version."""
    client = get_client()
    return client.get("app/version")

@register_tool(
    namespace="qbittorrent",
    description="Get the qBittorrent WebAPI version.",
    examples=[
        "load_tool(\"qbittorrent.app_get_webapi_version\")(...)",
    ],
)
def app_get_webapi_version() -> Any:
    """Get the qBittorrent WebAPI version."""
    client = get_client()
    return client.get("app/webapiVersion")

@register_tool(
    namespace="qbittorrent",
    description="Get qBittorrent build dependency and bitness information.",
    examples=[
        "load_tool(\"qbittorrent.app_get_build_info\")(...)",
    ],
)
def app_get_build_info() -> Any:
    """Get qBittorrent build dependency and bitness information."""
    client = get_client()
    return client.get("app/buildInfo")

@register_tool(
    namespace="qbittorrent",
    description="Shut down the qBittorrent application. This stops the running server process.",
    examples=[
        "load_tool(\"qbittorrent.app_shutdown\")(...)",
    ],
    tool_class="write",
)
def app_shutdown() -> Any:
    """Shut down the qBittorrent application. This stops the running server process."""
    client = get_client()
    return client.post("app/shutdown", {})

@register_tool(
    namespace="qbittorrent",
    description="Get qBittorrent application preferences.",
    examples=[
        "load_tool(\"qbittorrent.app_get_preferences\")(...)",
    ],
)
def app_get_preferences() -> Any:
    """Get qBittorrent application preferences."""
    client = get_client()
    return client.get("app/preferences")

@register_tool(
    namespace="qbittorrent",
    description="Set qBittorrent application preferences. This changes server configuration values.",
    examples=[
        "load_tool(\"qbittorrent.app_set_preferences\")({\"queueing_enabled\": False})",
    ],
    tool_class="write",
)
def app_set_preferences(preferences: Dict[str, Any]) -> Any:
    """Set qBittorrent application preferences. This changes server configuration values."""
    client = get_client()
    return client.post_json_field("app/setPreferences", "json", preferences)

@register_tool(
    namespace="qbittorrent",
    description="Get the default torrent save path.",
    examples=[
        "load_tool(\"qbittorrent.app_get_default_save_path\")(...)",
    ],
)
def app_get_default_save_path() -> Any:
    """Get the default torrent save path."""
    client = get_client()
    return client.get("app/defaultSavePath")

@register_tool(
    namespace="qbittorrent",
    description="Get cookies used by qBittorrent when downloading torrent files.",
    examples=[
        "load_tool(\"qbittorrent.app_get_cookies\")(...)",
    ],
)
def app_get_cookies() -> Any:
    """Get cookies used by qBittorrent when downloading torrent files."""
    client = get_client()
    return client.get("app/cookies")

@register_tool(
    namespace="qbittorrent",
    description="Set cookies used by qBittorrent when downloading torrent files. This replaces saved cookie data.",
    examples=[
        "load_tool(\"qbittorrent.app_set_cookies\")([{\"name\": \"Example\", \"value\": \"foo=bar\"}])",
    ],
    tool_class="write",
)
def app_set_cookies(cookies: Sequence[Dict[str, Any]]) -> Any:
    """Set cookies used by qBittorrent when downloading torrent files. This replaces saved cookie data."""
    client = get_client()
    return client.post_json_field("app/setCookies", "json", list(cookies))
