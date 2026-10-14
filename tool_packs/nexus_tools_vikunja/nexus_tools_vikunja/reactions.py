"""Ordinary Vikunja API v2 operations from the checked live specification."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='List reactions for an entity.', examples=['load_tool("vikunja.list_reactions")(\'tasks\', 1)'], tool_class='read', aliases=[])
def list_reactions(entity_kind: str, entity_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns every reaction on the entity, grouped as a map keyed by reaction value; each value maps to the users who reacted with it. Requires read access to the entity. Not paginated.'
    if entity_kind not in {'tasks', 'comments'}:
        raise ValueError('entity_kind must be tasks or comments')
    return get_client().request('GET', f'{path_text(entity_kind)}/{positive_id(entity_id)}/reactions', params=params)


@register_tool(namespace="vikunja", description='React to an entity.', examples=['load_tool("vikunja.add_reaction")(\'tasks\', 1, \'acknowledged\')'], tool_class='write', aliases=[])
def add_reaction(entity_kind: str, entity_id: int, value: str, params: dict[str, Any] | None = None) -> Any:
    "Adds the authenticated user's reaction to the entity. Requires write access. No-op if the same reaction already exists."
    if entity_kind not in {'tasks', 'comments'}:
        raise ValueError('entity_kind must be tasks or comments')
    if not isinstance(value, str) or not value or len(value) > 20:
        raise ValueError('value must contain 1 to 20 characters')
    return get_client().request('POST', f'{path_text(entity_kind)}/{positive_id(entity_id)}/reactions', params=params, body={'value': value})


@register_tool(namespace="vikunja", description='Remove a reaction from an entity.', examples=['load_tool("vikunja.remove_reaction")(\'tasks\', 1, \'acknowledged\')'], tool_class='write', aliases=[])
def remove_reaction(entity_kind: str, entity_id: int, value: str, params: dict[str, Any] | None = None) -> Any:
    "Removes the authenticated user's own reaction from the entity. The reaction to remove is named in the body (there is no per-reaction id), so this is a POST with a body rather than a DELETE. Requires write access."
    if entity_kind not in {'tasks', 'comments'}:
        raise ValueError('entity_kind must be tasks or comments')
    if not isinstance(value, str) or not value or len(value) > 20:
        raise ValueError('value must contain 1 to 20 characters')
    return get_client().request('POST', f'{path_text(entity_kind)}/{positive_id(entity_id)}/reactions/delete', params=params, body={'value': value})
