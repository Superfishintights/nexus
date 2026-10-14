"""Registered chart wrappers for Google Sheets."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .batch import BatchUpdateTools


def _tools() -> BatchUpdateTools:
    return BatchUpdateTools()


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Add an embedded chart to a spreadsheet.", examples=["load_tool('google_sheets.add_chart')('SPREADSHEET_ID', {'spec': {'title': 'Sales'}, 'position': {'newSheet': True}})"])
def add_chart(spreadsheet_id: str, chart: Any) -> Dict[str, Any]:
    return _tools().add_chart(spreadsheet_id, chart)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update an embedded chart spec.", examples=["load_tool('google_sheets.update_chart')('SPREADSHEET_ID', {'chartId': 123, 'spec': {'title': 'Sales'}})"])
def update_chart(spreadsheet_id: str, chart: Any) -> Dict[str, Any]:
    return _tools().update_chart(spreadsheet_id, chart)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete an embedded object such as a chart.", examples=["load_tool('google_sheets.delete_embedded_object')('SPREADSHEET_ID', 123)"])
def delete_embedded_object(spreadsheet_id: str, object_id: int) -> Dict[str, Any]:
    return _tools().delete_embedded_object(spreadsheet_id, object_id)
