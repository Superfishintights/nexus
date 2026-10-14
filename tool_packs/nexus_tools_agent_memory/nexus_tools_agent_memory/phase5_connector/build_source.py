"""Build immutable Phase 5 agent-memory connector evidence from the legacy API AST."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
API_PATH = HERE.parent / "api.py"
OUTPUT_PATH = HERE / "source.v1.json"
PYTHON_OUTPUT_PATH = HERE / "source_v1.py"
SCHEMA_VERSION = "nexus.phase5.agent-memory-source/v1"
MAPPING_VERSION = "agent-memory.identity-map/v1"
ACTION_REVISION = "agent-memory.actions/2026-07-12"

ACTION_REVIEW: dict[str, tuple[str, str]] = {
    "get_health": ("observe", "read-only service health check"),
    "get_ready": ("observe", "read-only service and database readiness check"),
    "remember": ("mutate", "creates durable memory state"),
    "recall": ("observe", "reads matching memory evidence or summaries"),
    "list_memories": ("observe", "reads stored memory metadata and content"),
    "forget": ("mutate", "destructive removal of durable memory state"),
    "correct": ("mutate", "supersedes durable memory state with a replacement"),
    "ingest": ("external-effect", "queues worker-backed ingestion that creates durable memory state"),
}


def _literal(node: ast.AST) -> Any:
    return ast.literal_eval(node)


def _annotation_name(node: ast.AST | None) -> str:
    return "" if node is None else ast.unparse(node)


def _schema_for(annotation: ast.AST | None) -> dict[str, Any]:
    name = _annotation_name(annotation).replace(" ", "")
    optional = name.startswith("Optional[")
    inner = name[9:-1] if optional else name
    if inner == "str":
        result: dict[str, Any] = {"type": "string"}
    elif inner == "int":
        result = {"type": "integer"}
    elif inner in {"List[str]", "list[str]"}:
        result = {"type": "array", "items": {"type": "string"}}
    elif inner in {"Dict[str,Any]", "dict[str,Any]"}:
        result = {"type": "object"}
    else:
        result = {}
    if optional and "type" in result:
        result["type"] = [result["type"], "null"]
    return result


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _registered_metadata(function: ast.FunctionDef) -> dict[str, Any]:
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if not isinstance(decorator.func, ast.Name) or decorator.func.id != "register_tool":
            continue
        return {keyword.arg: _literal(keyword.value) for keyword in decorator.keywords if keyword.arg}
    raise ValueError(f"{function.name} is not a registered tool")


def _input_schema(function: ast.FunctionDef) -> dict[str, Any]:
    positional = [*function.args.posonlyargs, *function.args.args]
    positional_defaults = [None] * (len(positional) - len(function.args.defaults)) + list(function.args.defaults)
    keyword = list(function.args.kwonlyargs)
    keyword_defaults = list(function.args.kw_defaults)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for argument, default in zip([*positional, *keyword], [*positional_defaults, *keyword_defaults], strict=True):
        schema = _schema_for(argument.annotation)
        if default is None:
            required.append(argument.arg)
        else:
            try:
                value = _literal(default)
            except (ValueError, TypeError):
                value = None
            if value is not None:
                schema["default"] = value
        properties[argument.arg] = schema
    result: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        result["required"] = required
    return result


def build_source() -> dict[str, Any]:
    tree = ast.parse(API_PATH.read_text(encoding="utf-8"), filename=str(API_PATH))
    tools: list[dict[str, Any]] = []
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        metadata = _registered_metadata(function)
        aliases = list(metadata.get("aliases", []))
        if function.name == "remember" and "memorise" not in aliases:
            # Protected-live compatibility evidence; the saved checkout owns the api.py edit.
            aliases.append("memorise")
        original_input = _input_schema(function)
        normalized_input = _canonical(original_input)
        action_class, impact = ACTION_REVIEW[function.name]
        item: dict[str, Any] = {
            "description": metadata["description"],
            "examples": metadata["examples"],
            "identityMapping": {
                "mappingVersion": MAPPING_VERSION,
                "legacyCanonicalName": f"agent_memory.{function.name}",
                "gatewayCanonicalName": f"agent_memory:{function.name}",
                "aliases": aliases,
            },
            "schemas": {
                # The legacy decorator has no output-schema contract. Retain
                # that absence rather than inventing an unconstrained object.
                "original": {"inputSchema": original_input},
                "normalized": {"inputSchema": normalized_input},
            },
            "action": {
                "schemaVersion": 1,
                "reviewed": True,
                "actionRef": f"action:agent-memory:{function.name.replace('_', '-')}",
                "actionClass": action_class,
                "metadataRevision": ACTION_REVISION,
                "reviewerRef": "review:agent-memory-phase5-manual",
                "impact": impact,
            },
            "source": {
                "kind": "thin-service-adapter",
                "module": "nexus_tools_agent_memory.api",
                "sourceFile": "tool_packs/nexus_tools_agent_memory/nexus_tools_agent_memory/api.py",
                "operation": function.name,
            },
        }
        item["revisionDigest"] = _digest(item)
        tools.append(item)
    aliases = [alias for tool in tools for alias in tool["identityMapping"]["aliases"]]
    source: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "identityMapping": {"version": MAPPING_VERSION},
        "counts": {"canonical": len(tools), "aliases": len(aliases), "deprecatedPlaceholders": 0},
        "tools": tools,
    }
    source["identityMapping"]["revisionDigest"] = _digest(
        [tool["identityMapping"] for tool in tools]
    )
    return source


def main() -> None:
    source = build_source()
    OUTPUT_PATH.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PYTHON_OUTPUT_PATH.write_text(
        '"""Immutable agent-memory Phase 5 source evidence."""\n\n'
        f"SOURCE = {source!r}\n",
        encoding="utf-8",
    )
    print(json.dumps(source["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
