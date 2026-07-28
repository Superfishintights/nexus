"""Google Sheets values tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .base import SheetsToolBase
from .client import clean_body, clean_params, coerce_list, optional_bool, optional_str, quote_range


class ValuesTools(SheetsToolBase):
    def _values_path(self, spreadsheet_id: str, cell_range: str, suffix: str = "") -> str:
        return f"{self.spreadsheet_path(spreadsheet_id)}/values/{quote_range(cell_range)}{suffix}"

    @staticmethod
    def _value_range(cell_range: Optional[str], values: Any, major_dimension: str) -> Dict[str, Any]:
        rows = coerce_list(values, name="values")
        return clean_body({"range": cell_range, "majorDimension": major_dimension, "values": rows})

    def get_values(
        self,
        spreadsheet_id: str,
        cell_range: str,
        *,
        major_dimension: Optional[str] = None,
        value_render_option: Optional[str] = None,
        date_time_render_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.request(
            self._values_path(spreadsheet_id, cell_range),
            params=clean_params(
                {
                    "majorDimension": optional_str(major_dimension),
                    "valueRenderOption": optional_str(value_render_option),
                    "dateTimeRenderOption": optional_str(date_time_render_option),
                }
            ),
        )

    def batch_get_values(
        self,
        spreadsheet_id: str,
        ranges: Any,
        *,
        major_dimension: Optional[str] = None,
        value_render_option: Optional[str] = None,
        date_time_render_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, "/values:batchGet"),
            params=clean_params(
                {
                    "ranges": coerce_list(ranges, name="ranges"),
                    "majorDimension": optional_str(major_dimension),
                    "valueRenderOption": optional_str(value_render_option),
                    "dateTimeRenderOption": optional_str(date_time_render_option),
                }
            ),
        )

    def get_values_by_data_filter(
        self,
        spreadsheet_id: str,
        data_filters: Any,
        *,
        major_dimension: Optional[str] = None,
        value_render_option: Optional[str] = None,
        date_time_render_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        body = clean_body(
            {
                "dataFilters": coerce_list(data_filters, name="data_filters"),
                "majorDimension": optional_str(major_dimension),
                "valueRenderOption": optional_str(value_render_option),
                "dateTimeRenderOption": optional_str(date_time_render_option),
            }
        )
        return self.request(self.spreadsheet_path(spreadsheet_id, "/values:batchGetByDataFilter"), method="POST", payload=body)

    def update_values(
        self,
        spreadsheet_id: str,
        cell_range: str,
        values: Any,
        *,
        major_dimension: str = "ROWS",
        value_input_option: str = "RAW",
        include_values_in_response: bool = False,
        response_value_render_option: Optional[str] = None,
        response_date_time_render_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = clean_params(
            {
                "valueInputOption": value_input_option,
                "includeValuesInResponse": optional_bool(include_values_in_response),
                "responseValueRenderOption": optional_str(response_value_render_option),
                "responseDateTimeRenderOption": optional_str(response_date_time_render_option),
            }
        )
        return self.request(
            self._values_path(spreadsheet_id, cell_range),
            method="PUT",
            params=params,
            payload=self._value_range(cell_range, values, major_dimension),
        )

    def batch_update_values(
        self,
        spreadsheet_id: str,
        data: Any,
        *,
        value_input_option: str = "RAW",
        include_values_in_response: bool = False,
        response_value_render_option: Optional[str] = None,
        response_date_time_render_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        body = clean_body(
            {
                "valueInputOption": value_input_option,
                "data": coerce_list(data, name="data"),
                "includeValuesInResponse": optional_bool(include_values_in_response),
                "responseValueRenderOption": optional_str(response_value_render_option),
                "responseDateTimeRenderOption": optional_str(response_date_time_render_option),
            }
        )
        return self.request(self.spreadsheet_path(spreadsheet_id, "/values:batchUpdate"), method="POST", payload=body)

    def update_values_by_data_filter(
        self,
        spreadsheet_id: str,
        data: Any,
        *,
        value_input_option: str = "RAW",
        include_values_in_response: bool = False,
    ) -> Dict[str, Any]:
        body = clean_body(
            {
                "valueInputOption": value_input_option,
                "data": coerce_list(data, name="data"),
                "includeValuesInResponse": optional_bool(include_values_in_response),
            }
        )
        return self.request(self.spreadsheet_path(spreadsheet_id, "/values:batchUpdateByDataFilter"), method="POST", payload=body)

    def append_values(
        self,
        spreadsheet_id: str,
        cell_range: str,
        values: Any,
        *,
        major_dimension: str = "ROWS",
        value_input_option: str = "RAW",
        insert_data_option: Optional[str] = None,
        include_values_in_response: bool = False,
    ) -> Dict[str, Any]:
        params = clean_params(
            {
                "valueInputOption": value_input_option,
                "insertDataOption": optional_str(insert_data_option),
                "includeValuesInResponse": optional_bool(include_values_in_response),
            }
        )
        return self.request(
            self._values_path(spreadsheet_id, cell_range, ":append"),
            method="POST",
            params=params,
            payload=self._value_range(cell_range, values, major_dimension),
        )

    def clear_values(self, spreadsheet_id: str, cell_range: str) -> Dict[str, Any]:
        return self.request(self._values_path(spreadsheet_id, cell_range, ":clear"), method="POST", payload={})

    def batch_clear_values(self, spreadsheet_id: str, ranges: Any) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, "/values:batchClear"),
            method="POST",
            payload={"ranges": coerce_list(ranges, name="ranges")},
        )

    def clear_values_by_data_filter(self, spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, "/values:batchClearByDataFilter"),
            method="POST",
            payload={"dataFilters": coerce_list(data_filters, name="data_filters")},
        )


def _tools() -> ValuesTools:
    return ValuesTools()


@register_tool(namespace="google_sheets", aliases=[], tool_class="read", description="Read values from a spreadsheet range.", examples=["load_tool('google_sheets.get_values')('SPREADSHEET_ID', 'Sheet1!A1:C10')"])
def get_values(spreadsheet_id: str, cell_range: str, *, major_dimension: Optional[str] = None, value_render_option: Optional[str] = None, date_time_render_option: Optional[str] = None) -> Dict[str, Any]:
    return _tools().get_values(spreadsheet_id, cell_range, major_dimension=major_dimension, value_render_option=value_render_option, date_time_render_option=date_time_render_option)


@register_tool(namespace="google_sheets", aliases=[], tool_class="read", description="Read values from multiple spreadsheet ranges.", examples=["load_tool('google_sheets.batch_get_values')('SPREADSHEET_ID', ['Sheet1!A1:A5'])"])
def batch_get_values(spreadsheet_id: str, ranges: Any, *, major_dimension: Optional[str] = None, value_render_option: Optional[str] = None, date_time_render_option: Optional[str] = None) -> Dict[str, Any]:
    return _tools().batch_get_values(spreadsheet_id, ranges, major_dimension=major_dimension, value_render_option=value_render_option, date_time_render_option=date_time_render_option)


@register_tool(namespace="google_sheets", aliases=[], tool_class="read", description="Read values by DataFilter selectors.", examples=["load_tool('google_sheets.get_values_by_data_filter')('SPREADSHEET_ID', [{'a1Range': 'Sheet1!A1:C10'}])"])
def get_values_by_data_filter(spreadsheet_id: str, data_filters: Any, *, major_dimension: Optional[str] = None, value_render_option: Optional[str] = None, date_time_render_option: Optional[str] = None) -> Dict[str, Any]:
    return _tools().get_values_by_data_filter(spreadsheet_id, data_filters, major_dimension=major_dimension, value_render_option=value_render_option, date_time_render_option=date_time_render_option)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update values in a spreadsheet range.", examples=["load_tool('google_sheets.update_values')('SPREADSHEET_ID', 'Sheet1!A1', [[1, 2]])"])
def update_values(spreadsheet_id: str, cell_range: str, values: Any, *, major_dimension: str = "ROWS", value_input_option: str = "RAW", include_values_in_response: bool = False, response_value_render_option: Optional[str] = None, response_date_time_render_option: Optional[str] = None) -> Dict[str, Any]:
    return _tools().update_values(spreadsheet_id, cell_range, values, major_dimension=major_dimension, value_input_option=value_input_option, include_values_in_response=include_values_in_response, response_value_render_option=response_value_render_option, response_date_time_render_option=response_date_time_render_option)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update values in multiple ranges.", examples=["load_tool('google_sheets.batch_update_values')('SPREADSHEET_ID', [{'range': 'Sheet1!A1', 'values': [[1]]}])"])
def batch_update_values(spreadsheet_id: str, data: Any, *, value_input_option: str = "RAW", include_values_in_response: bool = False, response_value_render_option: Optional[str] = None, response_date_time_render_option: Optional[str] = None) -> Dict[str, Any]:
    return _tools().batch_update_values(spreadsheet_id, data, value_input_option=value_input_option, include_values_in_response=include_values_in_response, response_value_render_option=response_value_render_option, response_date_time_render_option=response_date_time_render_option)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update values selected by DataFilter.", examples=["load_tool('google_sheets.update_values_by_data_filter')('SPREADSHEET_ID', [{'dataFilter': {'a1Range': 'Sheet1!A1'}, 'values': [[1]]}])"])
def update_values_by_data_filter(spreadsheet_id: str, data: Any, *, value_input_option: str = "RAW", include_values_in_response: bool = False) -> Dict[str, Any]:
    return _tools().update_values_by_data_filter(spreadsheet_id, data, value_input_option=value_input_option, include_values_in_response=include_values_in_response)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Append rows or columns to a values range.", examples=["load_tool('google_sheets.append_values')('SPREADSHEET_ID', 'Sheet1!A1', [['A', 'B']])"])
def append_values(spreadsheet_id: str, cell_range: str, values: Any, *, major_dimension: str = "ROWS", value_input_option: str = "RAW", insert_data_option: Optional[str] = None, include_values_in_response: bool = False) -> Dict[str, Any]:
    return _tools().append_values(spreadsheet_id, cell_range, values, major_dimension=major_dimension, value_input_option=value_input_option, insert_data_option=insert_data_option, include_values_in_response=include_values_in_response)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Clear values from one range.", examples=["load_tool('google_sheets.clear_values')('SPREADSHEET_ID', 'Sheet1!A1:C10')"])
def clear_values(spreadsheet_id: str, cell_range: str) -> Dict[str, Any]:
    return _tools().clear_values(spreadsheet_id, cell_range)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Clear values from multiple ranges.", examples=["load_tool('google_sheets.batch_clear_values')('SPREADSHEET_ID', ['Sheet1!A1:C10'])"])
def batch_clear_values(spreadsheet_id: str, ranges: Any) -> Dict[str, Any]:
    return _tools().batch_clear_values(spreadsheet_id, ranges)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Clear values selected by DataFilter.", examples=["load_tool('google_sheets.clear_values_by_data_filter')('SPREADSHEET_ID', [{'a1Range': 'Sheet1!A1:C10'}])"])
def clear_values_by_data_filter(spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
    return _tools().clear_values_by_data_filter(spreadsheet_id, data_filters)
