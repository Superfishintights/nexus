"""Ordinary Vikunja API v2 operations from the checked live specification."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='Create a saved filter.', examples=['load_tool("vikunja.create_saved_filter")(\'Open tasks\')'], tool_class='write', aliases=[])
def create_saved_filter(title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a saved filter; the authenticated user becomes its owner. The filter query is validated before it is stored.'
    return get_client().request('POST', 'filters', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Delete a saved filter.', examples=['load_tool("vikunja.delete_saved_filter")(1)'], tool_class='destructive', aliases=[])
def delete_saved_filter(filter_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a saved filter. Only the owner may delete it.'
    return get_client().request('DELETE', f'filters/{positive_id(filter_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a saved filter.', examples=['load_tool("vikunja.get_saved_filter")(1)'], tool_class='read', aliases=[])
def get_saved_filter(filter_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single saved filter. Only the owner may see it. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'filters/{positive_id(filter_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a saved filter. Full replacement, omitted fields may reset.', examples=['load_tool("vikunja.replace_saved_filter")(1, {})'], tool_class='write', aliases=[])
def replace_saved_filter(filter_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Replaces all of a saved filter's fields — only the owner may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'filters/{positive_id(filter_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description="Partially update a saved filter without replacing unmentioned fields.", examples=['load_tool("vikunja.update_saved_filter")(1, {"title": "Daily work"})'], tool_class="write", aliases=[])
def update_saved_filter(filter_id: int, fields: dict[str, Any]) -> Any:
    return get_client().request("PATCH", f"filters/{positive_id(filter_id)}", body=fields)
