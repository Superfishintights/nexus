"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="Get the current user's general settings. Returns the same settings as the settings field of GET /user. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback.",
    examples=['load_tool("vikunja.get_general_settings")()'],
    tool_class='read',
    aliases=[],
)
def get_general_settings(params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/user/settings/general. Returns the same settings as the settings field of GET /user.'
    client = get_client()
    return safe_response(safe_request(client, 'GET', 'user/settings/general', params=params))


@register_tool(
    namespace="vikunja",
    description="Update the current user's general settings (partial). Partial update operation supporting both JSON Merge Patch & JSON Patch updates. Uses JSON Merge Patch: send only changed fields, including explicit null when needed. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback. Request body schema: {\"content\":{\"application/json-patch+json\":{\"schema\":{\"items\":{\"$ref\":\"#/components/schemas/JsonPatchOp\"},\"type\":[\"array\",\"null\"]}},\"application/merge-patch+json\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/UserGeneralSettings.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"default_project_id\":{\"description\":\"Project a task is filed under when created without an explicit project.\",\"format\":\"int64\",\"type\":\"integer\"},\"discoverable_by_email\":{\"description\":\"If true, the user can be found when searching for their exact email.\",\"type\":\"boolean\"},\"discoverable_by_name\":{\"description\":\"If true, this user can be found by their name or parts of it when searching.\",\"type\":\"boolean\"},\"email_reminders_enabled\":{\"description\":\"If enabled, sends email reminders of tasks to the user.\",\"type\":\"boolean\"},\"extra_settings_links\":{\"additionalProperties\":{},\"description\":\"Additional settings links provided by the OpenID provider. Server-controlled.\",\"readOnly\":true,\"type\":\"object\"},\"frontend_settings\":{\"description\":\"Arbitrary settings used only by the frontend. Any JSON value; stored and returned verbatim.\"},\"language\":{\"description\":\"The user's language.\",\"type\":\"string\"},\"name\":{\"description\":\"The full name of the user.\",\"type\":\"string\"},\"overdue_tasks_reminders_enabled\":{\"description\":\"If enabled, the user gets an email for their overdue tasks each morning.\",\"type\":\"boolean\"},\"overdue_tasks_reminders_time\":{\"description\":\"The time the daily overdue-tasks summary is sent, as HH:MM.\",\"type\":\"string\"},\"timezone\":{\"description\":\"The user's time zone, used to send task reminders in their local time.\",\"type\":\"string\"},\"week_start\":{\"description\":\"The day the week starts on: 0=sunday, 1=monday, \\u2026 6=saturday.\",\"format\":\"int64\",\"maximum\":6,\"minimum\":0,\"type\":\"integer\"}},\"type\":\"object\"}},\"application/merge-patch+shorthand\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/UserGeneralSettings.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"default_project_id\":{\"description\":\"Project a task is filed under when created without an explicit project.\",\"format\":\"int64\",\"type\":\"integer\"},\"discoverable_by_email\":{\"description\":\"If true, the user can be found when searching for their exact email.\",\"type\":\"boolean\"},\"discoverable_by_name\":{\"description\":\"If true, this user can be found by their name or parts of it when searching.\",\"type\":\"boolean\"},\"email_reminders_enabled\":{\"description\":\"If enabled, sends email reminders of tasks to the user.\",\"type\":\"boolean\"},\"extra_settings_links\":{\"additionalProperties\":{},\"description\":\"Additional settings links provided by the OpenID provider. Server-controlled.\",\"readOnly\":true,\"type\":\"object\"},\"frontend_settings\":{\"description\":\"Arbitrary settings used only by the frontend. Any JSON value; stored and returned verbatim.\"},\"language\":{\"description\":\"The user's language.\",\"type\":\"string\"},\"name\":{\"description\":\"The full name of the user.\",\"type\":\"string\"},\"overdue_tasks_reminders_enabled\":{\"description\":\"If enabled, the user gets an email for their overdue tasks each morning.\",\"type\":\"boolean\"},\"overdue_tasks_reminders_time\":{\"description\":\"The time the daily overdue-tasks summary is sent, as HH:MM.\",\"type\":\"string\"},\"timezone\":{\"description\":\"The user's time zone, used to send task reminders in their local time.\",\"type\":\"string\"},\"week_start\":{\"description\":\"The day the week starts on: 0=sunday, 1=monday, \\u2026 6=saturday.\",\"format\":\"int64\",\"maximum\":6,\"minimum\":0,\"type\":\"integer\"}},\"type\":\"object\"}}},\"required\":true}",
    examples=['load_tool("vikunja.update_general_settings")(fields={"language":"en"})'],
    tool_class='write',
    aliases=[],
)
def update_general_settings(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'PATCH /api/v2/user/settings/general. Partial update operation supporting both JSON Merge Patch & JSON Patch updates.'
    client = get_client()
    return safe_response(safe_request(client, 'PATCH', 'user/settings/general', params=params, body=fields_object(fields), headers={'Content-Type':'application/merge-patch+json'}))


@register_tool(
    namespace="vikunja",
    description="Update the current user's general settings. Replaces the authenticated user's general settings (name, reminders, discoverability, default project, week start, language, timezone, frontend settings). Use PATCH to change only some of them; it merges into frontend_settings key by key. Full replacement can reset omitted fields. Prefer the partial update tool for sparse changes. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/UserGeneralSettings\"}}},\"required\":true}",
    examples=['load_tool("vikunja.replace_general_settings")(fields={"language":"en","timezone":"Europe/London"})'],
    tool_class='write',
    aliases=[],
)
def replace_general_settings(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "PUT /api/v2/user/settings/general. Replaces the authenticated user's general settings (name, reminders, discoverability, default project, week start, language, timezone, frontend settings). Use PATCH to change only some of them; it merges into frontend_settings key by key."
    client = get_client()
    return safe_response(safe_request(client, 'PUT', 'user/settings/general', params=params, body=fields_object(fields)))


@register_tool(
    namespace="vikunja",
    description="Get the current user's avatar provider. Returns the avatar provider configured for the authenticated user. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback.",
    examples=['load_tool("vikunja.get_avatar_provider")()'],
    tool_class='read',
    aliases=[],
)
def get_avatar_provider(params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/user/settings/avatar/provider. Returns the avatar provider configured for the authenticated user.'
    client = get_client()
    return safe_response(safe_request(client, 'GET', 'user/settings/avatar/provider', params=params))


@register_tool(
    namespace="vikunja",
    description="Set the current user's avatar provider (partial). Partial update operation supporting both JSON Merge Patch & JSON Patch updates. Uses JSON Merge Patch: send only changed fields, including explicit null when needed. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback. Request body schema: {\"content\":{\"application/json-patch+json\":{\"schema\":{\"items\":{\"$ref\":\"#/components/schemas/JsonPatchOp\"},\"type\":[\"array\",\"null\"]}},\"application/merge-patch+json\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/UserAvatarProviderBody.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"avatar_provider\":{\"description\":\"The avatar provider. One of: gravatar (uses the user email), upload, initials, marble (random per user), ldap (synced from LDAP), openid (synced from OpenID), default.\",\"type\":\"string\"}},\"type\":\"object\"}},\"application/merge-patch+shorthand\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/UserAvatarProviderBody.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"avatar_provider\":{\"description\":\"The avatar provider. One of: gravatar (uses the user email), upload, initials, marble (random per user), ldap (synced from LDAP), openid (synced from OpenID), default.\",\"type\":\"string\"}},\"type\":\"object\"}}},\"required\":true}",
    examples=['load_tool("vikunja.update_avatar_provider")(fields={"avatar_provider":"default"})'],
    tool_class='write',
    aliases=[],
)
def update_avatar_provider(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'PATCH /api/v2/user/settings/avatar/provider. Partial update operation supporting both JSON Merge Patch & JSON Patch updates.'
    client = get_client()
    return safe_response(safe_request(client, 'PATCH', 'user/settings/avatar/provider', params=params, body=fields_object(fields), headers={'Content-Type':'application/merge-patch+json'}))


@register_tool(
    namespace="vikunja",
    description="Set the current user's avatar provider. Changes the avatar provider for the authenticated user. Valid values: gravatar, upload, initials, marble, ldap, openid, default. Full replacement can reset omitted fields. Prefer the partial update tool for sparse changes. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/UserAvatarProviderBody\"}}},\"required\":true}",
    examples=['load_tool("vikunja.replace_avatar_provider")(fields={"avatar_provider":"default"})'],
    tool_class='write',
    aliases=[],
)
def replace_avatar_provider(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'PUT /api/v2/user/settings/avatar/provider. Changes the avatar provider for the authenticated user. Valid values: gravatar, upload, initials, marble, ldap, openid, default.'
    client = get_client()
    return safe_response(safe_request(client, 'PUT', 'user/settings/avatar/provider', params=params, body=fields_object(fields)))


@register_tool(
    namespace="vikunja",
    description="List available time zones. Returns every time zone this Vikunja instance can handle. The list depends on the host system and is unsorted; sort it client-side. Credential fields in nested settings are redacted from responses; do not replace settings from a redacted readback.",
    examples=['load_tool("vikunja.list_timezones")()'],
    tool_class='read',
    aliases=[],
)
def list_timezones(params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/user/timezones. Returns every time zone this Vikunja instance can handle. The list depends on the host system and is unsorted; sort it client-side.'
    client = get_client()
    return safe_response(safe_request(client, 'GET', 'user/timezones', params=params))

