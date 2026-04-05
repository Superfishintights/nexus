"""n8n tool: delete_tag."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a tag in n8n by ID.",
    examples=['n8n.delete_tag(tag_id="tag_123")'],
)
def delete_tag(tag_id: str) -> Dict[str, Any]:
    """Delete a tag in n8n by ID.

    Args:
        tag_id: The tag ID.

    Returns:
        The delete response object (often empty).
    """
    client = get_client()
    return client._make_request(f"tags/{tag_id}", method="DELETE")
