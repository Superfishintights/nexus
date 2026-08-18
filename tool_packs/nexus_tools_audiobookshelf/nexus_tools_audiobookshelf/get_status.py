"""Audiobookshelf tool: get_status."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Get the current status of Audiobookshelf.",
    examples=[
        "load_tool(\"audiobookshelf.get_status\")()",
    ],
    tool_class="read",
    aliases=[],
)
def get_status() -> Any:
    """GET /status without authentication."""
    return get_client().get("status", api_path="", authenticated=False)
