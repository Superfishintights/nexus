"""Vikunja API v2 tools. See the pack README and versioned official spec."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='List labels.', examples=['load_tool("vikunja.list_labels")()'], tool_class='read', aliases=[])
def list_labels(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the labels visible to the authenticated user — their own plus any used on tasks they can access. Not a global list.'
    return get_client().page('labels', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a label.', examples=['load_tool("vikunja.create_label")(\'Nexus integration test\')'], tool_class='write', aliases=[])
def create_label(title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a label; the authenticated user becomes its owner.'
    return get_client().request('POST', 'labels', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Delete a label.', examples=['load_tool("vikunja.delete_label")(1)'], tool_class='destructive', aliases=[])
def delete_label(label_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a label. Only the owner may delete it.'
    return get_client().request('DELETE', f'labels/{positive_id(label_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a label.', examples=['load_tool("vikunja.get_label")(1)'], tool_class='read', aliases=[])
def get_label(label_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single label. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'labels/{positive_id(label_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a label. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_label")(1, {})'], tool_class='write', aliases=[])
def replace_label(label_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces all of a label's fields — only the owner may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'labels/{positive_id(label_id)}', params=params, body=fields)
