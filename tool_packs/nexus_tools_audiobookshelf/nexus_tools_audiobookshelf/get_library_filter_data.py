"""Retrieve maintenance filter data for an Audiobookshelf library."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Retrieve a library's filter data for issue review and missing metadata maintenance inputs."
    ),
    examples=["audiobookshelf.get_library_filter_data(library_id='library-abc123')"],
    tool_class="read",
    aliases=[],
)
def get_library_filter_data(library_id: str) -> Any:
    """Return filter data used to maintain issues and missing metadata in a library."""

    client = get_client()
    return client.get(f"libraries/{client.segment(library_id, name='library_id')}/filterdata")
