"""Practical Google Docs batchUpdate request builders."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import (
    clean_body,
    coerce_json,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    require_object,
)
from .documents import batch_update_document, get_document


def _range(start_index: int, end_index: int, segment_id: Optional[str] = None, tab_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"startIndex": start_index, "endIndex": end_index}
    if segment_id:
        payload["segmentId"] = segment_id
    if tab_id:
        payload["tabId"] = tab_id
    return payload


def _location(index: int, segment_id: Optional[str] = None, tab_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"index": index}
    if segment_id:
        payload["segmentId"] = segment_id
    if tab_id:
        payload["tabId"] = tab_id
    return payload


def _end_index(document: Dict[str, Any]) -> int:
    content = document.get("body", {}).get("content", [])
    indexes = [item.get("endIndex") for item in content if isinstance(item.get("endIndex"), int)]
    return max(indexes, default=1)


@register_tool(
    namespace="google_docs",
    description="Append text at the end of a Google Docs document.",
    examples=["load_tool('google_docs.append_text')('DOC_ID', '\\nNext section')"],
    tool_class="write",
    aliases=[],
)
def append_text(document_id: str, text: str) -> Dict[str, Any]:
    document = get_document(document_id, fields="body/content/endIndex")
    insert_index = max(1, _end_index(document) - 1)
    return batch_update_document(
        document_id,
        [{"insertText": {"location": {"index": insert_index}, "text": text}}],
    )


@register_tool(
    namespace="google_docs",
    description="Insert text at a specific Google Docs structural index.",
    examples=["load_tool('google_docs.insert_text')('DOC_ID', 1, 'Hello')"],
    tool_class="write",
    aliases=[],
)
def insert_text(
    document_id: str,
    index: int,
    text: str,
    *,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [{"insertText": {"location": _location(index, segment_id, tab_id), "text": text}}],
    )


@register_tool(
    namespace="google_docs",
    description="Replace all matching text in a Google Docs document.",
    examples=["load_tool('google_docs.replace_all_text')('DOC_ID', '{{name}}', 'Jay')"],
    tool_class="destructive",
    aliases=[],
)
def replace_all_text(
    document_id: str,
    contains_text: str,
    replace_text: str,
    *,
    match_case: bool = True,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    request: Dict[str, Any] = {
        "replaceAllText": {
            "containsText": {"text": contains_text, "matchCase": match_case},
            "replaceText": replace_text,
        }
    }
    if tab_id:
        request["replaceAllText"]["tabsCriteria"] = {"tabIds": [tab_id]}
    return batch_update_document(document_id, [request])


@register_tool(
    namespace="google_docs",
    description="Delete a range of document content by structural indexes.",
    examples=["load_tool('google_docs.delete_content_range')('DOC_ID', 10, 20)"],
    tool_class="destructive",
    aliases=[],
)
def delete_content_range(
    document_id: str,
    start_index: int,
    end_index: int,
    *,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [{"deleteContentRange": {"range": _range(start_index, end_index, segment_id, tab_id)}}],
    )


@register_tool(
    namespace="google_docs",
    description="Insert a table at a Google Docs structural index.",
    examples=["load_tool('google_docs.insert_table')('DOC_ID', 1, rows=3, columns=4)"],
    tool_class="write",
    aliases=[],
)
def insert_table(
    document_id: str,
    index: int,
    *,
    rows: int,
    columns: int,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [
            {
                "insertTable": {
                    "rows": rows,
                    "columns": columns,
                    "location": _location(index, segment_id, tab_id),
                }
            }
        ],
    )


@register_tool(
    namespace="google_docs",
    description="Insert a page break at a Google Docs structural index.",
    examples=["load_tool('google_docs.insert_page_break')('DOC_ID', 25)"],
    tool_class="write",
    aliases=[],
)
def insert_page_break(
    document_id: str,
    index: int,
    *,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [{"insertPageBreak": {"location": _location(index, segment_id, tab_id)}}],
    )


@register_tool(
    namespace="google_docs",
    description="Create a named range in a Google Docs document.",
    examples=["load_tool('google_docs.create_named_range')('DOC_ID', 'Intro', 1, 50)"],
    tool_class="write",
    aliases=[],
)
def create_named_range(
    document_id: str,
    name: str,
    start_index: int,
    end_index: int,
    *,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [
            {
                "createNamedRange": {
                    "name": name,
                    "range": _range(start_index, end_index, segment_id, tab_id),
                }
            }
        ],
    )


@register_tool(
    namespace="google_docs",
    description="Update text style across a Google Docs range.",
    examples=["load_tool('google_docs.update_text_style')('DOC_ID', 1, 20, {'bold': True}, fields='bold')"],
    tool_class="write",
    aliases=[],
)
def update_text_style(
    document_id: str,
    start_index: int,
    end_index: int,
    text_style: Any,
    *,
    fields: str,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [
            {
                "updateTextStyle": {
                    "range": _range(start_index, end_index, segment_id, tab_id),
                    "textStyle": require_object(text_style, "text_style"),
                    "fields": fields,
                }
            }
        ],
    )


@register_tool(
    namespace="google_docs",
    description="Update paragraph style across a Google Docs range.",
    examples=["load_tool('google_docs.update_paragraph_style')('DOC_ID', 1, 20, {'namedStyleType': 'HEADING_1'}, fields='namedStyleType')"],
    tool_class="write",
    aliases=[],
)
def update_paragraph_style(
    document_id: str,
    start_index: int,
    end_index: int,
    paragraph_style: Any,
    *,
    fields: str,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [
            {
                "updateParagraphStyle": {
                    "range": _range(start_index, end_index, segment_id, tab_id),
                    "paragraphStyle": require_object(paragraph_style, "paragraph_style"),
                    "fields": fields,
                }
            }
        ],
    )


@register_tool(
    namespace="google_docs",
    description="Insert an inline image from a URI at a document index.",
    examples=["load_tool('google_docs.insert_inline_image')('DOC_ID', 1, 'https://example.com/image.png')"],
    tool_class="write",
    aliases=[],
)
def insert_inline_image(
    document_id: str,
    index: int,
    uri: str,
    *,
    object_size: Optional[Any] = None,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    image: Dict[str, Any] = {"uri": uri, "location": _location(index, segment_id, tab_id)}
    if object_size is not None:
        image["objectSize"] = require_object(object_size, "object_size")
    return batch_update_document(document_id, [{"insertInlineImage": image}])


@register_tool(
    namespace="google_docs",
    description="Pin a number of table rows as headers at a table start location.",
    examples=["load_tool('google_docs.pin_table_header_rows')('DOC_ID', 5, 1)"],
    tool_class="write",
    aliases=[],
)
def pin_table_header_rows(
    document_id: str,
    table_start_index: int,
    pinned_header_rows_count: int,
    *,
    segment_id: Optional[str] = None,
    tab_id: Optional[str] = None,
) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [
            {
                "pinTableHeaderRows": {
                    "tableStartLocation": _location(table_start_index, segment_id, tab_id),
                    "pinnedHeaderRowsCount": pinned_header_rows_count,
                }
            }
        ],
    )


@register_tool(
    namespace="google_docs",
    description="Merge cells in a Google Docs table range.",
    examples=["load_tool('google_docs.merge_table_cells')('DOC_ID', {'tableCellLocation': {...}, 'rowSpan': 1, 'columnSpan': 2})"],
    tool_class="write",
    aliases=[],
)
def merge_table_cells(document_id: str, table_range: Any) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [{"mergeTableCells": {"tableRange": require_object(table_range, "table_range")}}],
    )


@register_tool(
    namespace="google_docs",
    description="Unmerge cells in a Google Docs table range.",
    examples=["load_tool('google_docs.unmerge_table_cells')('DOC_ID', {'tableCellLocation': {...}, 'rowSpan': 1, 'columnSpan': 2})"],
    tool_class="write",
    aliases=[],
)
def unmerge_table_cells(document_id: str, table_range: Any) -> Dict[str, Any]:
    return batch_update_document(
        document_id,
        [{"unmergeTableCells": {"tableRange": require_object(table_range, "table_range")}}],
    )
