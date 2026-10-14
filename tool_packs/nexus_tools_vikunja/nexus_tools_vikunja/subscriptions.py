"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="Subscribe to an entity. Subscribes the authenticated user to a project or task so they receive its notifications. The user needs read access to the entity. Fails if the user is already subscribed, directly or through a parent project. Subscribing again after an opt-out lifts it.",
    examples=['load_tool("vikunja.subscribe")(entity="task", entity_id=1)'],
    tool_class='write',
    aliases=[],
)
def subscribe(entity: str, entity_id: int, params: dict[str, Any] | None = None) -> Any:
    'POST /api/v2/subscriptions/{entity}/{entityID}. Subscribes the authenticated user to a project or task so they receive its notifications. The user needs read access to the entity. Fails if the user is already subscribed, directly or through a parent project. Subscribing again after an opt-out lifts it.'
    client = get_client()
    return safe_response(safe_request(client, 'POST', f'subscriptions/{subscription_entity(entity)}/{positive_id(entity_id)}', params=params))


@register_tool(
    namespace="vikunja",
    description="Unsubscribe from an entity. Stops notifications about a project or task for the authenticated user. If the subscription was inherited from a parent project, the opt-out is recorded for this entity instead, leaving the parent subscription in place. Only affects the caller's subscription, not other users'.",
    examples=['load_tool("vikunja.unsubscribe")(entity="task", entity_id=1)'],
    tool_class='destructive',
    aliases=[],
)
def unsubscribe(entity: str, entity_id: int, params: dict[str, Any] | None = None) -> Any:
    "DELETE /api/v2/subscriptions/{entity}/{entityID}. Stops notifications about a project or task for the authenticated user. If the subscription was inherited from a parent project, the opt-out is recorded for this entity instead, leaving the parent subscription in place. Only affects the caller's subscription, not other users'."
    client = get_client()
    return safe_response(safe_request(client, 'DELETE', f'subscriptions/{subscription_entity(entity)}/{positive_id(entity_id)}', params=params))

