"""Google People client helpers backed by nexus-tools-google-common."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional

from nexus_tools_google_common.client import (
    coerce_json,
    coerce_list,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    get_client,
)


PEOPLE_SERVICE = "people"


def quote_resource_name(value: Any) -> str:
    """Quote a Google resource name while preserving resource slashes."""
    return urllib.parse.quote(str(value).strip("/"), safe="/@")


def request_people(
    path: str,
    *,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Any] = None,
) -> Any:
    return get_client().request(PEOPLE_SERVICE, path, method=method, params=params, payload=payload)


def require_object(value: Any, name: str) -> Dict[str, Any]:
    parsed = coerce_json(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def require_array(value: Any, name: str) -> List[Any]:
    parsed = coerce_json(value)
    if not isinstance(parsed, list):
        raise ValueError(f"{name} must be a JSON array")
    return parsed


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}
