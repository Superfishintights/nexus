"""n8n tool: create_tag."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Create a tag in n8n.",
    examples=['n8n.create_tag(name="Important")'],
)
def create_tag(name: str) -> Dict[str, Any]:
    """Create a tag in n8n.

    Args:
        name: The tag name.

    Returns:
        The created tag object.
    """
    client = get_client()
    payload = {"name": name}
    return client._make_request("tags", method="POST", data=payload)
