"""Convenience wrappers for Google Slides batchUpdate request types."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .helpers import coerce_dict, coerce_list, dimension, drop_none, normalize_requests, singleton_request, size, transform


class RequestTools:
    """Build and apply common Google Slides batchUpdate requests."""

    def __init__(self, client: Any):
        self.client = client

    def apply(
        self,
        presentation_id: str,
        request: Dict[str, Any],
        required_revision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client.batch_update(
            presentation_id,
            [request],
            required_revision_id=required_revision_id,
        )

    def build_slide_request(
        self,
        page_object_id: Optional[str] = None,
        insertion_index: Optional[int] = None,
        predefined_layout: Optional[str] = None,
    ) -> Dict[str, Any]:
        slide_layout_reference = None
        if predefined_layout:
            slide_layout_reference = {"predefinedLayout": predefined_layout}
        return singleton_request(
            "createSlide",
            {
                "objectId": page_object_id,
                "insertionIndex": insertion_index,
                "slideLayoutReference": slide_layout_reference,
            },
        )

    def create_shape_request(
        self,
        object_id: str,
        page_object_id: str,
        shape_type: str,
        width: float,
        height: float,
        translate_x: float,
        translate_y: float,
    ) -> Dict[str, Any]:
        return singleton_request(
            "createShape",
            {
                "objectId": object_id,
                "shapeType": shape_type,
                "elementProperties": {
                    "pageObjectId": page_object_id,
                    "size": size(width, height),
                    "transform": transform(translate_x=translate_x, translate_y=translate_y),
                },
            },
        )

    def create_image_request(
        self,
        object_id: str,
        page_object_id: str,
        url: str,
        width: float,
        height: float,
        translate_x: float,
        translate_y: float,
    ) -> Dict[str, Any]:
        return singleton_request(
            "createImage",
            {
                "objectId": object_id,
                "url": url,
                "elementProperties": {
                    "pageObjectId": page_object_id,
                    "size": size(width, height),
                    "transform": transform(translate_x=translate_x, translate_y=translate_y),
                },
            },
        )

    def create_line_request(
        self,
        object_id: str,
        page_object_id: str,
        line_category: str,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> Dict[str, Any]:
        return singleton_request(
            "createLine",
            {
                "objectId": object_id,
                "lineCategory": line_category,
                "elementProperties": {
                    "pageObjectId": page_object_id,
                    "transform": transform(translate_x=start_x, translate_y=start_y),
                    "size": size(end_x - start_x, end_y - start_y),
                },
            },
        )

    def create_table_request(
        self,
        object_id: str,
        page_object_id: str,
        rows: int,
        columns: int,
        width: float,
        height: float,
        translate_x: float,
        translate_y: float,
    ) -> Dict[str, Any]:
        return singleton_request(
            "createTable",
            {
                "objectId": object_id,
                "rows": rows,
                "columns": columns,
                "elementProperties": {
                    "pageObjectId": page_object_id,
                    "size": size(width, height),
                    "transform": transform(translate_x=translate_x, translate_y=translate_y),
                },
            },
        )


def _tools() -> RequestTools:
    return RequestTools(get_client())


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a slide using presentations.batchUpdate.",
    examples=['load_tool("google_slides.create_slide")("presentation-id", predefined_layout="BLANK")'],
    tool_class="write",
)
def create_slide(
    presentation_id: str,
    page_object_id: Optional[str] = None,
    insertion_index: Optional[int] = None,
    predefined_layout: Optional[str] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    request = _tools().build_slide_request(page_object_id, insertion_index, predefined_layout)
    return _tools().apply(presentation_id, request, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete a slide or page element object.",
    examples=['load_tool("google_slides.delete_object")("presentation-id", "object-id")'],
    tool_class="destructive",
)
def delete_object(
    presentation_id: str,
    object_id: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("deleteObject", {"objectId": object_id}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete a slide by page object ID.",
    examples=['load_tool("google_slides.delete_slide")("presentation-id", "slide-id")'],
    tool_class="destructive",
)
def delete_slide(
    presentation_id: str,
    page_object_id: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return delete_object(presentation_id, page_object_id, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Duplicate a slide or page element.",
    examples=['load_tool("google_slides.duplicate_object")("presentation-id", "object-id")'],
    tool_class="write",
)
def duplicate_object(
    presentation_id: str,
    object_id: str,
    object_ids: Optional[Dict[str, str]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("duplicateObject", {"objectId": object_id, "objectIds": object_ids}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a shape on a slide.",
    examples=['load_tool("google_slides.create_shape")("presentation-id", "shape-id", "slide-id", "RECTANGLE", 300, 80, 72, 72)'],
    tool_class="write",
)
def create_shape(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    shape_type: str,
    width: float,
    height: float,
    translate_x: float,
    translate_y: float,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    request = _tools().create_shape_request(
        object_id,
        page_object_id,
        shape_type,
        width,
        height,
        translate_x,
        translate_y,
    )
    return _tools().apply(presentation_id, request, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a text box shape on a slide.",
    examples=['load_tool("google_slides.create_text_box")("presentation-id", "box-id", "slide-id", 300, 80, 72, 72, text="Hello")'],
    tool_class="write",
)
def create_text_box(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    width: float,
    height: float,
    translate_x: float,
    translate_y: float,
    text: Optional[str] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    requests = [
        _tools().create_shape_request(
            object_id,
            page_object_id,
            "TEXT_BOX",
            width,
            height,
            translate_x,
            translate_y,
        )
    ]
    if text:
        requests.append(singleton_request("insertText", {"objectId": object_id, "text": text}))
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create an image on a slide from a URL.",
    examples=['load_tool("google_slides.create_image")("presentation-id", "image-id", "slide-id", "https://example.com/a.png", 300, 200, 72, 72)'],
    tool_class="write",
)
def create_image(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    url: str,
    width: float,
    height: float,
    translate_x: float,
    translate_y: float,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    request = _tools().create_image_request(
        object_id,
        page_object_id,
        url,
        width,
        height,
        translate_x,
        translate_y,
    )
    return _tools().apply(presentation_id, request, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a line on a slide.",
    examples=['load_tool("google_slides.create_line")("presentation-id", "line-id", "slide-id", "STRAIGHT", 72, 72, 300, 72)'],
    tool_class="write",
)
def create_line(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    line_category: str,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    request = _tools().create_line_request(
        object_id,
        page_object_id,
        line_category,
        start_x,
        start_y,
        end_x,
        end_y,
    )
    return _tools().apply(presentation_id, request, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a table on a slide.",
    examples=['load_tool("google_slides.create_table")("presentation-id", "table-id", "slide-id", 3, 4, 400, 160, 72, 72)'],
    tool_class="write",
)
def create_table(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    rows: int,
    columns: int,
    width: float,
    height: float,
    translate_x: float,
    translate_y: float,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    request = _tools().create_table_request(
        object_id,
        page_object_id,
        rows,
        columns,
        width,
        height,
        translate_x,
        translate_y,
    )
    return _tools().apply(presentation_id, request, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Insert text into a shape or table cell.",
    examples=['load_tool("google_slides.insert_text")("presentation-id", "shape-id", "Hello")'],
    tool_class="write",
)
def insert_text(
    presentation_id: str,
    object_id: str,
    text: str,
    insertion_index: Optional[int] = None,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "insertText",
            {
                "objectId": object_id,
                "text": text,
                "insertionIndex": insertion_index,
                "cellLocation": cell_location,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete text from a shape or table cell.",
    examples=['load_tool("google_slides.delete_text")("presentation-id", "shape-id", 0, 5)'],
    tool_class="destructive",
)
def delete_text(
    presentation_id: str,
    object_id: str,
    start_index: int,
    end_index: int,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}
    return _tools().apply(
        presentation_id,
        singleton_request(
            "deleteText",
            {"objectId": object_id, "textRange": text_range, "cellLocation": cell_location},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Replace all matching text in a presentation.",
    examples=['load_tool("google_slides.replace_all_text")("presentation-id", "{{title}}", "Q3")'],
    tool_class="destructive",
)
def replace_all_text(
    presentation_id: str,
    contains_text: str,
    replace_text: str,
    match_case: bool = False,
    page_object_ids: Optional[List[str]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "replaceAllText",
            {
                "containsText": {"text": contains_text, "matchCase": match_case},
                "replaceText": replace_text,
                "pageObjectIds": page_object_ids,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update text style using a Google Slides field mask.",
    examples=['load_tool("google_slides.update_text_style")("presentation-id", "shape-id", {"bold": true}, "bold")'],
    tool_class="write",
)
def update_text_style(
    presentation_id: str,
    object_id: str,
    style: Dict[str, Any],
    fields: str,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    text_range = None
    if start_index is not None and end_index is not None:
        text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateTextStyle",
            {
                "objectId": object_id,
                "style": coerce_dict(style, name="style"),
                "fields": fields,
                "textRange": text_range,
                "cellLocation": cell_location,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update paragraph style using a Google Slides field mask.",
    examples=['load_tool("google_slides.update_paragraph_style")("presentation-id", "shape-id", {"alignment": "CENTER"}, "alignment")'],
    tool_class="write",
)
def update_paragraph_style(
    presentation_id: str,
    object_id: str,
    style: Dict[str, Any],
    fields: str,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    text_range = None
    if start_index is not None and end_index is not None:
        text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateParagraphStyle",
            {
                "objectId": object_id,
                "style": coerce_dict(style, name="style"),
                "fields": fields,
                "textRange": text_range,
                "cellLocation": cell_location,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create paragraph bullets in text.",
    examples=['load_tool("google_slides.create_paragraph_bullets")("presentation-id", "shape-id", "BULLET_DISC_CIRCLE_SQUARE")'],
    tool_class="write",
)
def create_paragraph_bullets(
    presentation_id: str,
    object_id: str,
    bullet_preset: str,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    text_range = None
    if start_index is not None and end_index is not None:
        text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}
    return _tools().apply(
        presentation_id,
        singleton_request(
            "createParagraphBullets",
            {
                "objectId": object_id,
                "bulletPreset": bullet_preset,
                "textRange": text_range,
                "cellLocation": cell_location,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete paragraph bullets from text.",
    examples=['load_tool("google_slides.delete_paragraph_bullets")("presentation-id", "shape-id")'],
    tool_class="destructive",
)
def delete_paragraph_bullets(
    presentation_id: str,
    object_id: str,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    cell_location: Optional[Dict[str, int]] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    text_range = None
    if start_index is not None and end_index is not None:
        text_range = {"type": "FIXED_RANGE", "startIndex": start_index, "endIndex": end_index}
    return _tools().apply(
        presentation_id,
        singleton_request(
            "deleteParagraphBullets",
            {
                "objectId": object_id,
                "textRange": text_range,
                "cellLocation": cell_location,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update page element transform.",
    examples=['load_tool("google_slides.update_transform")("presentation-id", "object-id", 144, 72)'],
    tool_class="write",
)
def update_transform(
    presentation_id: str,
    object_id: str,
    translate_x: float,
    translate_y: float,
    scale_x: float = 1,
    scale_y: float = 1,
    apply_mode: str = "ABSOLUTE",
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updatePageElementTransform",
            {
                "objectId": object_id,
                "transform": transform(
                    translate_x=translate_x,
                    translate_y=translate_y,
                    scale_x=scale_x,
                    scale_y=scale_y,
                ),
                "applyMode": apply_mode,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update object z-order.",
    examples=['load_tool("google_slides.update_z_order")("presentation-id", "object-id", "BRING_TO_FRONT")'],
    tool_class="write",
)
def update_z_order(
    presentation_id: str,
    object_id: str,
    operation: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("updatePageElementZOrder", {"pageElementObjectId": object_id, "operation": operation}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Group multiple page elements.",
    examples=['load_tool("google_slides.group_objects")("presentation-id", ["a", "b"], group_object_id="g")'],
    tool_class="write",
)
def group_objects(
    presentation_id: str,
    children_object_ids: List[str],
    group_object_id: Optional[str] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "groupObjects",
            {"childrenObjectIds": coerce_list(children_object_ids), "groupObjectId": group_object_id},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Ungroup a page element group.",
    examples=['load_tool("google_slides.ungroup_objects")("presentation-id", "group-id")'],
    tool_class="write",
)
def ungroup_objects(
    presentation_id: str,
    group_object_id: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("ungroupObjects", {"objectId": group_object_id}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update a shape's properties using a field mask.",
    examples=['load_tool("google_slides.update_shape_properties")("presentation-id", "shape-id", {"shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 1}}}}}, "shapeBackgroundFill")'],
    tool_class="write",
)
def update_shape_properties(
    presentation_id: str,
    object_id: str,
    shape_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateShapeProperties",
            {"objectId": object_id, "shapeProperties": coerce_dict(shape_properties), "fields": fields},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update an image's properties using a field mask.",
    examples=['load_tool("google_slides.update_image_properties")("presentation-id", "image-id", {"transparency": 0.2}, "transparency")'],
    tool_class="write",
)
def update_image_properties(
    presentation_id: str,
    object_id: str,
    image_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateImageProperties",
            {"objectId": object_id, "imageProperties": coerce_dict(image_properties), "fields": fields},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update a line's properties using a field mask.",
    examples=['load_tool("google_slides.update_line_properties")("presentation-id", "line-id", {"lineFill": {"solidFill": {"color": {"rgbColor": {"blue": 1}}}}}, "lineFill")'],
    tool_class="write",
)
def update_line_properties(
    presentation_id: str,
    object_id: str,
    line_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateLineProperties",
            {"objectId": object_id, "lineProperties": coerce_dict(line_properties), "fields": fields},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update page properties using a field mask.",
    examples=['load_tool("google_slides.update_page_properties")("presentation-id", "slide-id", {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 1}}}}}, "pageBackgroundFill")'],
    tool_class="write",
)
def update_page_properties(
    presentation_id: str,
    object_id: str,
    page_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updatePageProperties",
            {"objectId": object_id, "pageProperties": coerce_dict(page_properties), "fields": fields},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update table cell properties using a field mask.",
    examples=['load_tool("google_slides.update_table_cell_properties")("presentation-id", "table-id", {"rowIndex": 0, "columnIndex": 0}, {"tableCellBackgroundFill": {"solidFill": {"color": {"rgbColor": {"green": 1}}}}}, "tableCellBackgroundFill")'],
    tool_class="write",
)
def update_table_cell_properties(
    presentation_id: str,
    object_id: str,
    table_range: Dict[str, Any],
    table_cell_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateTableCellProperties",
            {
                "objectId": object_id,
                "tableRange": coerce_dict(table_range, name="table_range"),
                "tableCellProperties": coerce_dict(table_cell_properties),
                "fields": fields,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update table border properties using a field mask.",
    examples=['load_tool("google_slides.update_table_border_properties")("presentation-id", "table-id", {"rowIndex": 0, "columnIndex": 0}, "BOTTOM", {"weight": {"magnitude": 1, "unit": "PT"}}, "weight")'],
    tool_class="write",
)
def update_table_border_properties(
    presentation_id: str,
    object_id: str,
    table_range: Dict[str, Any],
    border_position: str,
    table_border_properties: Dict[str, Any],
    fields: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateTableBorderProperties",
            {
                "objectId": object_id,
                "tableRange": coerce_dict(table_range, name="table_range"),
                "borderPosition": border_position,
                "tableBorderProperties": coerce_dict(table_border_properties),
                "fields": fields,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Insert rows into a table.",
    examples=['load_tool("google_slides.insert_table_rows")("presentation-id", "table-id", 1, 2)'],
    tool_class="write",
)
def insert_table_rows(
    presentation_id: str,
    object_id: str,
    row_index: int,
    number: int,
    insert_below: bool = True,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "insertTableRows",
            {"tableObjectId": object_id, "cellLocation": {"rowIndex": row_index, "columnIndex": 0}, "insertBelow": insert_below, "number": number},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Insert columns into a table.",
    examples=['load_tool("google_slides.insert_table_columns")("presentation-id", "table-id", 1, 2)'],
    tool_class="write",
)
def insert_table_columns(
    presentation_id: str,
    object_id: str,
    column_index: int,
    number: int,
    insert_right: bool = True,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "insertTableColumns",
            {"tableObjectId": object_id, "cellLocation": {"rowIndex": 0, "columnIndex": column_index}, "insertRight": insert_right, "number": number},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete a table row.",
    examples=['load_tool("google_slides.delete_table_row")("presentation-id", "table-id", 2)'],
    tool_class="destructive",
)
def delete_table_row(
    presentation_id: str,
    object_id: str,
    row_index: int,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("deleteTableRow", {"tableObjectId": object_id, "cellLocation": {"rowIndex": row_index, "columnIndex": 0}}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Delete a table column.",
    examples=['load_tool("google_slides.delete_table_column")("presentation-id", "table-id", 2)'],
    tool_class="destructive",
)
def delete_table_column(
    presentation_id: str,
    object_id: str,
    column_index: int,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("deleteTableColumn", {"tableObjectId": object_id, "cellLocation": {"rowIndex": 0, "columnIndex": column_index}}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Merge a range of table cells.",
    examples=['load_tool("google_slides.merge_table_cells")("presentation-id", "table-id", {"location": {"rowIndex": 0, "columnIndex": 0}, "rowSpan": 1, "columnSpan": 2})'],
    tool_class="write",
)
def merge_table_cells(
    presentation_id: str,
    object_id: str,
    table_range: Dict[str, Any],
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("mergeTableCells", {"objectId": object_id, "tableRange": coerce_dict(table_range, name="table_range")}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Unmerge a range of table cells.",
    examples=['load_tool("google_slides.unmerge_table_cells")("presentation-id", "table-id", {"location": {"rowIndex": 0, "columnIndex": 0}, "rowSpan": 1, "columnSpan": 2})'],
    tool_class="write",
)
def unmerge_table_cells(
    presentation_id: str,
    object_id: str,
    table_range: Dict[str, Any],
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("unmergeTableCells", {"objectId": object_id, "tableRange": coerce_dict(table_range, name="table_range")}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Replace an image object with a new image URL.",
    examples=['load_tool("google_slides.replace_image")("presentation-id", "image-id", "https://example.com/b.png")'],
    tool_class="destructive",
)
def replace_image(
    presentation_id: str,
    image_object_id: str,
    url: str,
    image_replace_method: str = "CENTER_CROP",
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "replaceImage",
            {"imageObjectId": image_object_id, "url": url, "imageReplaceMethod": image_replace_method},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Replace matching shapes with an image.",
    examples=['load_tool("google_slides.replace_all_shapes_with_image")("presentation-id", "{{logo}}", "https://example.com/logo.png")'],
    tool_class="destructive",
)
def replace_all_shapes_with_image(
    presentation_id: str,
    contains_text: str,
    image_url: str,
    match_case: bool = False,
    page_object_ids: Optional[List[str]] = None,
    replace_method: str = "CENTER_CROP",
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "replaceAllShapesWithImage",
            {
                "containsText": {"text": contains_text, "matchCase": match_case},
                "imageUrl": image_url,
                "pageObjectIds": page_object_ids,
                "replaceMethod": replace_method,
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a linked Sheets chart on a slide.",
    examples=['load_tool("google_slides.create_sheets_chart")("presentation-id", "chart-id", "slide-id", "spreadsheet-id", 123, 400, 260, 72, 72)'],
    tool_class="write",
)
def create_sheets_chart(
    presentation_id: str,
    object_id: str,
    page_object_id: str,
    spreadsheet_id: str,
    chart_id: int,
    width: float,
    height: float,
    translate_x: float,
    translate_y: float,
    linking_mode: str = "LINKED",
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "createSheetsChart",
            {
                "objectId": object_id,
                "spreadsheetId": spreadsheet_id,
                "chartId": chart_id,
                "linkingMode": linking_mode,
                "elementProperties": {
                    "pageObjectId": page_object_id,
                    "size": size(width, height),
                    "transform": transform(translate_x=translate_x, translate_y=translate_y),
                },
            },
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Refresh a linked Sheets chart.",
    examples=['load_tool("google_slides.refresh_sheets_chart")("presentation-id", "chart-id")'],
    tool_class="write",
)
def refresh_sheets_chart(
    presentation_id: str,
    object_id: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request("refreshSheetsChart", {"objectId": object_id}),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Update object alt text title and description.",
    examples=['load_tool("google_slides.update_alt_text")("presentation-id", "object-id", "Logo", "Company logo")'],
    tool_class="write",
)
def update_alt_text(
    presentation_id: str,
    object_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    fields = ",".join(field for field, value in {"title": title, "description": description}.items() if value is not None)
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updatePageElementAltText",
            {"objectId": object_id, "title": title, "description": description},
        ),
        required_revision_id,
    ) if fields else {"updated": False, "reason": "No alt text fields supplied"}


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Reorder slides by object ID order.",
    examples=['load_tool("google_slides.reorder_slides")("presentation-id", ["slide-a", "slide-b"], 0)'],
    tool_class="write",
)
def reorder_slides(
    presentation_id: str,
    slide_object_ids: List[str],
    insertion_index: int,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().apply(
        presentation_id,
        singleton_request(
            "updateSlidesPosition",
            {"slideObjectIds": coerce_list(slide_object_ids), "insertionIndex": insertion_index},
        ),
        required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Apply template text replacements across a deck.",
    examples=['load_tool("google_slides.replace_template_text")("presentation-id", {"{{title}}": "Q3", "{{date}}": "2026"})'],
    tool_class="destructive",
)
def replace_template_text(
    presentation_id: str,
    replacements: Dict[str, str],
    match_case: bool = False,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    requests = [
        singleton_request(
            "replaceAllText",
            {"containsText": {"text": key, "matchCase": match_case}, "replaceText": value},
        )
        for key, value in coerce_dict(replacements, name="replacements").items()
    ]
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a simple title slide with title and subtitle text boxes.",
    examples=['load_tool("google_slides.create_title_slide")("presentation-id", "deck_title", "Revenue Review", subtitle="Q3")'],
    tool_class="write",
)
def create_title_slide(
    presentation_id: str,
    page_object_id: str,
    title: str,
    subtitle: Optional[str] = None,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    title_id = f"{page_object_id}_title"
    subtitle_id = f"{page_object_id}_subtitle"
    requests = [
        _tools().build_slide_request(page_object_id, None, "BLANK"),
        _tools().create_shape_request(title_id, page_object_id, "TEXT_BOX", 560, 80, 72, 120),
        singleton_request("insertText", {"objectId": title_id, "text": title}),
    ]
    if subtitle:
        requests.extend(
            [
                _tools().create_shape_request(subtitle_id, page_object_id, "TEXT_BOX", 560, 60, 72, 220),
                singleton_request("insertText", {"objectId": subtitle_id, "text": subtitle}),
            ]
        )
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Append a text slide with one body text box.",
    examples=['load_tool("google_slides.append_text_slide")("presentation-id", "slide-id", "Some text")'],
    tool_class="write",
)
def append_text_slide(
    presentation_id: str,
    page_object_id: str,
    text: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    box_id = f"{page_object_id}_body"
    requests = [
        _tools().build_slide_request(page_object_id, None, "BLANK"),
        _tools().create_shape_request(box_id, page_object_id, "TEXT_BOX", 560, 320, 72, 72),
        singleton_request("insertText", {"objectId": box_id, "text": text}),
    ]
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Append an image slide with one full-content image.",
    examples=['load_tool("google_slides.append_image_slide")("presentation-id", "slide-id", "image-id", "https://example.com/a.png")'],
    tool_class="write",
)
def append_image_slide(
    presentation_id: str,
    page_object_id: str,
    image_object_id: str,
    url: str,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    requests = [
        _tools().build_slide_request(page_object_id, None, "BLANK"),
        _tools().create_image_request(image_object_id, page_object_id, url, 560, 315, 72, 72),
    ]
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Append a table slide with a blank table.",
    examples=['load_tool("google_slides.append_table_slide")("presentation-id", "slide-id", "table-id", 4, 3)'],
    tool_class="write",
)
def append_table_slide(
    presentation_id: str,
    page_object_id: str,
    table_object_id: str,
    rows: int,
    columns: int,
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    requests = [
        _tools().build_slide_request(page_object_id, None, "BLANK"),
        _tools().create_table_request(table_object_id, page_object_id, rows, columns, 560, 300, 72, 72),
    ]
    return get_client().batch_update(
        presentation_id,
        requests,
        required_revision_id=required_revision_id,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Apply a bulk list of already-built Slides requests.",
    examples=['load_tool("google_slides.bulk_apply_requests")("presentation-id", [{"createSlide": {}}])'],
    tool_class="write",
)
def bulk_apply_requests(
    presentation_id: str,
    requests: List[Dict[str, Any]],
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().batch_update(
        presentation_id,
        normalize_requests(requests),
        required_revision_id=required_revision_id,
    )
