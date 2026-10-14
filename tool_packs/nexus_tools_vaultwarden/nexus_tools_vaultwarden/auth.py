"""Vaultwarden authentication and session tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Get redacted status for the user's authorized personal Vaultwarden CLI session.",
    examples=[
        'load_tool("vaultwarden.status")()',
    ],
    tool_class="read",
)
def status(*, use_session: bool = False) -> Dict[str, Any]:
    """Return CLI/vault status without exposing session material."""
    return get_client().status(use_session=use_session)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Sync the user's authorized personal Vaultwarden vault through the configured Bitwarden CLI session.",
    examples=[
        'load_tool("vaultwarden.sync")(purpose="refresh before reading login metadata")',
    ],
    tool_class="write",
)
def sync(*, purpose: str = "explicit sync") -> Dict[str, Any]:
    return get_client().sync(purpose=purpose)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Lock the configured authorized personal Vaultwarden CLI session.",
    examples=[
        'load_tool("vaultwarden.lock")(purpose="finished reading requested credential")',
    ],
    tool_class="write",
)
def lock(*, purpose: str = "explicit lock") -> Dict[str, Any]:
    return get_client().lock(purpose=purpose)
