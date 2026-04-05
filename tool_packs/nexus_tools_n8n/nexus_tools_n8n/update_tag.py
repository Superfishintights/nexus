"""n8n tool: update_tag."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update a tag name in n8n by ID.",
    examples=['n8n.update_tag(tag_id="tag_123", name="Renamed")'],
)
def update_tag(tag_id: str, name: str) -> Dict[str, Any]:
    """Update a tag name in n8n by ID.

    Args:
        tag_id: The tag ID.
        name: The new tag name.

    Returns:
        The updated tag object.
    """
    client = get_client()
    payload = {"name": name}
    return client._make_request(f"tags/{tag_id}", method="PUT", data=payload)
