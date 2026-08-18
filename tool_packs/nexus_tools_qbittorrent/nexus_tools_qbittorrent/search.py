"""qBittorrent search tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Start a torrent search job. This triggers search plugin network activity.",
    examples=[
        "load_tool(\"qbittorrent.search_start\")(...)",
    ],
    tool_class="write",
)
def search_start(pattern: str, plugins: str, category: str) -> Any:
    """Start a torrent search job. This triggers search plugin network activity."""
    client = get_client()
    return client.post("search/start", {"pattern": pattern, "plugins": plugins, "category": category})

@register_tool(
    namespace="qbittorrent",
    description="Stop a torrent search job. This cancels search work.",
    examples=[
        "load_tool(\"qbittorrent.search_stop\")(...)",
    ],
    tool_class="write",
)
def search_stop(id: int) -> Any:
    """Stop a torrent search job. This cancels search work."""
    client = get_client()
    return client.post("search/stop", {"id": id})

@register_tool(
    namespace="qbittorrent",
    description="Get status for one search job or all search jobs.",
    examples=[
        "load_tool(\"qbittorrent.search_get_status\")(...)",
    ],
)
def search_get_status(id: Optional[int] = None) -> Any:
    """Get status for one search job or all search jobs."""
    client = get_client()
    return client.get("search/status", params={"id": id})

@register_tool(
    namespace="qbittorrent",
    description="Get torrent search results for a search job.",
    examples=[
        "load_tool(\"qbittorrent.search_get_results\")(...)",
    ],
)
def search_get_results(id: int, limit: Optional[int] = None, offset: Optional[int] = None) -> Any:
    """Get torrent search results for a search job."""
    client = get_client()
    return client.get("search/results", params={"id": id, "limit": limit, "offset": offset})

@register_tool(
    namespace="qbittorrent",
    description="Delete a torrent search job. This removes qBittorrent search job state.",
    examples=[
        "load_tool(\"qbittorrent.search_delete\")(...)",
    ],
    tool_class="write",
)
def search_delete(id: int) -> Any:
    """Delete a torrent search job. This removes qBittorrent search job state."""
    client = get_client()
    return client.post("search/delete", {"id": id})

@register_tool(
    namespace="qbittorrent",
    description="Get installed search plugins.",
    examples=[
        "load_tool(\"qbittorrent.search_get_plugins\")(...)",
    ],
)
def search_get_plugins() -> Any:
    """Get installed search plugins."""
    client = get_client()
    return client.get("search/plugins")

@register_tool(
    namespace="qbittorrent",
    description="Install search plugins from URLs or paths. This changes executable search plugin configuration.",
    examples=[
        "load_tool(\"qbittorrent.search_install_plugin\")(...)",
    ],
    tool_class="write",
)
def search_install_plugin(sources: str) -> Any:
    """Install search plugins from URLs or paths. This changes executable search plugin configuration."""
    client = get_client()
    return client.post("search/installPlugin", {"sources": sources})

@register_tool(
    namespace="qbittorrent",
    description="Uninstall search plugins. This removes search plugin configuration.",
    examples=[
        "load_tool(\"qbittorrent.search_uninstall_plugin\")(...)",
    ],
    tool_class="write",
)
def search_uninstall_plugin(names: str) -> Any:
    """Uninstall search plugins. This removes search plugin configuration."""
    client = get_client()
    return client.post("search/uninstallPlugin", {"names": names})

@register_tool(
    namespace="qbittorrent",
    description="Enable or disable search plugins. This changes search plugin configuration.",
    examples=[
        "load_tool(\"qbittorrent.search_enable_plugin\")(...)",
    ],
    tool_class="write",
)
def search_enable_plugin(names: str, enable: bool) -> Any:
    """Enable or disable search plugins. This changes search plugin configuration."""
    client = get_client()
    return client.post("search/enablePlugin", {"names": names, "enable": enable})

@register_tool(
    namespace="qbittorrent",
    description="Update installed search plugins. This triggers plugin update network activity.",
    examples=[
        "load_tool(\"qbittorrent.search_update_plugins\")(...)",
    ],
    tool_class="write",
)
def search_update_plugins() -> Any:
    """Update installed search plugins. This triggers plugin update network activity."""
    client = get_client()
    return client.post("search/updatePlugins", {})
