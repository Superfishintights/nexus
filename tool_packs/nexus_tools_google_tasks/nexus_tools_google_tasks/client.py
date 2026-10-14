"""Google Tasks client helpers backed by nexus-tools-google-common."""

from __future__ import annotations

import json
import urllib.parse
from typing import Any, Optional


def get_client() -> Any:
    """Return the shared Google API client from the common Google package."""

    try:
        from nexus_tools_google_common import get_client as common_get_client
    except ImportError:
        from nexus_tools_google_common.client import get_client as common_get_client
    return common_get_client()


def quote_path_segment(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")


def coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return json.loads(text)
    return value


def optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value)


def optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)


def optional_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)
