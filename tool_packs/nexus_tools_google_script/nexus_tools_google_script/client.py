"""Shared helpers for Google Apps Script Nexus tools."""
from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict, Optional

SCRIPT_SERVICE = "script"


def get_client() -> Any:
    """Return the shared Google API client from nexus-tools-google-common."""

    from nexus_tools_google_common.client import get_client as get_google_client

    return get_google_client()


def quote_path_segment(value: Any) -> str:
    return urllib.parse.quote(str(value), safe="")


def clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not params:
        return {}
    return {key: value for key, value in params.items() if value is not None}


def coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("value must be valid JSON") from exc
    return value


def script_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Any] = None,
) -> Any:
    return get_client().request(
        SCRIPT_SERVICE,
        path,
        method=method,
        params=clean_params(params),
        payload=body,
    )
