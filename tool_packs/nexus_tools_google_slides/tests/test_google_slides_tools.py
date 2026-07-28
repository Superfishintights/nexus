from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACK_ROOT))

from nexus_tools_google_slides.client import GoogleSlidesClient, set_client_for_tests


class FakeGoogleClient:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def request(
        self,
        service: str,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        call = {
            "service": service,
            "path": path,
            "method": method,
            "params": params,
            "payload": payload,
        }
        self.calls.append(call)
        if path.endswith("/thumbnail"):
            return {"contentUrl": "https://example.test/thumb.png"}
        if path == "presentations/deck":
            return {
                "presentationId": "deck",
                "title": "Deck",
                "revisionId": "rev",
                "slides": [
                    {
                        "objectId": "slide1",
                        "pageElements": [
                            {
                                "objectId": "shape1",
                                "shape": {
                                    "text": {
                                        "textElements": [
                                            {"textRun": {"content": "Hello"}}
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                ],
            }
        return {"ok": True, "path": path, "payload": payload}


def install_fake() -> FakeGoogleClient:
    fake = FakeGoogleClient()
    set_client_for_tests(GoogleSlidesClient(fake))
    return fake


def test_create_presentation_posts_to_slides_v1_service() -> None:
    from nexus_tools_google_slides.presentations import create_presentation

    fake = install_fake()
    result = create_presentation("Deck", "deck")

    assert result["ok"] is True
    assert fake.calls[-1]["service"] == "slides"
    assert fake.calls[-1]["path"] == "presentations"
    assert fake.calls[-1]["method"] == "POST"
    assert fake.calls[-1]["payload"] == {"title": "Deck", "presentationId": "deck"}


def test_batch_update_adds_write_control() -> None:
    from nexus_tools_google_slides.batch_update import batch_update

    fake = install_fake()
    batch_update("deck", [{"createSlide": {}}], required_revision_id="rev")

    assert fake.calls[-1]["path"] == "presentations/deck:batchUpdate"
    assert fake.calls[-1]["payload"] == {
        "requests": [{"createSlide": {}}],
        "writeControl": {"requiredRevisionId": "rev"},
    }


def test_create_text_box_builds_shape_and_insert_requests() -> None:
    from nexus_tools_google_slides.requests import create_text_box

    fake = install_fake()
    create_text_box("deck", "box", "slide1", 300, 80, 72, 72, text="Hello")

    payload = fake.calls[-1]["payload"]
    assert payload["requests"][0]["createShape"]["shapeType"] == "TEXT_BOX"
    assert payload["requests"][1] == {"insertText": {"objectId": "box", "text": "Hello"}}


def test_summary_extracts_slide_and_object_ids() -> None:
    from nexus_tools_google_slides.presentations import get_presentation_summary

    install_fake()
    summary = get_presentation_summary("deck")

    assert summary["slideCount"] == 1
    assert summary["objectIds"] == ["slide1", "shape1"]


def test_thumbnail_uses_official_query_parameter_names() -> None:
    from nexus_tools_google_slides.pages import get_page_thumbnail

    fake = install_fake()
    get_page_thumbnail("deck", "slide1", thumbnail_size="LARGE", mime_type="PNG")

    assert fake.calls[-1]["path"] == "presentations/deck/pages/slide1/thumbnail"
    assert fake.calls[-1]["params"] == {
        "thumbnailProperties.thumbnailSize": "LARGE",
        "thumbnailProperties.mimeType": "PNG",
    }


def test_registered_tool_metadata_is_literal_and_namespaced() -> None:
    modules = [
        PACK_ROOT / "nexus_tools_google_slides" / "presentations.py",
        PACK_ROOT / "nexus_tools_google_slides" / "pages.py",
        PACK_ROOT / "nexus_tools_google_slides" / "batch_update.py",
        PACK_ROOT / "nexus_tools_google_slides" / "requests.py",
    ]
    count = 0
    for module in modules:
        tree = ast.parse(module.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "register_tool":
                continue
            count += 1
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            assert isinstance(keywords.get("namespace"), ast.Constant)
            assert keywords["namespace"].value == "google_slides"
            assert isinstance(keywords.get("description"), ast.Constant)
            assert isinstance(keywords.get("examples"), ast.List)
            assert isinstance(keywords.get("tool_class"), ast.Constant)
            assert keywords["tool_class"].value in {"read", "write", "destructive", "admin"}
    assert count >= 40


def test_tool_classifications_are_explicit_and_conservative() -> None:
    expected = {
        "create_presentation": "write",
        "get_presentation": "read",
        "get_presentation_summary": "read",
        "list_slides": "read",
        "get_revision_id": "read",
        "get_slide_text": "read",
        "get_page": "read",
        "get_page_thumbnail": "read",
        "get_slide_thumbnails": "read",
        "find_page_elements": "read",
        "batch_update": "write",
        "validate_requests": "read",
        "apply_request_bundle": "write",
        "create_slide": "write",
        "delete_object": "destructive",
        "delete_slide": "destructive",
        "duplicate_object": "write",
        "create_shape": "write",
        "create_text_box": "write",
        "create_image": "write",
        "create_line": "write",
        "create_table": "write",
        "insert_text": "write",
        "delete_text": "destructive",
        "replace_all_text": "destructive",
        "update_text_style": "write",
        "update_paragraph_style": "write",
        "create_paragraph_bullets": "write",
        "delete_paragraph_bullets": "destructive",
        "update_transform": "write",
        "update_z_order": "write",
        "group_objects": "write",
        "ungroup_objects": "write",
        "update_shape_properties": "write",
        "update_image_properties": "write",
        "update_line_properties": "write",
        "update_page_properties": "write",
        "update_table_cell_properties": "write",
        "update_table_border_properties": "write",
        "insert_table_rows": "write",
        "insert_table_columns": "write",
        "delete_table_row": "destructive",
        "delete_table_column": "destructive",
        "merge_table_cells": "write",
        "unmerge_table_cells": "write",
        "replace_image": "destructive",
        "replace_all_shapes_with_image": "destructive",
        "create_sheets_chart": "write",
        "refresh_sheets_chart": "write",
        "update_alt_text": "write",
        "reorder_slides": "write",
        "replace_template_text": "destructive",
        "create_title_slide": "write",
        "append_text_slide": "write",
        "append_image_slide": "write",
        "append_table_slide": "write",
        "bulk_apply_requests": "write",
    }
    found = {}
    for module in [
        PACK_ROOT / "nexus_tools_google_slides" / "presentations.py",
        PACK_ROOT / "nexus_tools_google_slides" / "pages.py",
        PACK_ROOT / "nexus_tools_google_slides" / "batch_update.py",
        PACK_ROOT / "nexus_tools_google_slides" / "requests.py",
    ]:
        tree = ast.parse(module.read_text())
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not node.decorator_list:
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Name) or decorator.func.id != "register_tool":
                    continue
                keywords = {keyword.arg: keyword.value for keyword in decorator.keywords}
                found[node.name] = keywords["tool_class"].value
    assert found == expected

    mutating = {name for name, tool_class in expected.items() if tool_class != "read"}
    batch_mutators = {
        "batch_update",
        "apply_request_bundle",
        "create_slide",
        "bulk_apply_requests",
    }
    assert batch_mutators <= mutating
    assert all(found[name] != "read" for name in mutating)
