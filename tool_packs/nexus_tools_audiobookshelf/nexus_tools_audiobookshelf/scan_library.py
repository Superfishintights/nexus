"""Scan an Audiobookshelf library for newly available media."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Start an operational scan of an Audiobookshelf library for new or changed media.",
    examples=['audiobookshelf.scan_library("library-123")'],
    tool_class="admin",
    aliases=[],
)
def scan_library(library_id: str) -> Any:
    """Start a scan for the specified Audiobookshelf library."""
    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.post(f"libraries/{encoded}/scan")
