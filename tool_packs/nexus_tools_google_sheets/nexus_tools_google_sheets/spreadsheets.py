"""Spreadsheet-level Google Sheets tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .base import SheetsToolBase
from .client import clean_body, clean_params, coerce_dict, coerce_list, optional_bool, optional_str, quote_path_segment


class SpreadsheetTools(SheetsToolBase):
    def create_spreadsheet(
        self,
        spreadsheet: Any,
        *,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        body = coerce_dict(spreadsheet, name="spreadsheet")
        return self.request("spreadsheets", method="POST", params=clean_params({"fields": fields}), payload=body)

    def get_spreadsheet(
        self,
        spreadsheet_id: str,
        *,
        ranges: Optional[Any] = None,
        include_grid_data: bool = False,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = clean_params(
            {
                "ranges": coerce_list(ranges, name="ranges") if ranges is not None else None,
                "includeGridData": optional_bool(include_grid_data),
                "fields": optional_str(fields),
            }
        )
        return self.request(self.spreadsheet_path(spreadsheet_id), params=params)

    def get_spreadsheet_by_data_filter(
        self,
        spreadsheet_id: str,
        data_filters: Any,
        *,
        include_grid_data: bool = False,
    ) -> Dict[str, Any]:
        body = {
            "dataFilters": coerce_list(data_filters, name="data_filters"),
            "includeGridData": optional_bool(include_grid_data),
        }
        return self.request(
            self.spreadsheet_path(spreadsheet_id, ":getByDataFilter"),
            method="POST",
            payload=clean_body(body),
        )

    def batch_update_spreadsheet(
        self,
        spreadsheet_id: str,
        requests: Any,
        *,
        include_spreadsheet_in_response: bool = False,
        response_ranges: Optional[Any] = None,
        response_include_grid_data: bool = False,
    ) -> Dict[str, Any]:
        request_list = coerce_list(requests, name="requests")
        body = clean_body(
            {
                "requests": request_list,
                "includeSpreadsheetInResponse": optional_bool(include_spreadsheet_in_response),
                "responseRanges": coerce_list(response_ranges, name="response_ranges")
                if response_ranges is not None
                else None,
                "responseIncludeGridData": optional_bool(response_include_grid_data),
            }
        )
        return self.request(self.spreadsheet_path(spreadsheet_id, ":batchUpdate"), method="POST", payload=body)

    def copy_sheet_to_spreadsheet(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        destination_spreadsheet_id: str,
    ) -> Dict[str, Any]:
        path = f"{self.spreadsheet_path(spreadsheet_id)}/sheets/{quote_path_segment(sheet_id)}:copyTo"
        return self.request(
            path,
            method="POST",
            payload={"destinationSpreadsheetId": destination_spreadsheet_id},
        )


def _tools() -> SpreadsheetTools:
    return SpreadsheetTools()


@register_tool(
    namespace="google_sheets",
    aliases=[],
    tool_class="write",
    description="Create a Google spreadsheet from a Spreadsheet resource body.",
    examples=["load_tool('google_sheets.create_spreadsheet')({'properties': {'title': 'Budget'}})"],
)
def create_spreadsheet(spreadsheet: Any, *, fields: Optional[str] = None) -> Dict[str, Any]:
    return _tools().create_spreadsheet(spreadsheet, fields=fields)


@register_tool(
    namespace="google_sheets",
    aliases=[],
    tool_class="read",
    description="Get spreadsheet metadata and optionally grid data.",
    examples=["load_tool('google_sheets.get_spreadsheet')('SPREADSHEET_ID', ranges=['Sheet1!A1:C10'])"],
)
def get_spreadsheet(
    spreadsheet_id: str,
    *,
    ranges: Optional[Any] = None,
    include_grid_data: bool = False,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().get_spreadsheet(
        spreadsheet_id,
        ranges=ranges,
        include_grid_data=include_grid_data,
        fields=fields,
    )


@register_tool(
    namespace="google_sheets",
    aliases=[],
    tool_class="read",
    description="Get spreadsheet data using DataFilter selectors.",
    examples=["load_tool('google_sheets.get_spreadsheet_by_data_filter')('SPREADSHEET_ID', [{'a1Range': 'Sheet1!A1:C10'}])"],
)
def get_spreadsheet_by_data_filter(
    spreadsheet_id: str,
    data_filters: Any,
    *,
    include_grid_data: bool = False,
) -> Dict[str, Any]:
    return _tools().get_spreadsheet_by_data_filter(
        spreadsheet_id,
        data_filters,
        include_grid_data=include_grid_data,
    )


@register_tool(
    namespace="google_sheets",
    aliases=[],
    tool_class="admin",
    description="Run raw Sheets spreadsheets.batchUpdate requests.",
    examples=["load_tool('google_sheets.batch_update_spreadsheet')('SPREADSHEET_ID', [{'addSheet': {'properties': {'title': 'Data'}}}])"],
)
def batch_update_spreadsheet(
    spreadsheet_id: str,
    requests: Any,
    *,
    include_spreadsheet_in_response: bool = False,
    response_ranges: Optional[Any] = None,
    response_include_grid_data: bool = False,
) -> Dict[str, Any]:
    return _tools().batch_update_spreadsheet(
        spreadsheet_id,
        requests,
        include_spreadsheet_in_response=include_spreadsheet_in_response,
        response_ranges=response_ranges,
        response_include_grid_data=response_include_grid_data,
    )


@register_tool(
    namespace="google_sheets",
    aliases=[],
    tool_class="write",
    description="Copy one sheet tab into another spreadsheet.",
    examples=["load_tool('google_sheets.copy_sheet_to_spreadsheet')('SOURCE_ID', 0, 'DESTINATION_ID')"],
)
def copy_sheet_to_spreadsheet(
    spreadsheet_id: str,
    sheet_id: int,
    destination_spreadsheet_id: str,
) -> Dict[str, Any]:
    return _tools().copy_sheet_to_spreadsheet(spreadsheet_id, sheet_id, destination_spreadsheet_id)
