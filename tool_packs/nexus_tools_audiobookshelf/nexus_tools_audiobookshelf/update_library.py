"""Update an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Update an Audiobookshelf library. If folders is provided, it is a full "
        "replacement array and omitted folders are removed."
    ),
    examples=[
        'audiobookshelf.update_library("library-123", {"name": "Audiobooks"})',
    ],
    tool_class="admin",
    aliases=[],
)
def update_library(library_id: str, updates: Dict[str, Any]) -> Any:
    """Validate and PATCH the supplied library updates unchanged."""
    if not isinstance(updates, dict) or not updates:
        raise ValueError("updates must be a non-empty dictionary")

    if "folders" in updates:
        folders = updates["folders"]
        if not isinstance(folders, list):
            raise ValueError("folders must be a list")
        for folder in folders:
            if not isinstance(folder, dict):
                raise ValueError("each folder must be a dictionary")
            full_path = folder.get("fullPath")
            if not isinstance(full_path, str) or not full_path.strip():
                raise ValueError("each folder must include a non-blank fullPath")

    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.patch(f"libraries/{encoded}", body=updates)
