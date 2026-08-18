"""Find read-only duplicate candidates in an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Find read-only duplicate-item candidates in an Audiobookshelf library; "
        "does not automatically delete any items."
    ),
    examples=[
        'audiobookshelf.find_duplicate_items("library-123")',
        'audiobookshelf.find_duplicate_items("library-123", keys=("asin", "isbn"))',
    ],
    tool_class="read",
    aliases=[],
)
def find_duplicate_items(
    library_id: str,
    keys: Sequence[str] = ("path", "asin", "isbn", "title_author"),
    max_items: int = 10000,
    page_size: int = 500,
) -> Dict[str, Any]:
    """Return candidate duplicate groups without modifying the library."""
    return get_client().find_duplicate_items(
        library_id,
        keys=keys,
        max_items=max_items,
        page_size=page_size,
    )
