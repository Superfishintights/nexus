"""Side-effect-free access to the Sonarr migration source evidence."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

SOURCE_PATH = Path(__file__).with_name("source.v1.json")
SCHEMA_VERSION = "nexus.phase5.sonarr-source/v1"
EXPECTED_COUNTS = {"canonical": 222, "aliases": 14, "deprecatedPlaceholders": 6}
EXPECTED_SOURCE_REVISION_DIGEST = "sha256:374006d273a355a3ec9ce26c1107cc160ad5569820248dd1c072a5a1a2ef0728"


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@lru_cache(maxsize=1)
def load_source() -> Mapping[str, Any]:
    """Verify, then deeply freeze, source evidence on first connector use."""
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if _digest(source) != EXPECTED_SOURCE_REVISION_DIGEST:
        raise ValueError("Sonarr connector source does not match the pinned reviewed revision")
    if source.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unsupported Sonarr connector source version")
    if source.get("counts") != EXPECTED_COUNTS:
        raise ValueError("Sonarr connector source counts are not the reviewed inventory")
    tools = source.get("tools")
    if not isinstance(tools, list) or len(tools) != EXPECTED_COUNTS["canonical"]:
        raise ValueError("Sonarr connector source tools do not match the reviewed inventory")

    names: list[str] = []
    aliases: list[str] = []
    for item in tools:
        if not isinstance(item, dict):
            raise ValueError("Sonarr connector source tool must be an object")
        identity = item.get("identityMapping")
        if not isinstance(identity, dict):
            raise ValueError("Sonarr connector source tool identity is invalid")
        name = identity.get("legacyCanonicalName")
        item_aliases = identity.get("aliases")
        if not isinstance(name, str) or not isinstance(item_aliases, list) or not all(
            isinstance(alias, str) for alias in item_aliases
        ):
            raise ValueError("Sonarr connector source identity is invalid")
        revision = item.pop("revisionDigest", None)
        expected = _digest(item)
        item["revisionDigest"] = revision
        if revision != expected:
            raise ValueError(f"Sonarr connector source revision mismatch: {name}")
        names.append(name)
        aliases.extend(item_aliases)

    if (
        len(set(names)) != EXPECTED_COUNTS["canonical"]
        or len(aliases) != EXPECTED_COUNTS["aliases"]
        or len(set(aliases)) != EXPECTED_COUNTS["aliases"]
        or set(names).intersection(aliases)
    ):
        raise ValueError("Sonarr connector source contains identity collisions")
    mapping = source.get("identityMapping")
    expected_mapping = _digest([item["identityMapping"] for item in tools])
    if (
        not isinstance(mapping, dict)
        or mapping.get("version") != "sonarr.identity-map/v1"
        or mapping.get("revisionDigest") != expected_mapping
    ):
        raise ValueError("Sonarr identity mapping revision mismatch")
    return _freeze(source)
