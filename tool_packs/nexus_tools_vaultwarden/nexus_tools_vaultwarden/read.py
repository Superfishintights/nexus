"""Vaultwarden read tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Find items in the user's authorized personal Vaultwarden vault, returning redacted metadata.",
    examples=[
        'load_tool("vaultwarden.find_items")(search="github")',
        'load_tool("vaultwarden.find_items")(url="https://example.com", item_types=["login"], limit=5)',
    ],
    tool_class="read",
)
def find_items(
    *,
    search: Optional[str] = None,
    url: Optional[str] = None,
    folder_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    include_trash: bool = False,
    include_archived: bool = False,
    item_types: Optional[List[str]] = None,
    limit: int = 10,
    allow_all: bool = False,
) -> Dict[str, Any]:
    return get_client().find_items(
        search=search,
        url=url,
        folder_id=folder_id,
        collection_id=collection_id,
        organization_id=organization_id,
        include_trash=include_trash,
        include_archived=include_archived,
        item_types=item_types,
        limit=limit,
        allow_all=allow_all,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Get redacted metadata for one item in the user's authorized personal Vaultwarden vault.",
    examples=[
        'load_tool("vaultwarden.get_item")("github")',
        'load_tool("vaultwarden.get_item")("github", include_secret_fields=True, field_selectors=["username"], purpose="confirm login username")',
    ],
    tool_class="read",
)
def get_item(
    selector: str,
    *,
    include_secret_fields: bool = False,
    field_selectors: Optional[List[str]] = None,
    purpose: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().get_item(
        selector,
        include_secret_fields=include_secret_fields,
        field_selectors=field_selectors,
        purpose=purpose,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Get one selected secret field from the user's authorized personal Vaultwarden vault for a stated purpose.",
    examples=[
        'load_tool("vaultwarden.get_secret")("github", field="password", purpose="authenticate to GitHub CLI")',
        'load_tool("vaultwarden.get_secret")("bank", field="custom:member id", purpose="fill requested member id field")',
    ],
    tool_class="read",
)
def get_secret(selector: str, *, field: str, purpose: str) -> Dict[str, Any]:
    if not purpose:
        raise ValueError("purpose is required")
    return get_client().get_secret(selector, field=field, purpose=purpose)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Get the current TOTP code from the user's authorized personal Vaultwarden vault for a stated purpose.",
    examples=[
        'load_tool("vaultwarden.get_totp")("github", purpose="complete requested MFA prompt")',
    ],
    tool_class="read",
)
def get_totp(selector: str, *, purpose: str) -> Dict[str, Any]:
    if not purpose:
        raise ValueError("purpose is required")
    return get_client().get_totp(selector, purpose=purpose)
