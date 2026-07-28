from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from nexus_tools_google_sheets.batch import BatchUpdateTools
from nexus_tools_google_sheets.spreadsheets import SpreadsheetTools
from nexus_tools_google_sheets.values import ValuesTools


class FakeClient:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def request(
        self,
        service: str,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Any] = None,
    ) -> Dict[str, Any]:
        call = {
            "service": service,
            "path": path,
            "method": method,
            "params": params,
            "payload": payload,
        }
        self.calls.append(call)
        return call


def test_get_spreadsheet_builds_repeated_range_params() -> None:
    fake = FakeClient()
    result = SpreadsheetTools(fake).get_spreadsheet(
        "sheet id",
        ranges=["Sheet1!A1:B2", "Data!A:A"],
        include_grid_data=True,
        fields="spreadsheetId,sheets.properties",
    )

    assert result["service"] == "sheets"
    assert result["path"] == "spreadsheets/sheet%20id"
    assert result["method"] == "GET"
    assert result["params"] == {
        "ranges": ["Sheet1!A1:B2", "Data!A:A"],
        "includeGridData": True,
        "fields": "spreadsheetId,sheets.properties",
    }


def test_update_values_quotes_a1_range_and_builds_value_range() -> None:
    fake = FakeClient()
    result = ValuesTools(fake).update_values(
        "spreadsheet",
        "Sheet 1!A1:B2",
        [["A", "B"]],
        value_input_option="USER_ENTERED",
    )

    assert result["path"] == "spreadsheets/spreadsheet/values/Sheet%201%21A1%3AB2"
    assert result["method"] == "PUT"
    assert result["params"]["valueInputOption"] == "USER_ENTERED"
    assert result["payload"] == {
        "range": "Sheet 1!A1:B2",
        "majorDimension": "ROWS",
        "values": [["A", "B"]],
    }


def test_batch_get_values_uses_values_batch_get_endpoint() -> None:
    fake = FakeClient()
    result = ValuesTools(fake).batch_get_values("spreadsheet", ["A!A1", "B!B2"])

    assert result["path"] == "spreadsheets/spreadsheet/values:batchGet"
    assert result["method"] == "GET"
    assert result["params"] == {"ranges": ["A!A1", "B!B2"]}


def test_add_sheet_builds_batch_update_request() -> None:
    fake = FakeClient()
    result = BatchUpdateTools(fake).add_sheet(
        "spreadsheet",
        title="Data",
        sheet_id=123,
        rows=100,
        columns=12,
    )

    assert result["path"] == "spreadsheets/spreadsheet:batchUpdate"
    assert result["method"] == "POST"
    assert result["payload"] == {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": "Data",
                        "sheetId": 123,
                        "gridProperties": {"rowCount": 100, "columnCount": 12},
                    }
                }
            }
        ]
    }


def test_repeat_cell_format_builds_grid_range_and_field_mask() -> None:
    fake = FakeClient()
    result = BatchUpdateTools(fake).repeat_cell_format(
        "spreadsheet",
        {"userEnteredFormat": {"textFormat": {"bold": True}}},
        "userEnteredFormat.textFormat.bold",
        sheet_id=0,
        start_row_index=0,
        end_row_index=1,
        start_column_index=0,
        end_column_index=3,
    )

    assert result["payload"]["requests"][0] == {
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 3,
            },
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat.textFormat.bold",
        }
    }


def test_values_reject_non_list_values() -> None:
    with pytest.raises(ValueError, match="values must be a JSON array"):
        ValuesTools(FakeClient()).update_values("spreadsheet", "A1", {"not": "rows"})
