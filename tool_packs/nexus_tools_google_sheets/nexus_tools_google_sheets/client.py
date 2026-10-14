"""Client and coercion helpers for Google Sheets tools."""

from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict, List, Optional, Protocol


class SheetsClient(Protocol):
    def request(
        self,
        service: str,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Any] = None,
    ) -> Any:
        ...


def get_client() -> SheetsClient:
    """Return the unified Google client from nexus-tools-google-common."""
    try:
        from nexus_tools_google_common.client import get_client as get_common_client
    except Exception as exc:  # pragma: no cover - depends on shared pack install
        raise RuntimeError(
            "nexus-tools-google-common must expose nexus_tools_google_common.client.get_client"
        ) from exc

    return get_common_client()


def quote_path_segment(value: Any, *, safe: str = "@") -> str:
    return urllib.parse.quote(str(value), safe=safe)


def quote_range(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload must be valid JSON") from exc
    return value


def coerce_list(value: Any, *, name: str = "value") -> List[Any]:
    parsed = coerce_json(value)
    if parsed is None:
        return []
    if isinstance(parsed, tuple):
        parsed = list(parsed)
    if not isinstance(parsed, list):
        raise ValueError(f"{name} must be a JSON array")
    return parsed


def coerce_dict(value: Any, *, name: str = "value") -> Dict[str, Any]:
    parsed = coerce_json(value)
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return parsed


def optional_str(value: Any, *, allow_empty: bool = False) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text or allow_empty:
        return text
    return None


def optional_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "y"}:
        return True
    if text in {"0", "false", "no", "off", "n"}:
        return False
    return None


def optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def clean_body(body: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in body.items() if value is not None}


def grid_range(
    *,
    sheet_id: Optional[int] = None,
    start_row_index: Optional[int] = None,
    end_row_index: Optional[int] = None,
    start_column_index: Optional[int] = None,
    end_column_index: Optional[int] = None,
) -> Dict[str, Any]:
    return clean_body(
        {
            "sheetId": sheet_id,
            "startRowIndex": start_row_index,
            "endRowIndex": end_row_index,
            "startColumnIndex": start_column_index,
            "endColumnIndex": end_column_index,
        }
    )


def dimension_range(
    *,
    sheet_id: int,
    dimension: str,
    start_index: int,
    end_index: int,
) -> Dict[str, Any]:
    return {
        "sheetId": sheet_id,
        "dimension": dimension,
        "startIndex": start_index,
        "endIndex": end_index,
    }
