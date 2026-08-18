from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from nexus.tool_catalog import scan_file
from nexus.tool_registry import clear_registry, get_tool


ITEMS_PATH = (
    Path(__file__).resolve().parents[1]
    / "nexus_tools_vaultwarden"
    / "items.py"
)


class FakeClient:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, tuple[Any, ...], Dict[str, Any]]] = []

    def _record(self, call_name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append((call_name, args, kwargs))
        return {
            "id": "item-id",
            "name": "safe metadata",
            "login": {"hasPassword": True},
        }

    def build_login_payload(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(("build_login_payload", (), kwargs))
        return {"type": 1, "name": kwargs["name"], "login": {"password": kwargs.get("password")}}

    def build_secure_note_payload(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(("build_secure_note_payload", (), kwargs))
        return {"type": 2, "name": kwargs["name"], "notes": kwargs["notes"], "secureNote": {"type": 0}}

    def build_card_payload(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(("build_card_payload", (), kwargs))
        return {"type": 3, "name": kwargs["name"], "card": {"number": kwargs.get("number")}}

    def build_identity_payload(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(("build_identity_payload", (), kwargs))
        return {"type": 4, "name": kwargs["name"], "identity": kwargs["identity"]}

    def create_item(self, payload: Dict[str, Any], *, purpose: str = "create item") -> Dict[str, Any]:
        return self._record("create_item", payload, purpose=purpose)

    def update_login(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        return self._record("update_login", item_id, purpose=purpose, **updates)

    def update_secure_note(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        return self._record("update_secure_note", item_id, purpose=purpose, **updates)

    def update_card(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        return self._record("update_card", item_id, purpose=purpose, **updates)

    def update_identity(
        self,
        item_id: str,
        *,
        purpose: str,
        identity_updates: Dict[str, Any],
        **updates: Any,
    ) -> Dict[str, Any]:
        return self._record("update_identity", item_id, purpose=purpose, identity_updates=identity_updates, **updates)

    def update_custom_field(
        self,
        item_id: str,
        *,
        name: str,
        value: str | None = None,
        field_type: str = "text",
        purpose: str,
        create_if_missing: bool = True,
    ) -> Dict[str, Any]:
        return self._record(
            "update_custom_field",
            item_id,
            name=name,
            value=value,
            field_type=field_type,
            purpose=purpose,
            create_if_missing=create_if_missing,
        )


@pytest.fixture()
def items_module(monkeypatch: pytest.MonkeyPatch):
    clear_registry()
    sys.modules.pop("nexus_tools_vaultwarden.items", None)
    module = importlib.import_module("nexus_tools_vaultwarden.items")
    client = FakeClient()
    monkeypatch.setattr(module, "get_client", lambda: client)
    yield module, client
    clear_registry()


def test_create_login_builds_payload_and_returns_safe_metadata(items_module: tuple[Any, FakeClient]) -> None:
    items, client = items_module

    result = items.create_login(
        name="Example",
        username="alice",
        password="raw-secret",
        url="https://example.com",
        purpose="store login",
    )

    assert client.calls[0] == (
        "build_login_payload",
        (),
        {
            "name": "Example",
            "username": "alice",
            "password": "raw-secret",
            "uris": None,
            "url": "https://example.com",
            "notes": None,
            "folder_id": None,
            "favorite": False,
            "fields": None,
            "organization_id": None,
            "collection_ids": None,
            "totp": None,
        },
    )
    assert client.calls[1] == (
        "create_item",
        ({"type": 1, "name": "Example", "login": {"password": "raw-secret"}},),
        {"purpose": "store login"},
    )
    assert "raw-secret" not in json.dumps(result)


def test_create_item_passthrough(items_module: tuple[Any, FakeClient]) -> None:
    items, client = items_module
    payload = {"type": 2, "name": "Note", "notes": "secret text", "secureNote": {"type": 0}}

    result = items.create_item(payload, purpose="custom create")

    assert result["id"] == "item-id"
    assert client.calls == [("create_item", (payload,), {"purpose": "custom create"})]


@pytest.mark.parametrize(
    ("tool_name", "kwargs", "builder_name"),
    [
        ("create_secure_note", {"name": "Note", "notes": "secret note", "purpose": "store note"}, "build_secure_note_payload"),
        ("create_card", {"name": "Card", "number": "4111111111111111", "purpose": "store card"}, "build_card_payload"),
        (
            "create_identity",
            {"name": "Identity", "identity": {"email": "a@example.com"}, "purpose": "store identity"},
            "build_identity_payload",
        ),
    ],
)
def test_typed_create_tools_build_payloads(
    items_module: tuple[Any, FakeClient],
    tool_name: str,
    kwargs: Dict[str, Any],
    builder_name: str,
) -> None:
    items, client = items_module

    getattr(items, tool_name)(**kwargs)

    assert client.calls[0][0] == builder_name
    assert client.calls[1][0] == "create_item"
    assert client.calls[1][2] == {"purpose": kwargs["purpose"]}


@pytest.mark.parametrize(
    ("tool_name", "kwargs", "expected_call"),
    [
        (
            "update_login",
            {"username": "bob", "password": "new-secret", "url": "https://example.com"},
            "update_login",
        ),
        ("update_secure_note", {"notes": "new secret note"}, "update_secure_note"),
        ("update_card", {"exp_year": "2030", "code": "123"}, "update_card"),
        ("update_identity", {"identity_updates": {"email": "b@example.com"}}, "update_identity"),
        ("update_custom_field", {"name": "env", "value": "secret-ish", "field_type": "hidden"}, "update_custom_field"),
    ],
)
def test_update_tools_require_purpose_and_passthrough(
    items_module: tuple[Any, FakeClient],
    tool_name: str,
    kwargs: Dict[str, Any],
    expected_call: str,
) -> None:
    items, client = items_module

    with pytest.raises(ValueError, match="purpose is required"):
        getattr(items, tool_name)("00000000-0000-0000-0000-000000000000", purpose="", **kwargs)

    result = getattr(items, tool_name)(
        "00000000-0000-0000-0000-000000000000",
        purpose="documented update",
        **kwargs,
    )

    assert len(client.calls) == 1
    call_name, args, call_kwargs = client.calls[0]
    assert call_name == expected_call
    assert args == ("00000000-0000-0000-0000-000000000000",)
    assert call_kwargs["purpose"] == "documented update"
    for key, value in kwargs.items():
        assert call_kwargs[key] == value
    assert "new-secret" not in json.dumps(result)
    assert "secret-ish" not in json.dumps(result)


def test_registered_tools_are_write_class(items_module: tuple[Any, FakeClient]) -> None:
    expected = {
        "vaultwarden.create_login",
        "vaultwarden.create_secure_note",
        "vaultwarden.create_card",
        "vaultwarden.create_identity",
        "vaultwarden.create_item",
        "vaultwarden.update_login",
        "vaultwarden.update_secure_note",
        "vaultwarden.update_card",
        "vaultwarden.update_identity",
        "vaultwarden.update_custom_field",
    }

    assert {get_tool(name).tool_class for name in expected} == {"write"}


def test_catalog_metadata_is_literal_write_class() -> None:
    specs = scan_file(
        package_name="nexus_tools_vaultwarden",
        package_root=ITEMS_PATH.parent,
        file_path=ITEMS_PATH,
    )

    by_name = {spec.name: spec for spec in specs}
    assert set(by_name) == {
        "vaultwarden.create_login",
        "vaultwarden.create_secure_note",
        "vaultwarden.create_card",
        "vaultwarden.create_identity",
        "vaultwarden.create_item",
        "vaultwarden.update_login",
        "vaultwarden.update_secure_note",
        "vaultwarden.update_card",
        "vaultwarden.update_identity",
        "vaultwarden.update_custom_field",
    }
    assert {spec.tool_class for spec in by_name.values()} == {"write"}
    assert {spec.module for spec in by_name.values()} == {"nexus_tools_vaultwarden.items"}
