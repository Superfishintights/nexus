"""Ordinary Vikunja API v2 operations from the checked live specification."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description="List a project's webhooks.", examples=['load_tool("vikunja.list_project_webhooks")(1)'], tool_class='read', aliases=[])
def list_project_webhooks(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the webhook targets configured for the given project, paginated. Requires read access to the project. Secret and basic-auth credentials are never included.'
    return _without_credentials(get_client().page(f'projects/{positive_id(project_id)}/webhooks', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})}))


@register_tool(namespace="vikunja", description='Create a webhook target in a project.', examples=['load_tool("vikunja.create_project_webhook")(1, {})'], tool_class='write', aliases=[])
def create_project_webhook(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Creates a webhook target that receives POST requests about the subscribed events of the given project. The parent project is taken from the URL, not the body. Requires write access to the project. The secret and basic-auth credentials are write-only and not returned in the response.'
    return _without_credentials(get_client().request('POST', f'projects/{positive_id(project_id)}/webhooks', params=params, body=fields))


@register_tool(namespace="vikunja", description='Delete a webhook target.', examples=['load_tool("vikunja.delete_project_webhook")(1, 1)'], tool_class='destructive', aliases=[])
def delete_project_webhook(project_id: int, webhook_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a webhook target. The webhook must belong to the project in the path, and write access to that project is required.'
    return _without_credentials(get_client().request('DELETE', f'projects/{positive_id(project_id)}/webhooks/{positive_id(webhook_id)}', params=params))


@register_tool(namespace="vikunja", description="Update a webhook target's events.", examples=['load_tool("vikunja.update_project_webhook")(1, 1, {})'], tool_class='write', aliases=[])
def update_project_webhook(project_id: int, webhook_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Changes the events a webhook target subscribes to. Only the events list can be changed; target_url, secret and auth are immutable after creation. The webhook must belong to the project in the path, and write access to that project is required.'
    return _without_credentials(get_client().request('PUT', f'projects/{positive_id(project_id)}/webhooks/{positive_id(webhook_id)}', params=params, body=fields))


@register_tool(namespace="vikunja", description="List the current user's webhooks.", examples=['load_tool("vikunja.list_user_webhooks")()'], tool_class='read', aliases=[])
def list_user_webhooks(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the webhook targets the authenticated user has configured for themselves (not project webhooks), paginated. Secret and basic-auth credentials are never included.'
    return _without_credentials(get_client().page('user/settings/webhooks', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})}))


@register_tool(namespace="vikunja", description='Create a webhook for the current user.', examples=['load_tool("vikunja.create_user_webhook")({})'], tool_class='write', aliases=[])
def create_user_webhook(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Creates a webhook target owned by the authenticated user that receives POST requests across all of their projects. The owning user is taken from the token, not the body. May only subscribe to user-directed events (see the events route). The secret and basic-auth credentials are write-only and not returned in the response.'
    return _without_credentials(get_client().request('POST', 'user/settings/webhooks', params=params, body=fields))


@register_tool(namespace="vikunja", description='List available user-directed webhook events.', examples=['load_tool("vikunja.get_user_webhook_events")()'], tool_class='read', aliases=[])
def get_user_webhook_events(params: dict[str, Any] | None = None) -> Any:
    'Returns the webhook event names a user-level webhook may subscribe to. This is a subset of the project webhook events — only events that target a single user.'
    return _without_credentials(get_client().request('GET', 'user/settings/webhooks/events', params=params))


@register_tool(namespace="vikunja", description='Delete a user webhook.', examples=['load_tool("vikunja.delete_user_webhook")(1)'], tool_class='destructive', aliases=[])
def delete_user_webhook(webhook_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a webhook owned by the authenticated user. Only the owning user may delete it.'
    return _without_credentials(get_client().request('DELETE', f'user/settings/webhooks/{positive_id(webhook_id)}', params=params))


@register_tool(namespace="vikunja", description="Update a user webhook's events.", examples=['load_tool("vikunja.update_user_webhook")(1, {})'], tool_class='write', aliases=[])
def update_user_webhook(webhook_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Changes the events a user webhook subscribes to. Only the events list can be changed; target_url, secret and auth are immutable after creation. Only the owning user may update it.'
    return _without_credentials(get_client().request('PUT', f'user/settings/webhooks/{positive_id(webhook_id)}', params=params, body=fields))


@register_tool(namespace="vikunja", description='List available webhook events.', examples=['load_tool("vikunja.get_webhook_events")()'], tool_class='read', aliases=[])
def get_webhook_events(params: dict[str, Any] | None = None) -> Any:
    'Returns every event a webhook target can subscribe to. Use these values when creating or updating a webhook.'
    return _without_credentials(get_client().request('GET', 'webhooks/events', params=params))


def _without_credentials(value: Any) -> Any:
    """Keep configured request fields intact while omitting write-only response credentials."""
    if isinstance(value, dict):
        return {key: _without_credentials(item) for key, item in value.items()
                if key not in {"secret", "basic_auth_user", "basic_auth_password", "password", "token"}}
    if isinstance(value, list):
        return [_without_credentials(item) for item in value]
    return value
