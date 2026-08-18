"""Vaultwarden attachment tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .structure import _require_purpose


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="List attachment metadata for an exact item in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.list_attachments")(item_id, purpose="inspect saved files")'],
)
def list_attachments(item_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().list_attachments(item_id, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Download an attachment from an exact item in the user's authorized personal Vaultwarden vault.",
    examples=[
        'load_tool("vaultwarden.download_attachment")(item_id, attachment_id, output_path="/tmp/file.pdf", purpose="retrieve invoice")',
    ],
)
def download_attachment(
    item_id: str,
    attachment_id: str,
    *,
    purpose: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().download_attachment(
        item_id,
        attachment_id,
        output_path=output_path,
        purpose=_require_purpose(purpose),
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Upload a local file as an attachment to an exact item in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.upload_attachment")(item_id, "/tmp/file.pdf", purpose="attach recovery PDF")'],
    tool_class="write",
)
def upload_attachment(item_id: str, file_path: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().upload_attachment(item_id, file_path, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Delete an attachment from an exact item in the user's authorized personal Vaultwarden vault.",
    examples=['load_tool("vaultwarden.delete_attachment")(item_id, attachment_id, purpose="remove stale file")'],
    tool_class="destructive",
)
def delete_attachment(item_id: str, attachment_id: str, *, purpose: str) -> Dict[str, Any]:
    return get_client().delete_attachment(item_id, attachment_id, purpose=_require_purpose(purpose))
