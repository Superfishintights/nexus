"""NZBGet configuration tools."""

from __future__ import annotations

from typing import Any, Dict, List

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Read the currently loaded NZBGet configuration from memory.",
    examples=['load_tool("nzbget.config")()'],
    aliases=[],
)
def config() -> List[Dict[str, Any]]:
    """RPC signature: struct[] config()."""
    return get_client().call("config")


@register_tool(
    namespace="nzbget",
    description="Read NZBGet configuration from disk without changing settings.",
    examples=['load_tool("nzbget.loadconfig")()'],
    aliases=[],
)
def loadconfig() -> List[Dict[str, Any]]:
    """RPC signature: struct[] loadconfig()."""
    return get_client().call("loadconfig")


@register_tool(
    namespace="nzbget",
    description="Save NZBGet configuration options to disk; this changes persisted server settings.",
    examples=['load_tool("nzbget.saveconfig")([{"Name": "ControlPort", "Value": "6789"}])'],
    aliases=[],
)
def saveconfig(options: List[Dict[str, Any]]) -> bool:
    """RPC signature: bool saveconfig(struct[] Options)."""
    return get_client().call("saveconfig", [options])


@register_tool(
    namespace="nzbget",
    description="Get NZBGet configuration templates and extension configuration sections.",
    examples=['load_tool("nzbget.configtemplates")()', 'load_tool("nzbget.configtemplates")(load_from_disk=True)'],
    aliases=[],
)
def configtemplates(load_from_disk: bool = False) -> List[Dict[str, Any]]:
    """RPC signature: struct[] configtemplates(bool LoadFromDisk)."""
    return get_client().call("configtemplates", [load_from_disk])
