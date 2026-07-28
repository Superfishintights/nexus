"""Developer metadata tools for Google Sheets."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .base import SheetsToolBase
from .client import clean_body, coerce_dict, coerce_list


class MetadataTools(SheetsToolBase):
    def search_developer_metadata(self, spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, "/developerMetadata:search"),
            method="POST",
            payload={"dataFilters": coerce_list(data_filters, name="data_filters")},
        )

    def create_developer_metadata(self, spreadsheet_id: str, developer_metadata: Any) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, ":batchUpdate"),
            method="POST",
            payload={"requests": [{"createDeveloperMetadata": {"developerMetadata": coerce_dict(developer_metadata, name="developer_metadata")}}]},
        )

    def update_developer_metadata(self, spreadsheet_id: str, data_filters: Any, developer_metadata: Any, fields: str) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, ":batchUpdate"),
            method="POST",
            payload={
                "requests": [
                    {
                        "updateDeveloperMetadata": clean_body(
                            {
                                "dataFilters": coerce_list(data_filters, name="data_filters"),
                                "developerMetadata": coerce_dict(developer_metadata, name="developer_metadata"),
                                "fields": fields,
                            }
                        )
                    }
                ]
            },
        )

    def delete_developer_metadata(self, spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
        return self.request(
            self.spreadsheet_path(spreadsheet_id, ":batchUpdate"),
            method="POST",
            payload={"requests": [{"deleteDeveloperMetadata": {"dataFilters": coerce_list(data_filters, name="data_filters")}}]},
        )


def _tools() -> MetadataTools:
    return MetadataTools()


@register_tool(namespace="google_sheets", aliases=[], tool_class="read", description="Search developer metadata in a spreadsheet.", examples=["load_tool('google_sheets.search_developer_metadata')('SPREADSHEET_ID', [{'developerMetadataLookup': {'metadataKey': 'owner'}}])"])
def search_developer_metadata(spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
    return _tools().search_developer_metadata(spreadsheet_id, data_filters)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Create developer metadata with a batchUpdate request.", examples=["load_tool('google_sheets.create_developer_metadata')('SPREADSHEET_ID', {'metadataKey': 'owner', 'metadataValue': 'finance', 'visibility': 'DOCUMENT'})"])
def create_developer_metadata(spreadsheet_id: str, developer_metadata: Any) -> Dict[str, Any]:
    return _tools().create_developer_metadata(spreadsheet_id, developer_metadata)


@register_tool(namespace="google_sheets", aliases=[], tool_class="write", description="Update developer metadata matched by DataFilter.", examples=["load_tool('google_sheets.update_developer_metadata')('SPREADSHEET_ID', [{'developerMetadataLookup': {'metadataKey': 'owner'}}], {'metadataValue': 'ops'}, 'metadataValue')"])
def update_developer_metadata(spreadsheet_id: str, data_filters: Any, developer_metadata: Any, fields: str) -> Dict[str, Any]:
    return _tools().update_developer_metadata(spreadsheet_id, data_filters, developer_metadata, fields)


@register_tool(namespace="google_sheets", aliases=[], tool_class="destructive", description="Delete developer metadata matched by DataFilter.", examples=["load_tool('google_sheets.delete_developer_metadata')('SPREADSHEET_ID', [{'developerMetadataLookup': {'metadataKey': 'owner'}}])"])
def delete_developer_metadata(spreadsheet_id: str, data_filters: Any) -> Dict[str, Any]:
    return _tools().delete_developer_metadata(spreadsheet_id, data_filters)
