"""Create a credential in n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Create a credential in n8n.",
    examples=["n8n.create_credential(name=\"My Cred\", type=\"n8n-nodes-base.smtp\", data={\"user\": \"me\", \"password\": \"secret\"})"],
)
def create_credential(
    name: str,
    type: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a credential in n8n.

    Args:
        name: Name of the credential.
        type: Type of credential (e.g., n8n-nodes-base.smtp).
        data: The credential data/values.

    Returns:
        The created credential object.
    """
    client = get_client()
    
    payload = {
        "name": name,
        "type": type,
        "data": data,
    }

    return client._make_request("credentials", method="POST", data=payload)
