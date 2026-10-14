"""qBittorrent sync tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Get incremental qBittorrent main sync data.",
    examples=[
        "load_tool(\"qbittorrent.sync_get_main_data\")(...)",
    ],
)
def sync_get_main_data(rid: Optional[int] = None) -> Any:
    """Get incremental qBittorrent main sync data."""
    client = get_client()
    return client.get("sync/maindata", params={"rid": rid})

@register_tool(
    namespace="qbittorrent",
    description="Get incremental peer data for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.sync_get_torrent_peers\")(...)",
    ],
)
def sync_get_torrent_peers(hash: str, rid: Optional[int] = None) -> Any:
    """Get incremental peer data for a torrent hash."""
    client = get_client()
    return client.get("sync/torrentPeers", params={"hash": hash, "rid": rid})
