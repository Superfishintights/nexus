"""Vikunja API v2 tools. See the pack README and versioned official spec."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body, token_output_path, save_created_token, VikunjaError


@register_tool(namespace="vikunja", description='Instance info.', examples=['load_tool("vikunja.get_info")()'], tool_class='read', aliases=[])
def get_info(params: dict[str, Any] | None = None) -> Any:
    'Returns version, frontend URL, motd and the enabled features of this Vikunja instance. Public — no authentication required.'
    return get_client().request('GET', 'info', params=params, authenticated=False)


@register_tool(namespace="vikunja", description='List API token routes.', examples=['load_tool("vikunja.get_routes")()'], tool_class='read', aliases=[])
def get_routes(params: dict[str, Any] | None = None) -> Any:
    'Returns every API route available to scope an API token against, grouped by resource and permission. Covers both /api/v1 and /api/v2 routes.'
    return get_client().request('GET', 'routes', params=params)


@register_tool(namespace="vikunja", description='List api tokens.', examples=['load_tool("vikunja.list_tokens")()'], tool_class='read', aliases=[])
def list_tokens(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    "Returns the api tokens owned by the authenticated user. Pass owner_id to list a bot's tokens instead — only bots owned by the caller are allowed."
    return get_client().page('tokens', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create an API token and save its secret to a new private file; return metadata only.', examples=['load_tool("vikunja.create_token")({"title": "Planner", "permissions": {"tasks": ["read_all"]}}, "planner.token")'], tool_class='write', aliases=[])
def create_token(fields: dict[str, Any], output_name: str, params: dict[str, Any] | None = None) -> Any:
    'Creates an api token for the authenticated user, or for a bot they own when owner_id is set. The cleartext token is returned once in this response and is never readable again.'
    destination = token_output_path(output_name)
    client = get_client()
    created = client.request('POST', 'tokens', params=params, body=fields)
    token = created.pop('token', None)
    if not token:
        raise VikunjaError('Token creation response had no token; check token metadata and revoke it if necessary')
    try:
        save_created_token(destination, token)
    except OSError:
        revoked = False
        try:
            client.request('DELETE', f"tokens/{positive_id(created['id'])}")
            revoked = True
        except (VikunjaError, ValueError, KeyError):
            pass
        raise VikunjaError(f"Could not save new token ID {created.get('id')}; automatic revocation succeeded={revoked}") from None
    return {**created, 'token_file': str(destination), 'token_saved': True}


@register_tool(namespace="vikunja", description='Delete an api token.', examples=['load_tool("vikunja.delete_token")(1)'], tool_class='destructive', aliases=[])
def delete_token(token_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes an api token. The caller may delete their own tokens and tokens belonging to bots they own.'
    return get_client().request('DELETE', f'tokens/{positive_id(token_id)}', params=params)


@register_tool(namespace="vikunja", description='Get the current user.', examples=['load_tool("vikunja.get_current_user")()'], tool_class='read', aliases=[])
def get_current_user(params: dict[str, Any] | None = None) -> Any:
    'Returns the authenticated user together with their settings and computed account facts (auth_provider, is_local_user, is_admin, deletion_scheduled_at).'
    return get_client().request('GET', 'user', params=params)


@register_tool(namespace="vikunja", description='List bot users.', examples=['load_tool("vikunja.list_bots")()'], tool_class='read', aliases=[])
def list_bots(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns only the bot users owned by the authenticated user. Bots owned by anyone else are never listed.'
    return get_client().page('user/bots', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a bot user.', examples=['load_tool("vikunja.create_bot")({})'], tool_class='write', aliases=[])
def create_bot(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Creates a bot user owned by the authenticated user. The username must start with the 'bot-' prefix. Bots have no email or password and cannot create further bots. Requires a real user account — link shares cannot create bots."
    return get_client().request('POST', 'user/bots', params=params, body=fields)


@register_tool(namespace="vikunja", description='Delete a bot user.', examples=['load_tool("vikunja.delete_bot")(1)'], tool_class='destructive', aliases=[])
def delete_bot(bot_id: int, params: dict[str, Any] | None = None) -> Any:
    'Permanently deletes an owned bot user and all data associated with it. Only the owner may delete it.'
    return get_client().request('DELETE', f'user/bots/{positive_id(bot_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a bot user.', examples=['load_tool("vikunja.get_bot")(1)'], tool_class='read', aliases=[])
def get_bot(bot_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single bot user. Only the owner may read it; otherwise the request is refused. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'user/bots/{positive_id(bot_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a bot user. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_bot")(1, {})'], tool_class='write', aliases=[])
def replace_bot(bot_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces an owned bot user's name, status, and username; status is required. Only the owner may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'user/bots/{positive_id(bot_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='Search users.', examples=['load_tool("vikunja.search_users")()'], tool_class='read', aliases=[])
def search_users(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Searches users by username, name or full email. Matching by name or email requires the target user to have made themselves discoverable, unless both users share an external (OIDC/LDAP) team. Email addresses are never returned.'
    return get_client().page('users', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})
