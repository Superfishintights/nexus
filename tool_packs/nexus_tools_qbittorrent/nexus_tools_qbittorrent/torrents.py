"""qBittorrent torrent management tools."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from nexus.tool_registry import register_tool

from .client import get_client

Params = Optional[Dict[str, Any]]

@register_tool(
    namespace="qbittorrent",
    description="Get torrent list.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_list\")(...)",
    ],
)
def torrent_get_list(filter: Optional[str] = None, category: Optional[str] = None, tag: Optional[str] = None, sort: Optional[str] = None, reverse: Optional[bool] = None, limit: Optional[int] = None, offset: Optional[int] = None, hashes: Optional[str] = None) -> Any:
    """Get torrent list."""
    client = get_client()
    return client.get("torrents/info", params={"filter": filter, "category": category, "tag": tag, "sort": sort, "reverse": reverse, "limit": limit, "offset": offset, "hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Get generic properties for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_properties\")(...)",
    ],
)
def torrent_get_properties(hash: str) -> Any:
    """Get generic properties for a torrent hash."""
    client = get_client()
    return client.get("torrents/properties", params={"hash": hash})

@register_tool(
    namespace="qbittorrent",
    description="Get trackers for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_trackers\")(...)",
    ],
)
def torrent_get_trackers(hash: str) -> Any:
    """Get trackers for a torrent hash."""
    client = get_client()
    return client.get("torrents/trackers", params={"hash": hash})

@register_tool(
    namespace="qbittorrent",
    description="Get web seeds for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_webseeds\")(...)",
    ],
)
def torrent_get_webseeds(hash: str) -> Any:
    """Get web seeds for a torrent hash."""
    client = get_client()
    return client.get("torrents/webseeds", params={"hash": hash})

@register_tool(
    namespace="qbittorrent",
    description="Get file contents for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_files\")(...)",
    ],
)
def torrent_get_files(hash: str, indexes: Optional[str] = None) -> Any:
    """Get file contents for a torrent hash."""
    client = get_client()
    return client.get("torrents/files", params={"hash": hash, "indexes": indexes})

@register_tool(
    namespace="qbittorrent",
    description="Get piece states for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_piece_states\")(...)",
    ],
)
def torrent_get_piece_states(hash: str) -> Any:
    """Get piece states for a torrent hash."""
    client = get_client()
    return client.get("torrents/pieceStates", params={"hash": hash})

@register_tool(
    namespace="qbittorrent",
    description="Get piece hashes for a torrent hash.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_piece_hashes\")(...)",
    ],
)
def torrent_get_piece_hashes(hash: str) -> Any:
    """Get piece hashes for a torrent hash."""
    client = get_client()
    return client.get("torrents/pieceHashes", params={"hash": hash})

@register_tool(
    namespace="qbittorrent",
    description="Pause torrents by hash list or all. This stops selected torrent transfers.",
    examples=[
        "load_tool(\"qbittorrent.torrent_stop\")(...)",
    ],
    tool_class="write",
)
def torrent_stop(hashes: str) -> Any:
    """Pause torrents by hash list or all. This stops selected torrent transfers."""
    client = get_client()
    return client.post("torrents/stop", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Resume torrents by hash list or all. This starts selected torrent transfers.",
    examples=[
        "load_tool(\"qbittorrent.torrent_start\")(...)",
    ],
    tool_class="write",
)
def torrent_start(hashes: str) -> Any:
    """Resume torrents by hash list or all. This starts selected torrent transfers."""
    client = get_client()
    return client.post("torrents/start", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Delete torrents by hash list or all. If delete_files is true, downloaded data is also deleted.",
    examples=[
        "load_tool(\"qbittorrent.torrent_delete\")(...)",
    ],
    tool_class="write",
)
def torrent_delete(hashes: str, delete_files: bool = False) -> Any:
    """Delete torrents by hash list or all. If delete_files is true, downloaded data is also deleted."""
    client = get_client()
    return client.post("torrents/delete", {"hashes": hashes, "deleteFiles": delete_files})

@register_tool(
    namespace="qbittorrent",
    description="Recheck torrents by hash list or all. This can cause disk and tracker activity.",
    examples=[
        "load_tool(\"qbittorrent.torrent_recheck\")(...)",
    ],
    tool_class="write",
)
def torrent_recheck(hashes: str) -> Any:
    """Recheck torrents by hash list or all. This can cause disk and tracker activity."""
    client = get_client()
    return client.post("torrents/recheck", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Reannounce torrents by hash list or all. This contacts trackers for selected torrents.",
    examples=[
        "load_tool(\"qbittorrent.torrent_reannounce\")(...)",
    ],
    tool_class="write",
)
def torrent_reannounce(hashes: str) -> Any:
    """Reannounce torrents by hash list or all. This contacts trackers for selected torrents."""
    client = get_client()
    return client.post("torrents/reannounce", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Add new torrents from URLs or local .torrent files. This creates torrent jobs in qBittorrent.",
    examples=[
        "load_tool(\"qbittorrent.torrent_add\")(...)",
    ],
    tool_class="write",
)
def torrent_add(urls: Optional[str] = None, torrent_paths: Optional[Sequence[str]] = None, savepath: Optional[str] = None, category: Optional[str] = None, tags: Optional[str] = None, skip_checking: Optional[bool] = None, paused: Optional[bool] = None, root_folder: Optional[bool] = None, rename: Optional[str] = None, upLimit: Optional[int] = None, dlLimit: Optional[int] = None, ratioLimit: Optional[float] = None, seedingTimeLimit: Optional[int] = None, autoTMM: Optional[bool] = None, sequentialDownload: Optional[bool] = None, firstLastPiecePrio: Optional[bool] = None) -> Any:
    """Add new torrents from URLs or local .torrent files. This creates torrent jobs in qBittorrent."""
    client = get_client()
    fields = {"urls": urls, "savepath": savepath, "category": category, "tags": tags, "skip_checking": skip_checking, "paused": paused, "root_folder": root_folder, "rename": rename, "upLimit": upLimit, "dlLimit": dlLimit, "ratioLimit": ratioLimit, "seedingTimeLimit": seedingTimeLimit, "autoTMM": autoTMM, "sequentialDownload": sequentialDownload, "firstLastPiecePrio": firstLastPiecePrio}
    return client.post_multipart("torrents/add", fields=fields, files=torrent_paths or ())

@register_tool(
    namespace="qbittorrent",
    description="Add trackers to a torrent. This modifies the selected torrent tracker list.",
    examples=[
        "load_tool(\"qbittorrent.torrent_add_trackers\")(...)",
    ],
    tool_class="write",
)
def torrent_add_trackers(hash: str, urls: str) -> Any:
    """Add trackers to a torrent. This modifies the selected torrent tracker list."""
    client = get_client()
    return client.post("torrents/addTrackers", {"hash": hash, "urls": urls})

@register_tool(
    namespace="qbittorrent",
    description="Edit a tracker URL on a torrent. This modifies the selected torrent tracker list.",
    examples=[
        "load_tool(\"qbittorrent.torrent_edit_tracker\")(...)",
    ],
    tool_class="write",
)
def torrent_edit_tracker(hash: str, origUrl: str, newUrl: str) -> Any:
    """Edit a tracker URL on a torrent. This modifies the selected torrent tracker list."""
    client = get_client()
    return client.post("torrents/editTracker", {"hash": hash, "origUrl": origUrl, "newUrl": newUrl})

@register_tool(
    namespace="qbittorrent",
    description="Remove tracker URLs from a torrent. This modifies the selected torrent tracker list.",
    examples=[
        "load_tool(\"qbittorrent.torrent_remove_trackers\")(...)",
    ],
    tool_class="write",
)
def torrent_remove_trackers(hash: str, urls: str) -> Any:
    """Remove tracker URLs from a torrent. This modifies the selected torrent tracker list."""
    client = get_client()
    return client.post("torrents/removeTrackers", {"hash": hash, "urls": urls})

@register_tool(
    namespace="qbittorrent",
    description="Add peers to torrents. This changes peer connection targets for selected torrents.",
    examples=[
        "load_tool(\"qbittorrent.torrent_add_peers\")(...)",
    ],
    tool_class="write",
)
def torrent_add_peers(hashes: str, peers: str) -> Any:
    """Add peers to torrents. This changes peer connection targets for selected torrents."""
    client = get_client()
    return client.post("torrents/addPeers", {"hashes": hashes, "peers": peers})

@register_tool(
    namespace="qbittorrent",
    description="Increase queue priority for torrents. This changes torrent queue ordering.",
    examples=[
        "load_tool(\"qbittorrent.torrent_increase_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_increase_priority(hashes: str) -> Any:
    """Increase queue priority for torrents. This changes torrent queue ordering."""
    client = get_client()
    return client.post("torrents/increasePrio", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Decrease queue priority for torrents. This changes torrent queue ordering.",
    examples=[
        "load_tool(\"qbittorrent.torrent_decrease_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_decrease_priority(hashes: str) -> Any:
    """Decrease queue priority for torrents. This changes torrent queue ordering."""
    client = get_client()
    return client.post("torrents/decreasePrio", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set torrents to maximum queue priority. This changes torrent queue ordering.",
    examples=[
        "load_tool(\"qbittorrent.torrent_top_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_top_priority(hashes: str) -> Any:
    """Set torrents to maximum queue priority. This changes torrent queue ordering."""
    client = get_client()
    return client.post("torrents/topPrio", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set torrents to minimum queue priority. This changes torrent queue ordering.",
    examples=[
        "load_tool(\"qbittorrent.torrent_bottom_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_bottom_priority(hashes: str) -> Any:
    """Set torrents to minimum queue priority. This changes torrent queue ordering."""
    client = get_client()
    return client.post("torrents/bottomPrio", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set file priority within a torrent. This changes which files download.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_file_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_set_file_priority(hash: str, id: str, priority: int) -> Any:
    """Set file priority within a torrent. This changes which files download."""
    client = get_client()
    return client.post("torrents/filePrio", {"hash": hash, "id": id, "priority": priority})

@register_tool(
    namespace="qbittorrent",
    description="Get per-torrent download limits for hashes.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_download_limit\")(...)",
    ],
)
def torrent_get_download_limit(hashes: str) -> Any:
    """Get per-torrent download limits for hashes."""
    client = get_client()
    return client.post("torrents/downloadLimit", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set per-torrent download limit in bytes per second. This changes transfer throttling.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_download_limit\")(...)",
    ],
    tool_class="write",
)
def torrent_set_download_limit(hashes: str, limit: int) -> Any:
    """Set per-torrent download limit in bytes per second. This changes transfer throttling."""
    client = get_client()
    return client.post("torrents/setDownloadLimit", {"hashes": hashes, "limit": limit})

@register_tool(
    namespace="qbittorrent",
    description="Set torrent share limits. This changes seeding ratio and time limits.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_share_limits\")(...)",
    ],
    tool_class="write",
)
def torrent_set_share_limits(hashes: str, ratioLimit: float, seedingTimeLimit: int, inactiveSeedingTimeLimit: int) -> Any:
    """Set torrent share limits. This changes seeding ratio and time limits."""
    client = get_client()
    return client.post("torrents/setShareLimits", {"hashes": hashes, "ratioLimit": ratioLimit, "seedingTimeLimit": seedingTimeLimit, "inactiveSeedingTimeLimit": inactiveSeedingTimeLimit})

@register_tool(
    namespace="qbittorrent",
    description="Get per-torrent upload limits for hashes.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_upload_limit\")(...)",
    ],
)
def torrent_get_upload_limit(hashes: str) -> Any:
    """Get per-torrent upload limits for hashes."""
    client = get_client()
    return client.post("torrents/uploadLimit", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set per-torrent upload limit in bytes per second. This changes transfer throttling.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_upload_limit\")(...)",
    ],
    tool_class="write",
)
def torrent_set_upload_limit(hashes: str, limit: int) -> Any:
    """Set per-torrent upload limit in bytes per second. This changes transfer throttling."""
    client = get_client()
    return client.post("torrents/setUploadLimit", {"hashes": hashes, "limit": limit})

@register_tool(
    namespace="qbittorrent",
    description="Set torrent download location. This can move or redirect downloaded data.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_location\")(...)",
    ],
    tool_class="write",
)
def torrent_set_location(hashes: str, location: str) -> Any:
    """Set torrent download location. This can move or redirect downloaded data."""
    client = get_client()
    return client.post("torrents/setLocation", {"hashes": hashes, "location": location})

@register_tool(
    namespace="qbittorrent",
    description="Rename a torrent. This changes the torrent display name.",
    examples=[
        "load_tool(\"qbittorrent.torrent_rename\")(...)",
    ],
    tool_class="write",
)
def torrent_rename(hash: str, name: str) -> Any:
    """Rename a torrent. This changes the torrent display name."""
    client = get_client()
    return client.post("torrents/rename", {"hash": hash, "name": name})

@register_tool(
    namespace="qbittorrent",
    description="Set category for torrents. This can trigger automatic torrent management moves.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_category\")(...)",
    ],
    tool_class="write",
)
def torrent_set_category(hashes: str, category: str) -> Any:
    """Set category for torrents. This can trigger automatic torrent management moves."""
    client = get_client()
    return client.post("torrents/setCategory", {"hashes": hashes, "category": category})

@register_tool(
    namespace="qbittorrent",
    description="Get all torrent categories.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_categories\")(...)",
    ],
)
def torrent_get_categories() -> Any:
    """Get all torrent categories."""
    client = get_client()
    return client.get("torrents/categories")

@register_tool(
    namespace="qbittorrent",
    description="Create a torrent category. This changes qBittorrent category configuration.",
    examples=[
        "load_tool(\"qbittorrent.torrent_create_category\")(...)",
    ],
    tool_class="write",
)
def torrent_create_category(category: str, savePath: Optional[str] = None) -> Any:
    """Create a torrent category. This changes qBittorrent category configuration."""
    client = get_client()
    return client.post("torrents/createCategory", {"category": category, "savePath": savePath})

@register_tool(
    namespace="qbittorrent",
    description="Edit a torrent category save path. This changes qBittorrent category configuration.",
    examples=[
        "load_tool(\"qbittorrent.torrent_edit_category\")(...)",
    ],
    tool_class="write",
)
def torrent_edit_category(category: str, savePath: str) -> Any:
    """Edit a torrent category save path. This changes qBittorrent category configuration."""
    client = get_client()
    return client.post("torrents/editCategory", {"category": category, "savePath": savePath})

@register_tool(
    namespace="qbittorrent",
    description="Remove torrent categories. This changes qBittorrent category configuration.",
    examples=[
        "load_tool(\"qbittorrent.torrent_remove_categories\")(...)",
    ],
    tool_class="write",
)
def torrent_remove_categories(categories: str) -> Any:
    """Remove torrent categories. This changes qBittorrent category configuration."""
    client = get_client()
    return client.post("torrents/removeCategories", {"categories": categories})

@register_tool(
    namespace="qbittorrent",
    description="Add tags to torrents. This changes torrent metadata.",
    examples=[
        "load_tool(\"qbittorrent.torrent_add_tags\")(...)",
    ],
    tool_class="write",
)
def torrent_add_tags(hashes: str, tags: str) -> Any:
    """Add tags to torrents. This changes torrent metadata."""
    client = get_client()
    return client.post("torrents/addTags", {"hashes": hashes, "tags": tags})

@register_tool(
    namespace="qbittorrent",
    description="Remove tags from torrents. Empty tags removes all tags from selected torrents.",
    examples=[
        "load_tool(\"qbittorrent.torrent_remove_tags\")(...)",
    ],
    tool_class="write",
)
def torrent_remove_tags(hashes: str, tags: str = "") -> Any:
    """Remove tags from torrents. Empty tags removes all tags from selected torrents."""
    client = get_client()
    return client.post("torrents/removeTags", {"hashes": hashes, "tags": tags})

@register_tool(
    namespace="qbittorrent",
    description="Get all torrent tags.",
    examples=[
        "load_tool(\"qbittorrent.torrent_get_tags\")(...)",
    ],
)
def torrent_get_tags() -> Any:
    """Get all torrent tags."""
    client = get_client()
    return client.get("torrents/tags")

@register_tool(
    namespace="qbittorrent",
    description="Create torrent tags. This changes qBittorrent tag configuration.",
    examples=[
        "load_tool(\"qbittorrent.torrent_create_tags\")(...)",
    ],
    tool_class="write",
)
def torrent_create_tags(tags: str) -> Any:
    """Create torrent tags. This changes qBittorrent tag configuration."""
    client = get_client()
    return client.post("torrents/createTags", {"tags": tags})

@register_tool(
    namespace="qbittorrent",
    description="Delete torrent tags. This removes tags from qBittorrent tag configuration.",
    examples=[
        "load_tool(\"qbittorrent.torrent_delete_tags\")(...)",
    ],
    tool_class="write",
)
def torrent_delete_tags(tags: str) -> Any:
    """Delete torrent tags. This removes tags from qBittorrent tag configuration."""
    client = get_client()
    return client.post("torrents/deleteTags", {"tags": tags})

@register_tool(
    namespace="qbittorrent",
    description="Set automatic torrent management for torrents. This can affect torrent relocation behavior.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_auto_management\")(...)",
    ],
    tool_class="write",
)
def torrent_set_auto_management(hashes: str, enable: bool) -> Any:
    """Set automatic torrent management for torrents. This can affect torrent relocation behavior."""
    client = get_client()
    return client.post("torrents/setAutoManagement", {"hashes": hashes, "enable": enable})

@register_tool(
    namespace="qbittorrent",
    description="Toggle sequential download for torrents. This changes selected torrent download behavior.",
    examples=[
        "load_tool(\"qbittorrent.torrent_toggle_sequential_download\")(...)",
    ],
    tool_class="write",
)
def torrent_toggle_sequential_download(hashes: str) -> Any:
    """Toggle sequential download for torrents. This changes selected torrent download behavior."""
    client = get_client()
    return client.post("torrents/toggleSequentialDownload", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Toggle first/last piece priority for torrents. This changes selected torrent download behavior.",
    examples=[
        "load_tool(\"qbittorrent.torrent_toggle_first_last_piece_priority\")(...)",
    ],
    tool_class="write",
)
def torrent_toggle_first_last_piece_priority(hashes: str) -> Any:
    """Toggle first/last piece priority for torrents. This changes selected torrent download behavior."""
    client = get_client()
    return client.post("torrents/toggleFirstLastPiecePrio", {"hashes": hashes})

@register_tool(
    namespace="qbittorrent",
    description="Set force start for torrents. This changes whether queue limits are bypassed.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_force_start\")(...)",
    ],
    tool_class="write",
)
def torrent_set_force_start(hashes: str, value: bool) -> Any:
    """Set force start for torrents. This changes whether queue limits are bypassed."""
    client = get_client()
    return client.post("torrents/setForceStart", {"hashes": hashes, "value": value})

@register_tool(
    namespace="qbittorrent",
    description="Set super seeding for torrents. This changes selected torrent seeding behavior.",
    examples=[
        "load_tool(\"qbittorrent.torrent_set_super_seeding\")(...)",
    ],
    tool_class="write",
)
def torrent_set_super_seeding(hashes: str, value: bool) -> Any:
    """Set super seeding for torrents. This changes selected torrent seeding behavior."""
    client = get_client()
    return client.post("torrents/setSuperSeeding", {"hashes": hashes, "value": value})

@register_tool(
    namespace="qbittorrent",
    description="Rename a file inside a torrent. This changes the selected file path.",
    examples=[
        "load_tool(\"qbittorrent.torrent_rename_file\")(...)",
    ],
    tool_class="write",
)
def torrent_rename_file(hash: str, oldPath: str, newPath: str) -> Any:
    """Rename a file inside a torrent. This changes the selected file path."""
    client = get_client()
    return client.post("torrents/renameFile", {"hash": hash, "oldPath": oldPath, "newPath": newPath})

@register_tool(
    namespace="qbittorrent",
    description="Rename a folder inside a torrent. This changes selected content paths.",
    examples=[
        "load_tool(\"qbittorrent.torrent_rename_folder\")(...)",
    ],
    tool_class="write",
)
def torrent_rename_folder(hash: str, oldPath: str, newPath: str) -> Any:
    """Rename a folder inside a torrent. This changes selected content paths."""
    client = get_client()
    return client.post("torrents/renameFolder", {"hash": hash, "oldPath": oldPath, "newPath": newPath})
