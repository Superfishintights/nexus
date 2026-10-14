"""NZBGet status, logging, and statistics tools."""

from __future__ import annotations

from typing import Any, Dict, List

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Get current NZBGet status and summary information.",
    examples=['load_tool("nzbget.status")()'],
    aliases=[],
)
def status() -> Dict[str, Any]:
    """RPC signature: struct status()."""
    return get_client().call("status")


@register_tool(
    namespace="nzbget",
    description="Get NZBGet environment and hardware information.",
    examples=['load_tool("nzbget.sysinfo")()'],
    aliases=[],
)
def sysinfo() -> Dict[str, Any]:
    """RPC signature: struct sysinfo()."""
    return get_client().call("sysinfo")


@register_tool(
    namespace="nzbget",
    description="Run NZBGet system-health diagnostics for the active configuration.",
    examples=['load_tool("nzbget.systemhealth")()'],
    aliases=[],
)
def systemhealth() -> Dict[str, Any]:
    """RPC signature: struct systemhealth()."""
    return get_client().call("systemhealth")


@register_tool(
    namespace="nzbget",
    description="Read entries from NZBGet's in-memory screen log buffer.",
    examples=['load_tool("nzbget.log")(0, 100)'],
    aliases=[],
)
def log(id_from: int = 0, number_of_entries: int = 100) -> List[Dict[str, Any]]:
    """RPC signature: struct[] log(int IDFrom, int NumberOfEntries)."""
    return get_client().call("log", [id_from, number_of_entries])


@register_tool(
    namespace="nzbget",
    description="Append an entry to NZBGet's server log file and screen log buffer.",
    examples=['load_tool("nzbget.writelog")("INFO", "Message from Nexus")'],
    aliases=[],
)
def writelog(kind: str, text: str) -> bool:
    """RPC signature: bool writelog(string Kind, string Text)."""
    return get_client().call("writelog", [kind, text])


@register_tool(
    namespace="nzbget",
    description="Load the on-disk log for a specific NZBGet NZBID.",
    examples=['load_tool("nzbget.loadlog")(123, 0, 100)'],
    aliases=[],
)
def loadlog(nzbid: int, id_from: int = 0, number_of_entries: int = 100) -> List[Dict[str, Any]]:
    """RPC signature: struct[] loadlog(int NZBID, int IDFrom, int NumberOfEntries)."""
    return get_client().call("loadlog", [nzbid, id_from, number_of_entries])


@register_tool(
    namespace="nzbget",
    description="Load the on-disk log for a specific NZBGet extension script.",
    examples=['load_tool("nzbget.logscript")(0, 100)'],
    aliases=[],
)
def logscript(id_from: int = 0, entries: int = 100) -> List[Dict[str, Any]]:
    """RPC signature: struct[] logscript(int idfrom, int entries)."""
    return get_client().call("logscript", [id_from, entries])


@register_tool(
    namespace="nzbget",
    description="Load the NZBGet update log from disk.",
    examples=['load_tool("nzbget.logupdate")(0, 100)'],
    aliases=[],
)
def logupdate(id_from: int = 0, entries: int = 100) -> List[Dict[str, Any]]:
    """RPC signature: struct[] logupdate(int idfrom, int entries)."""
    return get_client().call("logupdate", [id_from, entries])


@register_tool(
    namespace="nzbget",
    description="Get NZBGet download volume statistics per news server.",
    examples=['load_tool("nzbget.servervolumes")()'],
    aliases=[],
)
def servervolumes() -> List[Dict[str, Any]]:
    """RPC signature: struct[] servervolumes()."""
    return get_client().call("servervolumes")


@register_tool(
    namespace="nzbget",
    description="Reset NZBGet download volume statistics for one news server counter; this clears selected usage counters.",
    examples=['load_tool("nzbget.resetservervolume")(1, "total")'],
    aliases=[],
)
def resetservervolume(server_id: int, counter: str) -> bool:
    """RPC signature: bool resetservervolume(int ServerId, string Counter)."""
    return get_client().call("resetservervolume", [server_id, counter])
