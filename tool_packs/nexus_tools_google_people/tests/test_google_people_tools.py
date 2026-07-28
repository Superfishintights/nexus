from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

import pytest

from nexus_tools_google_people import contact_groups, other_contacts, people


PACKAGE_DIR = Path(__file__).resolve().parents[1] / "nexus_tools_google_people"


EXPECTED_TOOLS = {
    "batch_create_contacts",
    "batch_delete_contacts",
    "batch_get_contact_groups",
    "batch_get_people",
    "batch_update_contacts",
    "copy_other_contact_to_my_contacts",
    "create_contact",
    "create_contact_group",
    "delete_contact",
    "delete_contact_group",
    "delete_contact_photo",
    "get_contact_group",
    "get_person",
    "list_connections",
    "list_contact_groups",
    "list_directory_people",
    "list_other_contacts",
    "modify_contact_group_members",
    "search_contacts",
    "search_directory_people",
    "search_other_contacts",
    "update_contact",
    "update_contact_group",
    "update_contact_photo",
}


EXPECTED_TOOL_CLASSES = {
    "batch_create_contacts": "write",
    "batch_delete_contacts": "destructive",
    "batch_get_contact_groups": "read",
    "batch_get_people": "read",
    "batch_update_contacts": "write",
    "copy_other_contact_to_my_contacts": "write",
    "create_contact": "write",
    "create_contact_group": "write",
    "delete_contact": "destructive",
    "delete_contact_group": "destructive",
    "delete_contact_photo": "destructive",
    "get_contact_group": "read",
    "get_person": "read",
    "list_connections": "read",
    "list_contact_groups": "read",
    "list_directory_people": "read",
    "list_other_contacts": "read",
    "modify_contact_group_members": "write",
    "search_contacts": "read",
    "search_directory_people": "read",
    "search_other_contacts": "read",
    "update_contact": "write",
    "update_contact_group": "write",
    "update_contact_photo": "write",
}


def _registered_tools() -> Dict[str, Dict[str, str]]:
    tools: Dict[str, Dict[str, str]] = {}
    for path in PACKAGE_DIR.glob("*.py"):
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
                metadata = {"namespace": "", "tool_class": ""}
                for keyword in decorator.keywords:
                    if keyword.arg == "namespace" and isinstance(keyword.value, ast.Constant):
                        metadata["namespace"] = str(keyword.value.value)
                    if keyword.arg == "tool_class" and isinstance(keyword.value, ast.Constant):
                        metadata["tool_class"] = str(keyword.value.value)
                tools[node.name] = metadata
    return tools


def test_expected_tool_catalog_has_literal_namespace_and_tool_class() -> None:
    tools = _registered_tools()
    assert set(tools) == EXPECTED_TOOLS
    assert {metadata["namespace"] for metadata in tools.values()} == {"google_people"}
    assert {name: metadata["tool_class"] for name, metadata in tools.items()} == EXPECTED_TOOL_CLASSES


def test_quote_resource_name_preserves_people_resource_slash() -> None:
    assert people.quote_resource_name("people/c123") == "people/c123"
    assert people.quote_resource_name("contactGroups/my Contacts") == "contactGroups/my%20Contacts"


def test_get_person_uses_resource_name_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(people, "request_people", fake_request)
    assert people.get_person("people/c123", person_fields="names") == {"ok": True}
    assert calls == [{"path": "people/c123", "params": {"personFields": "names"}}]


def test_update_contact_builds_mask_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(people, "request_people", fake_request)
    person = {"etag": "abc", "names": [{"givenName": "Ada"}]}
    people.update_contact("people/c123", person, update_person_fields="names", person_fields="names")
    assert calls[0]["path"] == "people/c123:updateContact"
    assert calls[0]["method"] == "PATCH"
    assert calls[0]["params"]["updatePersonFields"] == "names"
    assert calls[0]["payload"] == person


def test_batch_update_contacts_body(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(people, "request_people", fake_request)
    contacts = {"people/c123": {"etag": "abc", "names": [{"givenName": "Ada"}]}}
    people.batch_update_contacts(contacts, update_mask="names", read_mask="names")
    assert calls[0]["path"] == "people:batchUpdateContacts"
    assert calls[0]["payload"] == {
        "contacts": contacts,
        "updateMask": "names",
        "readMask": "names",
    }


def test_contact_group_members_path_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(contact_groups, "request_people", fake_request)
    contact_groups.modify_contact_group_members(
        "contactGroups/friends",
        add_resource_names=["people/c123"],
        remove_resource_names=["people/c456"],
    )
    assert calls[0] == {
        "path": "contactGroups/friends/members:modify",
        "method": "POST",
        "payload": {
            "resourceNamesToAdd": ["people/c123"],
            "resourceNamesToRemove": ["people/c456"],
        },
    }


def test_other_contact_copy_path_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_request(path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append({"path": path, **kwargs})
        return {"ok": True}

    monkeypatch.setattr(other_contacts, "request_people", fake_request)
    other_contacts.copy_other_contact_to_my_contacts(
        "otherContacts/c123",
        copy_mask="names,emailAddresses",
        read_mask="names",
    )
    assert calls[0] == {
        "path": "otherContacts/c123:copyOtherContactToMyContactsGroup",
        "method": "POST",
        "params": {},
        "payload": {"copyMask": "names,emailAddresses", "readMask": "names"},
    }
