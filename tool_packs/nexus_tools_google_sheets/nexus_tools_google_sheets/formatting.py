"""Registered practical formatting and structure wrappers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .batch import BatchUpdateTools


def _tools() -> BatchUpdateTools:
    return BatchUpdateTools()


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Add a sheet tab to a spreadsheet.", examples=["load_tool('google_sheets.add_sheet')('SPREADSHEET_ID', title='Data')"])
def add_sheet(spreadsheet_id: str, *, title: str, sheet_id: Optional[int] = None, rows: Optional[int] = None, columns: Optional[int] = None) -> Dict[str, Any]:
    return _tools().add_sheet(spreadsheet_id, title=title, sheet_id=sheet_id, rows=rows, columns=columns)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete a sheet tab by numeric sheet ID.", examples=["load_tool('google_sheets.delete_sheet')('SPREADSHEET_ID', 123456)"])
def delete_sheet(spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
    return _tools().delete_sheet(spreadsheet_id, sheet_id)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Rename a sheet tab by numeric sheet ID.", examples=["load_tool('google_sheets.rename_sheet')('SPREADSHEET_ID', 0, 'Archive')"])
def rename_sheet(spreadsheet_id: str, sheet_id: int, title: str) -> Dict[str, Any]:
    return _tools().rename_sheet(spreadsheet_id, sheet_id, title)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Duplicate a sheet tab inside the same spreadsheet.", examples=["load_tool('google_sheets.duplicate_sheet')('SPREADSHEET_ID', 0, new_sheet_name='Copy')"])
def duplicate_sheet(spreadsheet_id: str, source_sheet_id: int, *, new_sheet_name: Optional[str] = None, new_sheet_id: Optional[int] = None, insert_sheet_index: Optional[int] = None) -> Dict[str, Any]:
    return _tools().duplicate_sheet(spreadsheet_id, source_sheet_id, new_sheet_name=new_sheet_name, new_sheet_id=new_sheet_id, insert_sheet_index=insert_sheet_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update arbitrary sheet properties using a field mask.", examples=["load_tool('google_sheets.update_sheet_properties')('SPREADSHEET_ID', {'sheetId': 0, 'hidden': True}, 'hidden')"])
def update_sheet_properties(spreadsheet_id: str, properties: Any, fields: str) -> Dict[str, Any]:
    return _tools().update_sheet_properties(spreadsheet_id, properties, fields)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Insert rows or columns in a sheet.", examples=["load_tool('google_sheets.add_dimension')('SPREADSHEET_ID', 0, 'ROWS', 1, 3)"])
def add_dimension(spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int, *, inherit_from_before: bool = False) -> Dict[str, Any]:
    return _tools().add_dimension(spreadsheet_id, sheet_id, dimension, start_index, end_index, inherit_from_before=inherit_from_before)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete rows or columns in a sheet.", examples=["load_tool('google_sheets.delete_dimension')('SPREADSHEET_ID', 0, 'ROWS', 1, 3)"])
def delete_dimension(spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int) -> Dict[str, Any]:
    return _tools().delete_dimension(spreadsheet_id, sheet_id, dimension, start_index, end_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Move rows or columns within a sheet.", examples=["load_tool('google_sheets.move_dimension')('SPREADSHEET_ID', 0, 'ROWS', 1, 3, 10)"])
def move_dimension(spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int, destination_index: int) -> Dict[str, Any]:
    return _tools().move_dimension(spreadsheet_id, sheet_id, dimension, start_index, end_index, destination_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Auto-resize rows or columns.", examples=["load_tool('google_sheets.auto_resize_dimensions')('SPREADSHEET_ID', 0, 'COLUMNS', 0, 4)"])
def auto_resize_dimensions(spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int) -> Dict[str, Any]:
    return _tools().auto_resize_dimensions(spreadsheet_id, sheet_id, dimension, start_index, end_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update cells from RowData values.", examples=["load_tool('google_sheets.update_cells')('SPREADSHEET_ID', {'sheetId': 0, 'rowIndex': 0, 'columnIndex': 0}, [{'values': []}], 'userEnteredValue')"])
def update_cells(spreadsheet_id: str, start: Any, rows: Any, fields: str) -> Dict[str, Any]:
    return _tools().update_cells(spreadsheet_id, start, rows, fields)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Apply a CellData format or value across a grid range.", examples=["load_tool('google_sheets.repeat_cell_format')('SPREADSHEET_ID', {'userEnteredFormat': {'textFormat': {'bold': True}}}, 'userEnteredFormat.textFormat.bold', sheet_id=0)"])
def repeat_cell_format(spreadsheet_id: str, cell: Any, fields: str, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None) -> Dict[str, Any]:
    return _tools().repeat_cell_format(spreadsheet_id, cell, fields, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Merge cells in a grid range.", examples=["load_tool('google_sheets.merge_cells')('SPREADSHEET_ID', sheet_id=0, start_row_index=0, end_row_index=1, start_column_index=0, end_column_index=3)"])
def merge_cells(spreadsheet_id: str, merge_type: str = "MERGE_ALL", *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None) -> Dict[str, Any]:
    return _tools().merge_cells(spreadsheet_id, merge_type, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Unmerge cells in a grid range.", examples=["load_tool('google_sheets.unmerge_cells')('SPREADSHEET_ID', sheet_id=0, start_row_index=0, end_row_index=1)"])
def unmerge_cells(spreadsheet_id: str, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None) -> Dict[str, Any]:
    return _tools().unmerge_cells(spreadsheet_id, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Set the basic filter for a grid range.", examples=["load_tool('google_sheets.set_basic_filter')('SPREADSHEET_ID', sheet_id=0, start_row_index=0)"])
def set_basic_filter(spreadsheet_id: str, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None, sort_specs: Optional[Any] = None, criteria: Optional[Any] = None) -> Dict[str, Any]:
    return _tools().set_basic_filter(spreadsheet_id, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index, sort_specs=sort_specs, criteria=criteria)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Clear the basic filter on a sheet.", examples=["load_tool('google_sheets.clear_basic_filter')('SPREADSHEET_ID', 0)"])
def clear_basic_filter(spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
    return _tools().clear_basic_filter(spreadsheet_id, sheet_id)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Set data validation for a grid range.", examples=["load_tool('google_sheets.set_data_validation')('SPREADSHEET_ID', {'condition': {'type': 'ONE_OF_LIST', 'values': []}}, sheet_id=0)"])
def set_data_validation(spreadsheet_id: str, rule: Any, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None, filtered_rows_included: bool = False) -> Dict[str, Any]:
    return _tools().set_data_validation(spreadsheet_id, rule, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index, filtered_rows_included=filtered_rows_included)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Add a conditional format rule.", examples=["load_tool('google_sheets.add_conditional_format_rule')('SPREADSHEET_ID', {'ranges': [], 'booleanRule': {}})"])
def add_conditional_format_rule(spreadsheet_id: str, rule: Any, *, index: int = 0) -> Dict[str, Any]:
    return _tools().add_conditional_format_rule(spreadsheet_id, rule, index=index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete a conditional format rule.", examples=["load_tool('google_sheets.delete_conditional_format_rule')('SPREADSHEET_ID', 0, 0)"])
def delete_conditional_format_rule(spreadsheet_id: str, sheet_id: int, index: int) -> Dict[str, Any]:
    return _tools().delete_conditional_format_rule(spreadsheet_id, sheet_id, index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Sort a grid range using Sheets SortSpec objects.", examples=["load_tool('google_sheets.sort_range')('SPREADSHEET_ID', [{'dimensionIndex': 0, 'sortOrder': 'ASCENDING'}], sheet_id=0)"])
def sort_range(spreadsheet_id: str, sort_specs: Any, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None) -> Dict[str, Any]:
    return _tools().sort_range(spreadsheet_id, sort_specs, sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Add a protected range.", examples=["load_tool('google_sheets.add_protected_range')('SPREADSHEET_ID', {'range': {'sheetId': 0}, 'description': 'Locked'})"])
def add_protected_range(spreadsheet_id: str, protected_range: Any) -> Dict[str, Any]:
    return _tools().add_protected_range(spreadsheet_id, protected_range)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update a protected range using a field mask.", examples=["load_tool('google_sheets.update_protected_range')('SPREADSHEET_ID', {'protectedRangeId': 1, 'description': 'Locked'}, 'description')"])
def update_protected_range(spreadsheet_id: str, protected_range: Any, fields: str) -> Dict[str, Any]:
    return _tools().update_protected_range(spreadsheet_id, protected_range, fields)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete a protected range.", examples=["load_tool('google_sheets.delete_protected_range')('SPREADSHEET_ID', 1)"])
def delete_protected_range(spreadsheet_id: str, protected_range_id: int) -> Dict[str, Any]:
    return _tools().delete_protected_range(spreadsheet_id, protected_range_id)
