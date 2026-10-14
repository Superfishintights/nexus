"""Delete an Audiobookshelf media progress record."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Permanently delete one exact Audiobookshelf media progress record by ID.",
    examples=['audiobookshelf.delete_media_progress("progress-123")'],
    tool_class="destructive",
    aliases=[],
)
def delete_media_progress(progress_id: str) -> Any:
    """DELETE /api/me/progress/{progress_id} to permanently remove one progress record."""
    if not progress_id or not progress_id.strip():
        raise ValueError("progress_id must be non-empty")

    client = get_client()
    encoded = client.segment(progress_id, name="progress_id")
    return client.delete(f"me/progress/{encoded}")
