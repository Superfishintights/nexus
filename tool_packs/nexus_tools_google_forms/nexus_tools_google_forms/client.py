"""Shared helpers for Google Forms Nexus tools."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional


FORMS_SERVICE = "forms"


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


def merge_params(base: Optional[Dict[str, Any]] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if base:
        merged.update(base)
    if extra:
        merged.update(extra)
    return clean_params(merged)


def require_object(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def require_array(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array")
    return value


def forms_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Any] = None,
) -> Any:
    return get_client().request(
        FORMS_SERVICE,
        path,
        method=method,
        params=clean_params(params),
        payload=body,
    )
