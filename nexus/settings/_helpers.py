from __future__ import annotations

from typing import Optional

from ..env import ConfigurationError, get_setting


def require_setting(name: str, *fallback_names: str, message: str) -> str:
    value = get_setting(name, *fallback_names)
    if not value:
        raise ConfigurationError(message)
    return value


def normalize_url(value: str) -> str:
    trimmed = value.strip()
    if not trimmed.startswith(("http://", "https://")):
        trimmed = f"https://{trimmed}"
    return trimmed.rstrip("/")


def optional_setting(name: str, *fallback_names: str) -> Optional[str]:
    return get_setting(name, *fallback_names)

