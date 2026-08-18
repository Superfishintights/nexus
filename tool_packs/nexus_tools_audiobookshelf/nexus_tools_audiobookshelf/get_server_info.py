"""Audiobookshelf tool: get_server_info."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Get the authorized Audiobookshelf user, server version, and server settings.",
    examples=["audiobookshelf.get_server_info()"],
    tool_class="admin",
    aliases=[],
)
def get_server_info() -> Any:
    """Return authorized-user context with the connected server's version and settings."""

    return get_client().post("authorize")
