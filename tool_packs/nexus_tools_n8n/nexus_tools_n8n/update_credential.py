"""n8n tool: update_credential."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update an existing credential in n8n.",
    examples=[
        'n8n.update_credential(credential_id="cred_123", name="Renamed Credential")',
        'n8n.update_credential(credential_id="cred_123", credential_type="n8n-nodes-base.smtp", is_global=True)',
    ],
)
def update_credential(
    credential_id: str,
    *,
    name: Optional[str] = None,
    credential_type: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    is_global: Optional[bool] = None,
    is_resolvable: Optional[bool] = None,
    is_partial_data: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update an existing credential in n8n.

    Args:
        credential_id: The credential ID to update.
        name: Optional new credential name.
        credential_type: Optional new credential type.
        data: Optional credential data payload.
        is_global: Optional global visibility flag.
        is_resolvable: Optional resolvable flag.
        is_partial_data: Optional partial data flag.

    Returns:
        The updated credential object.
    """
    client = get_client()

    payload: Dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if credential_type is not None:
        payload["type"] = credential_type
    if data is not None:
        payload["data"] = data
    if is_global is not None:
        payload["isGlobal"] = is_global
    if is_resolvable is not None:
        payload["isResolvable"] = is_resolvable
    if is_partial_data is not None:
        payload["isPartialData"] = is_partial_data

    return client._make_request(f"credentials/{credential_id}", method="PATCH", data=payload)
