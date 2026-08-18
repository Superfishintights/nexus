"""NZBGet queue and history tools."""

from __future__ import annotations

from typing import Any, Dict, List

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="List current NZBGet queue groups/downloads with summary information.",
    examples=['load_tool("nzbget.listgroups")()'],
    aliases=[],
)
def listgroups(number_of_log_entries: int = 0) -> List[Dict[str, Any]]:
    """RPC signature: struct[] listgroups(int NumberOfLogEntries)."""
    return get_client().call("listgroups", [number_of_log_entries])


@register_tool(
    namespace="nzbget",
    description="List files in queued NZBGet groups, optionally bounded by file IDs or an NZBID.",
    examples=['load_tool("nzbget.listfiles")(0, 0, 123)'],
    aliases=[],
)
def listfiles(id_from: int = 0, id_to: int = 0, nzbid: int = 0) -> List[Dict[str, Any]]:
    """RPC signature: struct[] listfiles(int IDFrom, int IDTo, int NZBID)."""
    return get_client().call("listfiles", [id_from, id_to, nzbid])


@register_tool(
    namespace="nzbget",
    description="List NZBGet history items, optionally including hidden history entries.",
    examples=['load_tool("nzbget.history")()', 'load_tool("nzbget.history")(hidden=True)'],
    aliases=[],
)
def history(hidden: bool = False) -> List[Dict[str, Any]]:
    """RPC signature: struct[] history(bool Hidden)."""
    return get_client().call("history", [hidden])


@register_tool(
    namespace="nzbget",
    description="Add an NZB, archive file, or URL to the NZBGet download queue; this creates a new queue item.",
    examples=[
        'load_tool("nzbget.append")(filename="show.nzb", content="<base64>", category="tv")',
        'load_tool("nzbget.append")(filename="", content="https://example.test/file.nzb")',
    ],
    aliases=[],
)
def append(
    filename: str,
    content: str,
    category: str = "",
    priority: int = 0,
    add_to_top: bool = False,
    add_paused: bool = False,
    dupe_key: str = "",
    dupe_score: int = 0,
    dupe_mode: str = "SCORE",
    auto_category: bool = False,
    pp_parameters: List[Dict[str, Any]] | None = None,
) -> int:
    """RPC signature: int append(string Filename, string Content, string Category, int Priority, bool AddToTop, bool AddPaused, string DupeKey, int DupeScore, string DupeMode, bool AutoCategory, struct[] PPParameters)."""
    return get_client().call(
        "append",
        [
            filename,
            content,
            category,
            priority,
            add_to_top,
            add_paused,
            dupe_key,
            dupe_score,
            dupe_mode,
            auto_category,
            pp_parameters or [],
        ],
    )


@register_tool(
    namespace="nzbget",
    description="Edit NZBGet queue or history items; commands can pause, resume, move, delete, or change metadata for selected IDs.",
    examples=['load_tool("nzbget.editqueue")("GroupPause", "", [123])'],
    aliases=[],
)
def editqueue(command: str, param: str, ids: List[int]) -> bool:
    """RPC signature: bool editqueue(string Command, string Param, int[] IDs)."""
    return get_client().call("editqueue", [command, param, ids])


@register_tool(
    namespace="nzbget",
    description="Request a rescan of NZBGet's incoming NZB directory.",
    examples=['load_tool("nzbget.scan")()', 'load_tool("nzbget.scan")(sync_mode=True)'],
    aliases=[],
)
def scan(sync_mode: bool = False) -> bool:
    """RPC signature: bool scan(bool SyncMode)."""
    return get_client().call("scan", [sync_mode])
