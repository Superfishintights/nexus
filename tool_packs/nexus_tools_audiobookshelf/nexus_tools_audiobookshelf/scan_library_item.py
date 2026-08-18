"""Scan one file-based Audiobookshelf library item."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Rescan one file-based Audiobookshelf library item. This endpoint only supports "
        "file items; use scan_library for folder-based library scans."
    ),
    examples=[
        'audiobookshelf.scan_library_item("item-123")',
    ],
    tool_class="admin",
    aliases=[],
)
def scan_library_item(item_id: str) -> Any:
    """POST /api/items/{item_id}/scan for one file-based library item."""
    client = get_client()
    encoded = client.segment(item_id, name="item_id")
    return client.post(f"items/{encoded}/scan")
