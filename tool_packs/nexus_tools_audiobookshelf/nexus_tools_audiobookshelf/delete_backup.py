"""Delete an Audiobookshelf server backup."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Permanently and irreversibly delete one exact Audiobookshelf server backup by ID."
    ),
    examples=['audiobookshelf.delete_backup("backup-123")'],
    tool_class="destructive",
    aliases=[],
)
def delete_backup(backup_id: str) -> Any:
    """DELETE /api/backups/{backup_id} for one exact server backup."""
    client = get_client()
    encoded = client.segment(backup_id, name="backup_id")
    return client.delete(f"backups/{encoded}")
