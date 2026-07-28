"""Shared helpers for Google Calendar Nexus tools."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, Optional


CALENDAR_SERVICE = "calendar"


def get_client() -> Any:
    """Return the shared Google API client from nexus-tools-google-common."""

    from nexus_tools_google_common.client import get_client as get_google_client

    return get_google_client()


def quote_path_segment(value: str) -> str:
    """Quote one Google REST path segment without escaping slash separators."""

    return urllib.parse.quote(str(value), safe="")


def clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Drop unset query parameters while preserving false and zero values."""

    if not params:
        return {}
    return {key: value for key, value in params.items() if value is not None}


def merge_params(
    base: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge caller-supplied params over generated params and drop unset values."""

    merged: Dict[str, Any] = {}
    if base:
        merged.update(base)
    if extra:
        merged.update(extra)
    return clean_params(merged)


def calendar_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Any] = None,
) -> Any:
    """Execute a Calendar API request using the shared Google client."""

    return get_client().request(
        CALENDAR_SERVICE,
        path,
        method=method,
        params=clean_params(params),
        payload=body,
    )
