"""Retrieve aggregate statistics for an Audiobookshelf library."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve aggregate size and health statistics for an Audiobookshelf library.",
    examples=['audiobookshelf.get_library_stats("library-123")'],
    tool_class="read",
    aliases=[],
)
def get_library_stats(library_id: str) -> Any:
    """Return aggregate statistics for the library identified by ``library_id``."""

    client = get_client()
    return client.get(f"libraries/{client.segment(library_id, name='library_id')}/stats")
