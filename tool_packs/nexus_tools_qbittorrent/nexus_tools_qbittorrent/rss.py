"""qBittorrent RSS tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Add an RSS folder. This changes RSS configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_add_folder\")(...)",
    ],
    tool_class="write",
)
def rss_add_folder(path: str) -> Any:
    """Add an RSS folder. This changes RSS configuration."""
    client = get_client()
    return client.post("rss/addFolder", {"path": path})

@register_tool(
    namespace="qbittorrent",
    description="Add an RSS feed. This changes RSS configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_add_feed\")(...)",
    ],
    tool_class="write",
)
def rss_add_feed(url: str, path: Optional[str] = None) -> Any:
    """Add an RSS feed. This changes RSS configuration."""
    client = get_client()
    return client.post("rss/addFeed", {"url": url, "path": path})

@register_tool(
    namespace="qbittorrent",
    description="Remove an RSS folder or feed. This deletes RSS configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_remove_item\")(...)",
    ],
    tool_class="write",
)
def rss_remove_item(path: str) -> Any:
    """Remove an RSS folder or feed. This deletes RSS configuration."""
    client = get_client()
    return client.post("rss/removeItem", {"path": path})

@register_tool(
    namespace="qbittorrent",
    description="Move or rename an RSS folder or feed. This changes RSS configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_move_item\")(...)",
    ],
    tool_class="write",
)
def rss_move_item(itemPath: str, destPath: str) -> Any:
    """Move or rename an RSS folder or feed. This changes RSS configuration."""
    client = get_client()
    return client.post("rss/moveItem", {"itemPath": itemPath, "destPath": destPath})

@register_tool(
    namespace="qbittorrent",
    description="Get all RSS items, optionally including feed article data.",
    examples=[
        "load_tool(\"qbittorrent.rss_get_items\")(...)",
    ],
)
def rss_get_items(withData: Optional[bool] = None) -> Any:
    """Get all RSS items, optionally including feed article data."""
    client = get_client()
    return client.get("rss/items", params={"withData": withData})

@register_tool(
    namespace="qbittorrent",
    description="Mark an RSS feed or article as read. This changes RSS read state.",
    examples=[
        "load_tool(\"qbittorrent.rss_mark_as_read\")(...)",
    ],
    tool_class="write",
)
def rss_mark_as_read(itemPath: str, articleId: Optional[str] = None) -> Any:
    """Mark an RSS feed or article as read. This changes RSS read state."""
    client = get_client()
    return client.post("rss/markAsRead", {"itemPath": itemPath, "articleId": articleId})

@register_tool(
    namespace="qbittorrent",
    description="Refresh an RSS folder or feed. This triggers RSS network activity.",
    examples=[
        "load_tool(\"qbittorrent.rss_refresh_item\")(...)",
    ],
    tool_class="write",
)
def rss_refresh_item(itemPath: str) -> Any:
    """Refresh an RSS folder or feed. This triggers RSS network activity."""
    client = get_client()
    return client.post("rss/refreshItem", {"itemPath": itemPath})

@register_tool(
    namespace="qbittorrent",
    description="Set an RSS auto-downloading rule. This changes RSS automation and can affect future torrent additions.",
    examples=[
        "load_tool(\"qbittorrent.rss_set_rule\")(...)",
    ],
    tool_class="write",
)
def rss_set_rule(ruleName: str, ruleDef: Union[str, Dict[str, Any]]) -> Any:
    """Set an RSS auto-downloading rule. This changes RSS automation and can affect future torrent additions."""
    client = get_client()
    return client.post("rss/setRule", {"ruleName": ruleName, "ruleDef": ruleDef})

@register_tool(
    namespace="qbittorrent",
    description="Rename an RSS auto-downloading rule. This changes RSS automation configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_rename_rule\")(...)",
    ],
    tool_class="write",
)
def rss_rename_rule(ruleName: str, newRuleName: str) -> Any:
    """Rename an RSS auto-downloading rule. This changes RSS automation configuration."""
    client = get_client()
    return client.post("rss/renameRule", {"ruleName": ruleName, "newRuleName": newRuleName})

@register_tool(
    namespace="qbittorrent",
    description="Remove an RSS auto-downloading rule. This deletes RSS automation configuration.",
    examples=[
        "load_tool(\"qbittorrent.rss_remove_rule\")(...)",
    ],
    tool_class="write",
)
def rss_remove_rule(ruleName: str) -> Any:
    """Remove an RSS auto-downloading rule. This deletes RSS automation configuration."""
    client = get_client()
    return client.post("rss/removeRule", {"ruleName": ruleName})

@register_tool(
    namespace="qbittorrent",
    description="Get all RSS auto-downloading rules.",
    examples=[
        "load_tool(\"qbittorrent.rss_get_rules\")(...)",
    ],
)
def rss_get_rules() -> Any:
    """Get all RSS auto-downloading rules."""
    client = get_client()
    return client.get("rss/rules")

@register_tool(
    namespace="qbittorrent",
    description="Get all RSS articles matching an auto-downloading rule.",
    examples=[
        "load_tool(\"qbittorrent.rss_get_matching_articles\")(...)",
    ],
)
def rss_get_matching_articles(ruleName: str) -> Any:
    """Get all RSS articles matching an auto-downloading rule."""
    client = get_client()
    return client.get("rss/matchingArticles", params={"ruleName": ruleName})
