from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

import pytest

from nexus_tools_google_forms import builders, forms, responses, watches


PACKAGE_DIR = Path(__file__).resolve().parents[1] / "nexus_tools_google_forms"

EXPECTED_TOOLS = {
    "batch_update_form",
    "build_choice_question_item",
    "build_create_item_request",
    "build_date_question_item",
    "build_delete_item_request",
    "build_move_item_request",
    "build_page_break_item",
    "build_rating_question_item",
    "build_scale_question_item",
    "build_text_item",
    "build_text_question_item",
    "build_time_question_item",
    "build_update_form_info_request",
    "build_update_item_request",
    "build_update_settings_request",
    "create_form",
    "create_watch",
    "delete_watch",
    "get_form",
    "get_response",
    "list_all_responses",
    "list_responses",
    "list_watches",
    "renew_watch",
    "request",
    "set_publish_settings",
}

EXPECTED_TOOL_CLASSES = {
    "batch_update_form": "write",
    "build_choice_question_item": "utility",
    "build_create_item_request": "utility",
    "build_date_question_item": "utility",
    "build_delete_item_request": "utility",
    "build_move_item_request": "utility",
    "build_page_break_item": "utility",
    "build_rating_question_item": "utility",
    "build_scale_question_item": "utility",
    "build_text_item": "utility",
    "build_text_question_item": "utility",
    "build_time_question_item": "utility",
    "build_update_form_info_request": "utility",
    "build_update_item_request": "utility",
    "build_update_settings_request": "utility",
    "create_form": "write",
    "create_watch": "write",
    "delete_watch": "destructive",
    "get_form": "read",
    "get_response": "read",
    "list_all_responses": "read",
    "list_responses": "read",
    "list_watches": "read",
    "renew_watch": "write",
    "request": "admin",
    "set_publish_settings": "write",
}


class FakeClient:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.pages = [
            {"responses": [{"responseId": "r1"}], "nextPageToken": "p2"},
            {"responses": [{"responseId": "r2"}]},
        ]

    def request(self, service: str, path: str, *, method: str = "GET", params: Any = None, payload: Any = None) -> Dict[str, Any]:
        self.calls.append({"service": service, "path": path, "method": method, "params": params, "payload": payload})
        if path.endswith("/responses") and method == "GET":
            return self.pages.pop(0)
        return {"service": service, "path": path, "method": method, "params": params, "payload": payload}


@pytest.fixture()
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr("nexus_tools_google_forms.client.get_client", lambda: client)
    return client


def _registered_tools() -> Dict[str, Dict[str, Any]]:
    tools: Dict[str, Dict[str, Any]] = {}
    for path in PACKAGE_DIR.glob("*.py"):
        if path.name.startswith("test_"):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if not (isinstance(func, ast.Name) and func.id == "register_tool"):
                    continue
                metadata: Dict[str, Any] = {}
                for keyword in decorator.keywords:
                    if isinstance(keyword.value, ast.Constant):
                        metadata[keyword.arg or ""] = keyword.value.value
                    elif isinstance(keyword.value, ast.List):
                        metadata[keyword.arg or ""] = ast.literal_eval(keyword.value)
                tools[node.name] = metadata
    return tools


def test_expected_tool_catalog_is_literal_google_forms_namespace() -> None:
    tools = _registered_tools()
    assert set(tools) == EXPECTED_TOOLS
    assert {metadata["namespace"] for metadata in tools.values()} == {"google_forms"}
    assert all("description" in metadata for metadata in tools.values())
    assert all("examples" in metadata for metadata in tools.values())
    assert all("tool_class" in metadata for metadata in tools.values())


def test_tool_classes_are_explicit_and_security_accurate() -> None:
    tools = _registered_tools()
    assert {name: metadata["tool_class"] for name, metadata in tools.items()} == EXPECTED_TOOL_CLASSES


def test_create_and_get_form_paths(fake_client: FakeClient) -> None:
    result = forms.create_form("Survey", document_title="Doc", unpublished=True)
    assert result["service"] == "forms"
    assert result["path"] == "forms"
    assert result["method"] == "POST"
    assert result["params"] == {"unpublished": True}
    assert result["payload"] == {"info": {"title": "Survey", "documentTitle": "Doc"}}

    forms.get_form("id with space")
    assert fake_client.calls[-1]["path"] == "forms/id%20with%20space"


def test_batch_update_write_control(fake_client: FakeClient) -> None:
    request = builders.build_update_form_info_request(description="New")
    forms.batch_update_form("form", [request], include_form_in_response=True, required_revision_id="rev")
    assert fake_client.calls[-1]["path"] == "forms/form:batchUpdate"
    assert fake_client.calls[-1]["payload"] == {
        "requests": [request],
        "includeFormInResponse": True,
        "writeControl": {"requiredRevisionId": "rev"},
    }


def test_batch_update_rejects_conflicting_revision_controls() -> None:
    with pytest.raises(ValueError):
        forms.batch_update_form("form", [], required_revision_id="a", target_revision_id="b")


def test_publish_settings_accept_responses_payload(fake_client: FakeClient) -> None:
    forms.set_publish_settings("form", accept_responses=False)
    assert fake_client.calls[-1]["path"] == "forms/form:setPublishSettings"
    assert fake_client.calls[-1]["payload"] == {
        "publishState": {"isPublished": True, "isAcceptingResponses": False}
    }


def test_responses_paths_and_all_pages(fake_client: FakeClient) -> None:
    all_responses = responses.list_all_responses("form", filter='timestamp >= "2026-07-01T00:00:00Z"')
    assert all_responses == {
        "responses": [{"responseId": "r1"}, {"responseId": "r2"}],
        "nextPageToken": None,
        "pageCount": 2,
        "responseCount": 2,
    }
    assert fake_client.calls[0]["params"]["pageSize"] == 5000
    assert fake_client.calls[1]["params"]["pageToken"] == "p2"

    responses.get_response("form id", "response id")
    assert fake_client.calls[-1]["path"] == "forms/form%20id/responses/response%20id"


def test_watch_payload_and_paths(fake_client: FakeClient) -> None:
    watches.create_watch("form", "RESPONSES", "projects/p/topics/t", watch_id="watch-id")
    assert fake_client.calls[-1]["payload"] == {
        "watch": {
            "eventType": "RESPONSES",
            "target": {"topic": {"topicName": "projects/p/topics/t"}},
        },
        "watchId": "watch-id",
    }

    watches.renew_watch("form", "watch id")
    assert fake_client.calls[-1]["path"] == "forms/form/watches/watch%20id:renew"
    assert fake_client.calls[-1]["payload"] == {}

    watches.delete_watch("form", "watch id")
    assert fake_client.calls[-1]["method"] == "DELETE"


def test_question_and_request_builders() -> None:
    item = builders.build_choice_question_item("Pick", ["A", {"value": "B"}], required=True, shuffle=True)
    assert item == {
        "title": "Pick",
        "questionItem": {
            "question": {
                "required": True,
                "choiceQuestion": {
                    "type": "RADIO",
                    "options": [{"value": "A"}, {"value": "B"}],
                    "shuffle": True,
                },
            }
        },
    }
    assert builders.build_create_item_request(item, index=0) == {"createItem": {"item": item, "location": {"index": 0}}}
    assert builders.build_delete_item_request("item") == {"deleteItem": {"itemId": "item"}}
    assert builders.build_move_item_request("item", new_index=3) == {
        "moveItem": {"originalLocation": {"itemId": "item"}, "newLocation": {"index": 3}}
    }


def test_static_and_settings_builders() -> None:
    assert builders.build_text_question_item("Name", paragraph=True)["questionItem"]["question"]["textQuestion"] == {
        "paragraph": True
    }
    assert builders.build_scale_question_item("Rate", low=1, high=5)["questionItem"]["question"]["scaleQuestion"] == {
        "low": 1,
        "high": 5,
    }
    assert builders.build_date_question_item("Date")["questionItem"]["question"]["dateQuestion"]["includeYear"] is True
    assert builders.build_time_question_item("Time")["questionItem"]["question"]["timeQuestion"] == {"duration": False}
    assert builders.build_rating_question_item("Rating", rating_scale_level=5)["questionItem"]["question"]["ratingQuestion"] == {
        "ratingScaleLevel": 5,
        "iconType": "STAR",
    }
    assert builders.build_text_item("Intro") == {"title": "Intro", "textItem": {}}
    assert builders.build_page_break_item("Section") == {"title": "Section", "pageBreakItem": {}}
    assert builders.build_update_settings_request(is_quiz=True) == {
        "updateSettings": {"settings": {"quizSettings": {"isQuiz": True}}, "updateMask": "quizSettings"}
    }
