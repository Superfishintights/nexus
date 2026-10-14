"""Load and verify immutable agent-memory Phase 5 source evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .source_v1 import SOURCE

SCHEMA_VERSION = "nexus.phase5.agent-memory-source/v1"
EXPECTED_SOURCE_REVISION_DIGEST = "sha256:321b257efe58992eb1217a20b358540f37fdd17a6add25f8bcb858b5b1d825cb"


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def load_source() -> dict[str, Any]:
    source = json.loads(json.dumps(SOURCE))
    if _digest(source) != EXPECTED_SOURCE_REVISION_DIGEST:
        raise ValueError("agent-memory source does not match the pinned reviewed revision")
    if source.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unsupported agent-memory connector source version")
    tools = source.get("tools")
    if not isinstance(tools, list):
        raise ValueError("agent-memory connector source tools must be a list")
    aliases = [alias for item in tools for alias in item["identityMapping"]["aliases"]]
    if source.get("counts") != {"canonical": 8, "aliases": 22, "deprecatedPlaceholders": 0}:
        raise ValueError("agent-memory connector source counts are not the reviewed inventory")
    names = [item["identityMapping"]["legacyCanonicalName"] for item in tools]
    if len(set(names)) != 8 or len(set(aliases)) != 22 or set(names).intersection(aliases):
        raise ValueError("agent-memory connector source contains identity collisions")
    for item in tools:
        revision = item.pop("revisionDigest", None)
        expected = _digest(item)
        item["revisionDigest"] = revision
        if revision != expected:
            raise ValueError("agent-memory connector source revision mismatch")
    mapping = source["identityMapping"]
    expected_mapping = _digest([item["identityMapping"] for item in tools])
    if mapping.get("revisionDigest") != expected_mapping:
        raise ValueError("agent-memory identity mapping revision mismatch")
    return source
