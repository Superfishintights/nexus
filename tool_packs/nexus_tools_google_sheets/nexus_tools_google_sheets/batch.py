"""Practical Google Sheets spreadsheets.batchUpdate wrappers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import SheetsToolBase
from .client import clean_body, coerce_dict, coerce_list, dimension_range, grid_range, optional_bool, optional_int


class BatchUpdateTools(SheetsToolBase):
    def batch(self, spreadsheet_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, ":batchUpdate"),
            method="POST",
            payload={"requests": [request]},
        )

    def add_sheet(self, spreadsheet_id: str, *, title: str, sheet_id: Optional[int] = None, rows: Optional[int] = None, columns: Optional[int] = None) -> Dict[str, Any]:
        properties = clean_body({"title": title, "sheetId": sheet_id})
        grid = clean_body({"rowCount": rows, "columnCount": columns})
        if grid:
            properties["gridProperties"] = grid
        return self.batch(spreadsheet_id, {"addSheet": {"properties": properties}})

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"deleteSheet": {"sheetId": sheet_id}})

    def rename_sheet(self, spreadsheet_id: str, sheet_id: int, title: str) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "title": title}, "fields": "title"}})

    def duplicate_sheet(self, spreadsheet_id: str, source_sheet_id: int, *, new_sheet_name: Optional[str] = None, new_sheet_id: Optional[int] = None, insert_sheet_index: Optional[int] = None) -> Dict[str, Any]:
        return self.batch(
            spreadsheet_id,
            {"duplicateSheet": clean_body({"sourceSheetId": source_sheet_id, "insertSheetIndex": insert_sheet_index, "newSheetId": new_sheet_id, "newSheetName": new_sheet_name})},
        )

    def update_sheet_properties(self, spreadsheet_id: str, properties: Any, fields: str) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"updateSheetProperties": {"properties": coerce_dict(properties, name="properties"), "fields": fields}})

    def add_dimension(self, spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int, *, inherit_from_before: bool = False) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"insertDimension": {"range": dimension_range(sheet_id=sheet_id, dimension=dimension, start_index=start_index, end_index=end_index), "inheritFromBefore": optional_bool(inherit_from_before)}})

    def delete_dimension(self, spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"deleteDimension": {"range": dimension_range(sheet_id=sheet_id, dimension=dimension, start_index=start_index, end_index=end_index)}})

    def move_dimension(self, spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int, destination_index: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"moveDimension": {"source": dimension_range(sheet_id=sheet_id, dimension=dimension, start_index=start_index, end_index=end_index), "destinationIndex": destination_index}})

    def auto_resize_dimensions(self, spreadsheet_id: str, sheet_id: int, dimension: str, start_index: int, end_index: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"autoResizeDimensions": {"dimensions": dimension_range(sheet_id=sheet_id, dimension=dimension, start_index=start_index, end_index=end_index)}})

    def update_cells(self, spreadsheet_id: str, start: Any, rows: Any, fields: str) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"updateCells": {"start": coerce_dict(start, name="start"), "rows": coerce_list(rows, name="rows"), "fields": fields}})

    def repeat_cell_format(self, spreadsheet_id: str, cell: Any, fields: str, *, sheet_id: Optional[int] = None, start_row_index: Optional[int] = None, end_row_index: Optional[int] = None, start_column_index: Optional[int] = None, end_column_index: Optional[int] = None) -> Dict[str, Any]:
        return self.batch(
            spreadsheet_id,
            {
                "repeatCell": {
                    "range": grid_range(sheet_id=sheet_id, start_row_index=start_row_index, end_row_index=end_row_index, start_column_index=start_column_index, end_column_index=end_column_index),
                    "cell": coerce_dict(cell, name="cell"),
                    "fields": fields,
                }
            },
        )

    def merge_cells(self, spreadsheet_id: str, merge_type: str = "MERGE_ALL", **range_parts: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"mergeCells": {"range": grid_range(**range_parts), "mergeType": merge_type}})

    def unmerge_cells(self, spreadsheet_id: str, **range_parts: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"unmergeCells": {"range": grid_range(**range_parts)}})

    def set_basic_filter(self, spreadsheet_id: str, *, sort_specs: Optional[Any] = None, criteria: Optional[Any] = None, **range_parts: Any) -> Dict[str, Any]:
        basic_filter = clean_body({"range": grid_range(**range_parts), "sortSpecs": coerce_list(sort_specs, name="sort_specs") if sort_specs is not None else None, "criteria": coerce_dict(criteria, name="criteria") if criteria is not None else None})
        return self.batch(spreadsheet_id, {"setBasicFilter": {"filter": basic_filter}})

    def clear_basic_filter(self, spreadsheet_id: str, sheet_id: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"clearBasicFilter": {"sheetId": sheet_id}})

    def set_data_validation(self, spreadsheet_id: str, rule: Any, *, filtered_rows_included: bool = False, **range_parts: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"setDataValidation": {"range": grid_range(**range_parts), "rule": coerce_dict(rule, name="rule"), "filteredRowsIncluded": optional_bool(filtered_rows_included)}})

    def add_conditional_format_rule(self, spreadsheet_id: str, rule: Any, *, index: int = 0) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"addConditionalFormatRule": {"rule": coerce_dict(rule, name="rule"), "index": index}})

    def delete_conditional_format_rule(self, spreadsheet_id: str, sheet_id: int, index: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": index}})

    def sort_range(self, spreadsheet_id: str, sort_specs: Any, **range_parts: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"sortRange": {"range": grid_range(**range_parts), "sortSpecs": coerce_list(sort_specs, name="sort_specs")}})

    def add_protected_range(self, spreadsheet_id: str, protected_range: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"addProtectedRange": {"protectedRange": coerce_dict(protected_range, name="protected_range")}})

    def update_protected_range(self, spreadsheet_id: str, protected_range: Any, fields: str) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"updateProtectedRange": {"protectedRange": coerce_dict(protected_range, name="protected_range"), "fields": fields}})

    def delete_protected_range(self, spreadsheet_id: str, protected_range_id: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"deleteProtectedRange": {"protectedRangeId": protected_range_id}})

    def add_chart(self, spreadsheet_id: str, chart: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"addChart": {"chart": coerce_dict(chart, name="chart")}})

    def update_chart(self, spreadsheet_id: str, chart: Any) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"updateChartSpec": {"chartId": coerce_dict(chart, name="chart").get("chartId"), "spec": coerce_dict(chart, name="chart").get("spec")}})

    def delete_embedded_object(self, spreadsheet_id: str, object_id: int) -> Dict[str, Any]:
        return self.batch(spreadsheet_id, {"deleteEmbeddedObject": {"objectId": object_id}})
