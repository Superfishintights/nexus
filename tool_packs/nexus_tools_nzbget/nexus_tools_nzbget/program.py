"""NZBGet program-control tools."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Get the NZBGet program version string.",
    examples=['load_tool("nzbget.version")()'],
    aliases=[],
)
def version() -> str:
    """RPC signature: string version()."""
    return get_client().call("version")


@register_tool(
    namespace="nzbget",
    description="Reload NZBGet after changed program options; this stops current activities and reinitializes the program.",
    examples=['load_tool("nzbget.shutdown")()'],
    aliases=[],
)
def shutdown() -> bool:
    """RPC signature: bool shutdown()."""
    return get_client().call("shutdown")


@register_tool(
    namespace="nzbget",
    description="Shut down the NZBGet program; this is a destructive service-control action.",
    examples=['load_tool("nzbget.reload")()'],
    aliases=[],
)
def reload() -> bool:
    """RPC signature: bool reload()."""
    return get_client().call("reload")


@register_tool(
    namespace="nzbget",
    description="Call a raw NZBGet JSON-RPC method with positional params; use only for newly added server methods not wrapped by this pack.",
    examples=['load_tool("nzbget.call")("status")', 'load_tool("nzbget.call")("log", [0, 100])'],
    aliases=[],
)
def call(method: str, params: list[Any] | None = None) -> Any:
    """Call any NZBGet JSON-RPC method using positional parameters."""
    return get_client().call(method, params=params)
