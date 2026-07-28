from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "nexus_tools_google_sheets"

EXPECTED_TOOL_CLASSES = {
    "add_chart": "write",
    "add_conditional_format_rule": "write",
    "add_dimension": "write",
    "add_protected_range": "write",
    "add_sheet": "write",
    "append_values": "write",
    "auto_resize_dimensions": "write",
    "batch_clear_values": "destructive",
    "batch_get_values": "read",
    "batch_update_spreadsheet": "admin",
    "batch_update_values": "write",
    "clear_basic_filter": "destructive",
    "clear_values": "destructive",
    "clear_values_by_data_filter": "destructive",
    "copy_sheet_to_spreadsheet": "write",
    "create_developer_metadata": "write",
    "create_spreadsheet": "write",
    "delete_conditional_format_rule": "destructive",
    "delete_developer_metadata": "destructive",
    "delete_dimension": "destructive",
    "delete_embedded_object": "destructive",
    "delete_protected_range": "destructive",
    "delete_sheet": "destructive",
    "duplicate_sheet": "write",
    "get_spreadsheet": "read",
    "get_spreadsheet_by_data_filter": "read",
    "get_values": "read",
    "get_values_by_data_filter": "read",
    "merge_cells": "write",
    "move_dimension": "write",
    "rename_sheet": "write",
    "repeat_cell_format": "write",
    "search_developer_metadata": "read",
    "set_basic_filter": "write",
    "set_data_validation": "write",
    "sort_range": "write",
    "unmerge_cells": "write",
    "update_cells": "write",
    "update_chart": "write",
    "update_developer_metadata": "write",
    "update_protected_range": "write",
    "update_sheet_properties": "write",
    "update_values": "write",
    "update_values_by_data_filter": "write",
}


def _literal_keyword(call: ast.Call, name: str) -> Any:
    for keyword in call.keywords:
        if keyword.arg == name:
            return ast.literal_eval(keyword.value)
    raise AssertionError(f"missing keyword {name}")


def _registered_tool_classes() -> Dict[str, str]:
    classes: Dict[str, str] = {}
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                is_register_tool = (
                    isinstance(func, ast.Name)
                    and func.id == "register_tool"
                    or isinstance(func, ast.Attribute)
                    and func.attr == "register_tool"
                )
                if not is_register_tool:
                    continue
                assert _literal_keyword(decorator, "namespace") == "google_sheets"
                assert _literal_keyword(decorator, "aliases") == []
                classes[node.name] = _literal_keyword(decorator, "tool_class")
    return classes


def test_every_registered_tool_has_explicit_expected_class() -> None:
    assert _registered_tool_classes() == EXPECTED_TOOL_CLASSES


def test_mutating_tools_are_not_read() -> None:
    classes = _registered_tool_classes()
    mutating_terms = (
        "add_",
        "append_",
        "auto_resize_",
        "batch_update_",
        "clear_",
        "copy_",
        "create_",
        "delete_",
        "duplicate_",
        "merge_",
        "move_",
        "rename_",
        "repeat_",
        "set_",
        "sort_",
        "unmerge_",
        "update_",
    )
    misclassified = {
        name: tool_class
        for name, tool_class in classes.items()
        if name.startswith(mutating_terms) and tool_class == "read"
    }
    assert misclassified == {}
