"""Google Docs client helpers."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from nexus_tools_google_common.client import (
    coerce_json,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    get_client as get_google_client,
    quote_path_segment,
)


def docs_request(
    path: str,
    *,
    method: str = "GET",
    params: Optional[Mapping[str, Any]] = None,
    payload: Optional[Any] = None,
) -> Dict[str, Any]:
    return get_google_client().request(
        "docs",
        path,
        method=method,
        params=params,
        payload=payload,
    )


def document_path(document_id: str, suffix: str = "") -> str:
    base = f"documents/{quote_path_segment(document_id)}"
    return f"{base}{suffix}" if suffix else base


def require_request_list(value: Any) -> list[Dict[str, Any]]:
    parsed = coerce_json(value)
    if not isinstance(parsed, list):
        raise ValueError("requests must be a JSON array")
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("each request must be a JSON object")
    return parsed


def require_object(value: Any, name: str) -> Dict[str, Any]:
    parsed = coerce_json(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def clean_params(params: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def clean_body(body: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in body.items() if value is not None}
