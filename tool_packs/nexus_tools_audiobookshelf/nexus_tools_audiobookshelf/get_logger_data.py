"""Audiobookshelf tool: get_logger_data."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Get Audiobookshelf logger data. Logs may contain operational paths or user activity; "
        "responses are sanitized by the client."
    ),
    examples=["audiobookshelf.get_logger_data()"],
    tool_class="admin",
    aliases=[],
)
def get_logger_data() -> Any:
    """Return sanitized Audiobookshelf server and scanner logger data."""

    return get_client().get("logger-data")
