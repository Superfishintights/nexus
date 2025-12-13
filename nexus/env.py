"""Environment-backed configuration helpers for Nexus.

This module handles:
- Reading settings from environment variables
- Reading settings from one or more `.env` files
- Caching `.env` reads and refreshing when files change
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing."""


_ENV_FILE_CACHE: dict[Path, tuple[float, dict[str, str]]] = {}


def _parse_env_value(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    values: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _parse_env_value(value)
    return values


def _get_env_file_values(path: Path) -> dict[str, str]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        _ENV_FILE_CACHE.pop(path, None)
        return {}

    cached = _ENV_FILE_CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    parsed = _read_env_file(path)
    _ENV_FILE_CACHE[path] = (mtime, parsed)
    return parsed


def _default_env_file_paths() -> list[Path]:
    """Return env file candidates, lowest precedence first."""

    explicit = os.getenv("NEXUS_ENV_FILE")
    if explicit:
        return [Path(explicit).expanduser()]

    home = Path.home()
    paths: list[Path] = []

    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    paths.append(xdg_config_home / "nexus" / ".env")
    paths.append(home / ".nexus" / ".env")
    paths.append(home / "Library" / "Application Support" / "nexus" / ".env")

    appdata = os.getenv("APPDATA")
    if appdata:
        paths.append(Path(appdata) / "nexus" / ".env")

    paths.append(Path.cwd() / ".env")

    return paths


def get_setting(name: str, *fallback_names: str) -> Optional[str]:
    """Return a setting from the process environment or a `.env` file.

    Resolution order (highest precedence first):
    1) Process environment variables
    2) `.env` in current working directory
    3) User-level `.env` in standard config locations

    Set `NEXUS_ENV_FILE` to force a specific `.env` file path.
    """

    candidates = (name,) + fallback_names

    for candidate in candidates:
        value = os.getenv(candidate) or os.getenv(candidate.lower())
        if value:
            return value

    merged: dict[str, str] = {}
    for path in _default_env_file_paths():
        merged.update(_get_env_file_values(path))

    for candidate in candidates:
        value = merged.get(candidate) or merged.get(candidate.lower())
        if value:
            return value

    return None
