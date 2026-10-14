"""Inspect the packaged Chaptarr API contract without contacting the service."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool


def _asset(name: str) -> Dict[str, Any]:
    return json.loads(files("nexus_tools_chaptarr").joinpath(name).read_text(encoding="utf-8"))


def _schema_references(value: Any, schemas: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            reference = item.get("$ref", "")
            prefix = "#/components/schemas/"
            if isinstance(reference, str) and reference.startswith(prefix):
                name = reference[len(prefix):]
                if name in schemas and name not in result:
                    result[name] = schemas[name]
                    visit(schemas[name])
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return result


@register_tool(
    namespace="chaptarr",
    description="List packaged Chaptarr API schemas or read one resource schema, without a network request.",
    examples=[
        'load_tool("chaptarr.get_api_schema")()',
        'load_tool("chaptarr.get_api_schema")("BookResource")',
    ],
    tool_class="read",
    aliases=[],
)
def get_api_schema(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Return available schema names, or one schema with its referenced schemas."""
    document = _asset("openapi.json")
    schemas = document.get("components", {}).get("schemas", {})
    if schema_name is None:
        manifest = _asset("coverage-manifest.json")
        return {
            "source": manifest.get("source"),
            "source_commit": manifest.get("source_commit"),
            "openapi_version": document.get("openapi"),
            "api_info": document.get("info", {}),
            "schema_count": len(schemas),
            "schemas": sorted(schemas),
        }
    name = schema_name.removeprefix("#/components/schemas/")
    if name not in schemas:
        raise ValueError(f"Unknown Chaptarr API schema: {name}")
    referenced = _schema_references(schemas[name], schemas)
    referenced.pop(name, None)
    return {"name": name, "schema": schemas[name], "referenced_schemas": referenced}


@register_tool(
    namespace="chaptarr",
    description="Read a Chaptarr tool's packaged API operation, query fields, request body and resource schemas locally.",
    examples=[
        'load_tool("chaptarr.get_api_operation")("chaptarr.create_book")',
        'load_tool("chaptarr.get_api_operation")("get_book_lookup")',
    ],
    tool_class="read",
    aliases=[],
)
def get_api_operation(tool_name: str) -> Dict[str, Any]:
    """Inspect one generated endpoint by its qualified or unqualified tool name."""
    canonical = tool_name if tool_name.startswith("chaptarr.") else "chaptarr." + tool_name
    manifest = _asset("coverage-manifest.json")
    operation = None
    for item in manifest.get("operations", []):
        name = item.get("tool", "")
        if name == canonical or "chaptarr." + name == canonical:
            operation = item
            break
    if operation is None:
        raise ValueError(f"Unknown generated Chaptarr API tool: {canonical}")
    document = _asset("openapi.json")
    path_item = document.get("paths", {}).get(operation["path"], {})
    contract = path_item.get(operation["method"].lower(), {})
    schemas = document.get("components", {}).get("schemas", {})
    supplements = [
        item for item in manifest.get("source_supplements", [])
        if item.get("path") == operation["path"]
        or operation["path"] in item.get("paths", [])
        or item.get("covered_by") == canonical
    ]
    return {
        "tool": canonical,
        "source_commit": manifest.get("source_commit"),
        "coverage": operation,
        "operation": contract,
        "shared_parameters": path_item.get("parameters", []),
        "source_supplements": supplements,
        "referenced_schemas": _schema_references([contract, path_item.get("parameters", [])], schemas),
    }
