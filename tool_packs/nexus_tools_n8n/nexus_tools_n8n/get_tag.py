"""n8n tool: get_tag."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve a single tag from n8n by ID.",
    examples=['n8n.get_tag(tag_id="tag_123")'],
)
def get_tag(tag_id: str) -> Dict[str, Any]:
    """Retrieve a single tag from n8n by ID.

    Args:
        tag_id: The tag ID.

    Returns:
        The tag object.
    """
    client = get_client()
    return client._make_request(f"tags/{tag_id}")
