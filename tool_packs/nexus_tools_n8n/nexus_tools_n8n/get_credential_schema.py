"""Get the schema for a credential type in n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Get the schema for a credential type in n8n.",
    examples=["n8n.get_credential_schema(\"n8n-nodes-base.smtp\")"],
)
def get_credential_schema(credential_type_name: str) -> Dict[str, Any]:
    """Get the schema for a credential type in n8n.

    Args:
        credential_type_name: The name of the credential type (e.g. n8n-nodes-base.smtp).

    Returns:
        The schema object.
    """
    client = get_client()
    return client._make_request(f"credentials/schema/{credential_type_name}")
