"""NZBGet extension-management tools."""

from __future__ import annotations

from typing import Any, Dict, List

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Read NZBGet extension metadata from disk.",
    examples=['load_tool("nzbget.loadextensions")()', 'load_tool("nzbget.loadextensions")(load_from_disk=True)'],
    aliases=[],
)
def loadextensions(load_from_disk: bool = False) -> List[Dict[str, Any]]:
    """RPC signature: struct[] loadextensions(bool LoadFromDisk)."""
    return get_client().call("loadextensions", [load_from_disk])


@register_tool(
    namespace="nzbget",
    description="Download and install an NZBGet extension from a URL; this changes installed extension files.",
    examples=['load_tool("nzbget.downloadextension")("https://example.test/script.py", "Script.py")'],
    aliases=[],
)
def downloadextension(url: str, ext_name: str) -> bool:
    """RPC signature: bool downloadextension(string URL, string ExtName)."""
    return get_client().call("downloadextension", [url, ext_name])


@register_tool(
    namespace="nzbget",
    description="Update an installed NZBGet extension from a URL; this changes installed extension files.",
    examples=['load_tool("nzbget.updateextension")("https://example.test/script.py", "Script.py")'],
    aliases=[],
)
def updateextension(url: str, ext_name: str) -> bool:
    """RPC signature: bool updateextension(string URL, string ExtName)."""
    return get_client().call("updateextension", [url, ext_name])


@register_tool(
    namespace="nzbget",
    description="Delete an installed NZBGet extension; this removes extension files.",
    examples=['load_tool("nzbget.deleteextension")("Script.py")'],
    aliases=[],
)
def deleteextension(ext_name: str) -> bool:
    """RPC signature: bool deleteextension(string ExtName)."""
    return get_client().call("deleteextension", [ext_name])
