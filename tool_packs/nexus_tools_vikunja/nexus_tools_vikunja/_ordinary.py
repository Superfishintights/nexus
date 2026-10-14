"""Pure validation and response filtering for the ordinary-operation modules."""
from __future__ import annotations
from typing import Any
from .client import positive_id, VikunjaError


_CREDENTIAL_FIELDS = frozenset({
    'token', 'access_token', 'refresh_token', 'password', 'secret', 'client_secret',
    'api_key', 'authorization', 'basic_auth_password', 'basic_auth_user',
})


def safe_response(value: Any) -> Any:
    """Keep ordinary data and pagination, redacting credential-bearing fields."""
    if isinstance(value, dict):
        return {key: '[redacted]' if str(key).lower() in _CREDENTIAL_FIELDS else safe_response(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [safe_response(item) for item in value]
    return value


def _credential_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        result = []
        for key, item in value.items():
            if str(key).lower() in _CREDENTIAL_FIELDS and isinstance(item, str) and item:
                result.append(item)
            result.extend(_credential_values(item))
        return result
    if isinstance(value, list):
        return [secret for item in value for secret in _credential_values(item)]
    return []


def safe_request(client: Any, method: str, endpoint: str, **kwargs: Any) -> Any:
    """Preserve sanitized provider errors, including arbitrary nested settings."""
    try:
        return client.request(method, endpoint, **kwargs)
    except VikunjaError as exc:
        message = str(exc)
        for secret in sorted(_credential_values(kwargs.get('body')), key=len, reverse=True):
            message = message.replace(secret, '[redacted]')
        raise VikunjaError(message, status=exc.status, code=exc.code) from None


def fields_object(fields: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fields, dict):
        raise ValueError('fields must be an object')
    return fields


def time_entry_fields(fields: dict[str, Any]) -> dict[str, Any]:
    fields_object(fields)
    task_id, project_id = fields.get('task_id', 0), fields.get('project_id', 0)
    if isinstance(task_id, bool) or isinstance(project_id, bool) or not isinstance(task_id, int) or not isinstance(project_id, int):
        raise ValueError('task_id and project_id must be integers when supplied')
    if task_id < 0 or project_id < 0 or bool(task_id) == bool(project_id):
        raise ValueError('Exactly one positive task_id or project_id must be supplied')
    positive_id(task_id or project_id)
    return fields


def subscription_entity(entity: str) -> str:
    if entity not in {'project', 'task'}:
        raise ValueError('entity must be project or task')
    return entity


def session_uuid(value: str) -> str:
    import uuid
    if not isinstance(value, str):
        raise ValueError('session_id must be a UUID string')
    try:
        result = str(uuid.UUID(value))
    except (ValueError, AttributeError):
        raise ValueError('session_id must be a UUID string') from None
    return result
