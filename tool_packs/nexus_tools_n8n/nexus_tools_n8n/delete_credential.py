"""Delete a credential from n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Delete a credential from n8n.",
    examples=["n8n.delete_credential(\"123\")"],
)
def delete_credential(credential_id: str) -> Dict[str, Any]:
    """Delete a credential from n8n.

    Args:
        credential_id: The ID of the credential to delete.

    Returns:
        The deleted credential object (or success message).
    """
    client = get_client()
    return client._make_request(f"credentials/{credential_id}", method="DELETE")
