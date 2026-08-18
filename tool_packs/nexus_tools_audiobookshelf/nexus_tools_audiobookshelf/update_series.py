"""Update Audiobookshelf series metadata."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Update an Audiobookshelf series. Audiobookshelf v2.36 accepts name and description.",
    examples=[
        'audiobookshelf.update_series("series-123", {"name": "The Sandman", "description": "A dark fantasy series."})',
    ],
    tool_class="write",
    aliases=[],
)
def update_series(series_id: str, updates: Dict[str, Any]) -> Any:
    """PATCH /api/series/{series_id} with supported series metadata updates."""
    if not isinstance(updates, dict) or not updates:
        raise ValueError("updates must be a non-empty dictionary")

    client = get_client()
    encoded = client.segment(series_id, name="series_id")
    return client.patch(f"series/{encoded}", body=updates)
