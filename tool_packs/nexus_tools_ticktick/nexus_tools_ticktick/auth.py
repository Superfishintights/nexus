"""Safe configuration and live authorization checks. Token setup is local only."""
from __future__ import annotations

from typing import Any
from nexus.config import get_setting
from nexus.tool_registry import register_tool
from .client import TickTickError, get_client, read_token, token_file


@register_tool(aliases=[], namespace='ticktick', description='Check TickTick credential configuration without returning credentials.', examples=['load_tool("ticktick.get_auth_status")()'])
def get_auth_status() -> dict[str, Any]:
    configured = False
    error = None
    try:
        read_token()
        configured = True
    except TickTickError as exc:
        error = str(exc)
    return {'token_configured': configured, 'token_source': 'environment' if get_setting('TICKTICK_ACCESS_TOKEN') else 'file' if token_file() else None, 'oauth_client_configured': bool(get_setting('TICKTICK_CLIENT_ID') and get_setting('TICKTICK_CLIENT_SECRET') and get_setting('TICKTICK_REDIRECT_URI')), 'error': error, 'live_verified': False}


@register_tool(aliases=[], namespace='ticktick', description='Verify TickTick authorization with a read-only preferences call.', examples=['load_tool("ticktick.get_health")()'])
def get_health() -> dict[str, Any]:
    try:
        preferences = get_client().post('preference')
        return {'ok': True, 'authenticated': True, 'time_zone': preferences.get('timeZone') if isinstance(preferences, dict) else None}
    except TickTickError as exc:
        return {'ok': False, 'authenticated': False, 'status_code': exc.status_code, 'error': str(exc)}


@register_tool(aliases=[], tool_class='admin', namespace='ticktick', description='Revoke the configured TickTick token. All integrations using that token lose access immediately.', examples=['load_tool("ticktick.revoke_authorization")()'])
def revoke_authorization() -> dict[str, Any]:
    get_client().revoke()
    return {'revoked': True, 'local_credential_removed': False}
