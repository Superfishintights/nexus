"""Build deterministic Sonarr Phase 5 migration source evidence.

This is a migration exporter, not an OpenAPI tool generator.  It reads the
literal metadata already committed in the Sonarr pack, retains the current
Python-facing schemas as the original representation, and writes a canonical
normalized view plus immutable digests for the connector gateway.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewed_actions import reviewed_actions

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
OUTPUT = HERE / "source.v1.json"
SPEC = PACK / "v3.json"
SCHEMA_VERSION = "nexus.phase5.sonarr-source/v1"
MAPPING_VERSION = "sonarr.identity-map/v1"
ACTION_METADATA_REVISION = "sonarr.actions/2026-07-12"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _literal_keyword(call: ast.Call, name: str, default: Any) -> Any:
    for keyword in call.keywords:
        if keyword.arg == name:
            return ast.literal_eval(keyword.value)
    return default


def _registered_function(tree: ast.Module) -> tuple[ast.FunctionDef, ast.Call] | None:
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            target = decorator.func
            if (isinstance(target, ast.Name) and target.id == "register_tool") or (
                isinstance(target, ast.Attribute) and target.attr == "register_tool"
            ):
                return node, decorator
    return None


def _annotation_schema(annotation: ast.expr | None) -> dict[str, Any]:
    text = ast.unparse(annotation) if annotation is not None else "Any"
    nullable = "Optional" in text or "None" in text
    if "Dict" in text or "dict" in text:
        schema: dict[str, Any] = {"type": "object"}
    elif "bool" in text:
        schema = {"type": "boolean"}
    elif "int" in text:
        schema = {"type": "integer"}
    elif "float" in text:
        schema = {"type": "number"}
    elif "str" in text:
        schema = {"type": "string"}
    else:
        schema = {}
    if nullable and "type" in schema:
        schema["type"] = [schema["type"], "null"]
    return schema


def _function_schema(function: ast.FunctionDef) -> dict[str, Any]:
    arguments = function.args.args
    defaults_at = len(arguments) - len(function.args.defaults)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for index, argument in enumerate(arguments):
        properties[argument.arg] = _annotation_schema(argument.annotation)
        if index < defaults_at:
            required.append(argument.arg)
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _transport(function: ast.FunctionDef) -> dict[str, Any]:
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"get", "post", "put", "delete", "head"} or not node.args:
            continue
        endpoint_node = node.args[0]
        if isinstance(endpoint_node, ast.Constant):
            endpoint = ast.literal_eval(endpoint_node)
        elif isinstance(endpoint_node, ast.JoinedStr):
            pieces: list[str] = []
            for part in endpoint_node.values:
                if isinstance(part, ast.Constant):
                    pieces.append(str(part.value))
                elif isinstance(part, ast.FormattedValue):
                    pieces.append("{" + ast.unparse(part.value) + "}")
            endpoint = "".join(pieces)
        else:
            raise ValueError(f"unsupported endpoint expression for {function.name}")
        return {
            "kind": "sonarr-rest",
            "method": node.func.attr.upper(),
            "endpointTemplate": endpoint,
            "apiPath": "" if endpoint == "ping" else "/api/v3",
        }
    raise ValueError(f"cannot find transport call for {function.name}")


def _tool_entry(path: Path, function: ast.FunctionDef, decorator: ast.Call) -> dict[str, Any]:
    namespace = _literal_keyword(decorator, "namespace", "")
    base_name = _literal_keyword(decorator, "name", function.name)
    legacy_name = f"{namespace}.{base_name}" if namespace else base_name
    aliases = _literal_keyword(decorator, "aliases", [])
    # The legacy register_tool surface declares no output schema. Preserve that
    # absence exactly; an empty object would be a newly invented contract.
    original = {"inputSchema": _function_schema(function)}
    normalized = _normalize(original)
    review = reviewed_actions()[legacy_name]
    source = {
        "kind": "generated-rest",
        "module": f"nexus_tools_sonarr.{path.stem}",
        "sourceFile": f"tool_packs/nexus_tools_sonarr/nexus_tools_sonarr/{path.name}",
        "openapiDocumentDigest": _digest(json.loads(SPEC.read_text(encoding="utf-8"))),
        "transport": _transport(function),
    }
    material = {
        "description": _literal_keyword(decorator, "description", ast.get_docstring(function) or ""),
        "examples": _literal_keyword(decorator, "examples", []),
        "identityMapping": {
            "mappingVersion": MAPPING_VERSION,
            "legacyCanonicalName": legacy_name,
            "gatewayCanonicalName": f"sonarr:{base_name}",
            "aliases": aliases,
        },
        "schemas": {
            "original": original,
            "normalized": normalized,
            "transforms": [
                {
                    "transformId": "nexus.schema.canonical-key-order",
                    "version": "1.0.0",
                    "direction": "input",
                    "reversible": True,
                    "lossy": False,
                    "notes": "Sort JSON object keys; retained original remains authoritative.",
                },
            ],
        },
        "action": {
            "schemaVersion": 1,
            "reviewed": True,
            "actionRef": f"action:sonarr:{base_name}",
            "actionClass": review.action_class,
            "metadataRevision": ACTION_METADATA_REVISION,
            "reviewerRef": "review:sonarr-phase5-manual",
            "impact": review.impact,
        },
        "source": source,
    }
    return {**material, "revisionDigest": _digest(material)}


def _compact_helper_entry() -> dict[str, Any]:
    legacy_name = "sonarr.list_season_releases"
    review = reviewed_actions()[legacy_name]
    properties = {
        "series_id": {"type": ["integer", "null"]},
        "series_title": {"type": ["string", "null"]},
        "query": {"type": ["string", "null"]},
        "season_number": {"type": ["integer", "null"]},
        "quality_contains": {"type": ["string", "null"]},
        "full_season_only": {"type": "boolean"},
        "min_custom_format_score": {"type": ["integer", "null"]},
        "positive_score_only": {"type": "boolean"},
        "max_results": {"type": ["integer", "null"], "minimum": 0},
        "include_rejected": {"type": "boolean"},
        "download_allowed": {"type": ["boolean", "null"]},
    }
    original = {
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": properties},
    }
    material = {
        "description": "Read-only Sonarr season release search that filters and compacts GET /api/v3/release results.",
        "examples": ['load_tool("sonarr.list_season_releases")(series_title="Game of Thrones", season_number=6, quality_contains="1080p", positive_score_only=True)'],
        "identityMapping": {
            "mappingVersion": MAPPING_VERSION,
            "legacyCanonicalName": legacy_name,
            "gatewayCanonicalName": "sonarr:list_season_releases",
            "aliases": [],
        },
        "schemas": {
            "original": original,
            "normalized": _normalize(original),
            "transforms": [
                {"transformId": "nexus.schema.canonical-key-order", "version": "1.0.0", "direction": "input", "reversible": True, "lossy": False, "notes": "Sort JSON object keys; retained original remains authoritative."},
            ],
        },
        "action": {
            "schemaVersion": 1, "reviewed": True, "actionRef": "action:sonarr:list_season_releases",
            "actionClass": review.action_class, "metadataRevision": ACTION_METADATA_REVISION,
            "reviewerRef": "review:sonarr-phase5-manual",
            "impact": review.impact,
        },
        "source": {
            "kind": "curated-helper",
            "module": "nexus_tools_sonarr.phase5_connector.adapter",
            "sourceFile": "tool_packs/nexus_tools_sonarr/nexus_tools_sonarr/phase5_connector/adapter.py",
            "semanticInput": "protected current Sonarr list_season_releases helper",
            "transport": {"kind": "curated-sonarr-release-search"},
        },
    }
    return {**material, "revisionDigest": _digest(material)}


def build() -> dict[str, Any]:
    tools: list[dict[str, Any]] = []
    for path in sorted(PACK.glob("*.py")):
        registered = _registered_function(ast.parse(path.read_text(encoding="utf-8")))
        if registered is not None:
            tools.append(_tool_entry(path, *registered))
    tools.append(_compact_helper_entry())
    tools.sort(key=lambda item: item["identityMapping"]["legacyCanonicalName"])

    names = {item["identityMapping"]["legacyCanonicalName"] for item in tools}
    reviewed = set(reviewed_actions())
    if names != reviewed:
        raise ValueError(f"action review mismatch missing={sorted(names-reviewed)} extra={sorted(reviewed-names)}")
    aliases = [alias for item in tools for alias in item["identityMapping"]["aliases"]]
    if len(aliases) != len(set(aliases)):
        raise ValueError("duplicate Sonarr alias")
    mapping_material = [item["identityMapping"] for item in tools]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "integration": {
            "schemaVersion": "nexus.phase2.integration/v1",
            "integrationId": "integration.sonarr",
            "namespace": "sonarr",
            "provider": {"kind": "native_connector", "definitionRef": "nexus-definition:sonarr/v1"},
            "displayName": "Sonarr",
            "tags": ["media", "series"],
        },
        "connectionContract": {
            "schemaVersion": "nexus.phase5.connector-connection/v1",
            "required": ["connectionId", "integrationId", "endpoint", "secretRef"],
            "secretFields": ["secretRef"],
            "catalogueVisibleFields": ["connectionId", "integrationId", "name"],
        },
        "identityMapping": {"version": MAPPING_VERSION, "revisionDigest": _digest(mapping_material)},
        "counts": {"canonical": len(tools), "aliases": len(aliases), "deprecatedPlaceholders": 6},
        "tools": tools,
    }


if __name__ == "__main__":
    source = build()
    OUTPUT.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), **source["counts"], "mappingRevision": source["identityMapping"]["revisionDigest"]}, sort_keys=True))
