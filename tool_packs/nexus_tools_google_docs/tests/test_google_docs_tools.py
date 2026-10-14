from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

import pytest

from nexus_tools_google_docs import documents, requests


PACKAGE_DIR = Path(__file__).resolve().parents[1] / "nexus_tools_google_docs"


EXPECTED_TOOLS = {
    "append_text",
    "batch_update_document",
    "create_document",
    "create_named_range",
    "delete_content_range",
    "get_document",
    "insert_inline_image",
    "insert_page_break",
    "insert_table",
    "insert_text",
    "merge_table_cells",
    "pin_table_header_rows",
    "replace_all_text",
    "unmerge_table_cells",
    "update_paragraph_style",
    "update_text_style",
}

EXPECTED_TOOL_CLASSES = {
    "append_text": "write",
    "batch_update_document": "destructive",
    "create_document": "write",
    "create_named_range": "write",
    "delete_content_range": "destructive",
    "get_document": "read",
    "insert_inline_image": "write",
    "insert_page_break": "write",
    "insert_table": "write",
    "insert_text": "write",
    "merge_table_cells": "write",
    "pin_table_header_rows": "write",
    "replace_all_text": "destructive",
    "unmerge_table_cells": "write",
    "update_paragraph_style": "write",
    "update_text_style": "write",
}


def _registered_tools() -> Dict[str, Dict[str, Any]]:
    tools: Dict[str, Dict[str, Any]] = {}
    for path in PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not (isinstance(func, ast.Name) and func.id == "register_tool"):
                    continue
                metadata: Dict[str, Any] = {}
                for keyword in decorator.keywords:
                    if keyword.arg is not None:
                        metadata[keyword.arg] = keyword.value
                tools[node.name] = metadata
    return tools


def test_expected_tool_catalog_is_literal_google_docs_namespace() -> None:
    tools = _registered_tools()
    assert set(tools) == EXPECTED_TOOLS
    assert all("namespace" in metadata for metadata in tools.values())
    assert all(isinstance(metadata["namespace"], ast.Constant) for metadata in tools.values())
    assert {metadata["namespace"].value for metadata in tools.values()} == {"google_docs"}


def test_tool_classes_are_explicit_literal_and_security_accurate() -> None:
    tools = _registered_tools()

    assert set(tools) == set(EXPECTED_TOOL_CLASSES)
    assert all("tool_class" in metadata for metadata in tools.values())
    assert all(isinstance(metadata["tool_class"], ast.Constant) for metadata in tools.values())
    assert all(isinstance(metadata["tool_class"].value, str) for metadata in tools.values())
    assert {name: metadata["tool_class"].value for name, metadata in tools.items()} == EXPECTED_TOOL_CLASSES


def test_get_document_path_and_params(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(documents, "docs_request", fake_request)

    result = documents.get_document("doc 1", fields="title")

    assert result == {"ok": True}
    assert calls == [
        {
            "path": "documents/doc%201",
            "params": {"fields": "title"},
        }
    ]


def test_batch_update_requires_request_array(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(documents, "docs_request", fake_request)

    documents.batch_update_document("doc", [{"insertText": {"location": {"index": 1}, "text": "Hi"}}])

    assert calls[0]["path"] == "documents/doc:batchUpdate"
    assert calls[0]["method"] == "POST"
    assert calls[0]["payload"] == {
        "requests": [{"insertText": {"location": {"index": 1}, "text": "Hi"}}]
    }
    with pytest.raises(ValueError):
        documents.batch_update_document("doc", {"not": "a list"})


def test_replace_all_text_builds_tabs_criteria(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Any] = []

    def fake_batch(document_id: str, request_list: Any, **kwargs: Any) -> Dict[str, Any]:
        calls.append((document_id, request_list, kwargs))
        return {"ok": True}

    monkeypatch.setattr(requests, "batch_update_document", fake_batch)

    requests.replace_all_text("doc", "{{name}}", "Jay", match_case=False, tab_id="tab-1")

    assert calls == [
        (
            "doc",
            [
                {
                    "replaceAllText": {
                        "containsText": {"text": "{{name}}", "matchCase": False},
                        "replaceText": "Jay",
                        "tabsCriteria": {"tabIds": ["tab-1"]},
                    }
                }
            ],
            {},
        )
    ]


def test_style_helpers_validate_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Any] = []

    def fake_batch(document_id: str, request_list: Any, **kwargs: Any) -> Dict[str, Any]:
        calls.append(request_list)
        return {"ok": True}

    monkeypatch.setattr(requests, "batch_update_document", fake_batch)

    requests.update_text_style("doc", 1, 5, {"bold": True}, fields="bold")

    assert calls[0] == [
        {
            "updateTextStyle": {
                "range": {"startIndex": 1, "endIndex": 5},
                "textStyle": {"bold": True},
                "fields": "bold",
            }
        }
    ]
    with pytest.raises(ValueError):
        requests.update_paragraph_style("doc", 1, 5, ["bad"], fields="namedStyleType")


def test_append_text_uses_end_index_minus_one(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Any] = []

    monkeypatch.setattr(
        requests,
        "get_document",
        lambda document_id, fields=None: {"body": {"content": [{"endIndex": 7}]}},
    )

    def fake_batch(document_id: str, request_list: Any, **kwargs: Any) -> Dict[str, Any]:
        calls.append((document_id, request_list))
        return {"ok": True}

    monkeypatch.setattr(requests, "batch_update_document", fake_batch)

    requests.append_text("doc", " tail")

    assert calls == [
        (
            "doc",
            [{"insertText": {"location": {"index": 6}, "text": " tail"}}],
        )
    ]
