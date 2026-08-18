"""Vaultwarden folder, collection, and item structure tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


def _require_purpose(purpose: str) -> str:
    cleaned = purpose.strip()
    if not cleaned:
        raise ValueError("purpose is required")
    return cleaned


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Move an exact item ID within the user's authorized personal Vaultwarden vault.",
    examples=[
        'load_tool("vaultwarden.move_item")(item_id, purpose="organize work login", folder_id=folder_id)',
    ],
    tool_class="write",
)
def move_item(
    item_id: str,
    *,
    purpose: str,
    folder_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    collection_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return get_client().move_item(
        item_id,
        purpose=_require_purpose(purpose),
        folder_id=folder_id,
        organization_id=organization_id,
        collection_ids=collection_ids,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Archive an exact item ID in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.archive_item")(item_id, purpose="retire old login")'],
    tool_class="write",
)
def archive_item(item_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().archive_item(item_id, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Restore an exact item ID from archive or trash in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.restore_item")(item_id, purpose="recover needed login")'],
    tool_class="write",
)
def restore_item(item_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().restore_item(item_id, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Move an exact item ID to trash in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.delete_item")(item_id, purpose="remove duplicate login")'],
    tool_class="destructive",
)
def delete_item(item_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().delete_item(item_id, purpose=_require_purpose(purpose), permanent=False)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Permanently delete an exact item ID from the user's authorized personal Vaultwarden vault; this cannot be restored.",
    examples=['load_tool("vaultwarden.permanently_delete_item")(item_id, purpose="purge compromised duplicate")'],
    tool_class="destructive",
)
def permanently_delete_item(item_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().delete_item(item_id, purpose=_require_purpose(purpose), permanent=True)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="List folders in the user's authorized personal Vaultwarden vault with capped results.",
    examples=['load_tool("vaultwarden.list_folders")(search="work")'],
)
def list_folders(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return get_client().list_folders(search=search, limit=limit)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create a folder in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.create_folder")("Work", purpose="organize work credentials")'],
    tool_class="write",
)
def create_folder(name: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().create_folder(name, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Rename an exact folder ID in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.update_folder")(folder_id, "Work", purpose="clarify folder name")'],
    tool_class="write",
)
def update_folder(folder_id: str, name: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().update_folder(folder_id, name, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Delete an exact folder ID in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.delete_folder")(folder_id, purpose="remove empty folder")'],
    tool_class="destructive",
)
def delete_folder(folder_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().delete_folder(folder_id, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="List collections available to the user's authorized personal Vaultwarden account.",
    examples=['load_tool("vaultwarden.list_collections")(organization_id=org_id)'],
)
def list_collections(organization_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    return get_client().list_collections(organization_id=organization_id, limit=limit)


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Assign an exact item ID to collections in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.assign_item_collections")(item_id, [collection_id], purpose="share with team")'],
    tool_class="write",
)
def assign_item_collections(item_id: str, collection_ids: List[str], *, purpose: str) -> Dict[str, Any]:
    return get_client().assign_item_collections(item_id, collection_ids, purpose=_require_purpose(purpose))
