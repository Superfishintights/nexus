"""Base class for Google Sheets tool groups."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import SheetsClient, get_client, quote_path_segment


class SheetsToolBase:
    def __init__(self, client: Optional[SheetsClient] = None):
        self.client = client or get_client()

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Any] = None,
    ) -> Any:
        return self.client.request(
            "sheets",
            path,
            method=method,
            params=params,
            payload=payload,
        )

    @staticmethod
    def spreadsheet_path(spreadsheet_id: str, suffix: str = "") -> str:
        path = f"spreadsheets/{quote_path_segment(spreadsheet_id)}"
        return f"{path}{suffix}"
