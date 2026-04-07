"""n8n tool: transfer_credential."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Transfer a credential to another project in n8n.",
    examples=['n8n.transfer_credential(credential_id="cred_123", destination_project_id="proj_456")'],
)
def transfer_credential(credential_id: str, destination_project_id: str) -> Dict[str, Any]:
    """Transfer a credential to another project in n8n.

    Args:
        credential_id: The credential ID to transfer.
        destination_project_id: The destination project ID.

    Returns:
        Dictionary containing the transfer result.
    """
    client = get_client()
    payload = {"destinationProjectId": destination_project_id}
    return client._make_request(f"credentials/{credential_id}/transfer", method="PUT", data=payload)
