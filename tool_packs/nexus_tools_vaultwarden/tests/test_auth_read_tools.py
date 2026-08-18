from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from nexus import tool_catalog  # noqa: E402
from nexus.tool_registry import clear_registry  # noqa: E402
from nexus_tools_vaultwarden import auth, read  # noqa: E402


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _record(self, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((name, args, kwargs))
        return {"method": name, "args": list(args), "kwargs": kwargs}

    def status(self, **kwargs: Any) -> dict[str, Any]:
        return self._record("status", **kwargs)

    def sync(self, **kwargs: Any) -> dict[str, Any]:
        return self._record("sync", **kwargs)

    def lock(self, **kwargs: Any) -> dict[str, Any]:
        return self._record("lock", **kwargs)

    def find_items(self, **kwargs: Any) -> dict[str, Any]:
        return self._record("find_items", **kwargs)

    def get_item(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._record("get_item", *args, **kwargs)

    def get_secret(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._record("get_secret", *args, **kwargs)

    def get_totp(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._record("get_totp", *args, **kwargs)


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(auth, "get_client", lambda: client)
    monkeypatch.setattr(read, "get_client", lambda: client)
    return client


def test_auth_tools_delegate_to_client(fake_client: FakeClient) -> None:
    assert auth.status() == {"method": "status", "args": [], "kwargs": {"use_session": False}}
    assert auth.status(use_session=True)["kwargs"] == {"use_session": True}
    assert auth.sync()["kwargs"] == {"purpose": "explicit sync"}
    assert auth.sync(purpose="manual refresh")["kwargs"] == {"purpose": "manual refresh"}
    assert auth.lock()["kwargs"] == {"purpose": "explicit lock"}

    assert fake_client.calls == [
        ("status", (), {"use_session": False}),
        ("status", (), {"use_session": True}),
        ("sync", (), {"purpose": "explicit sync"}),
        ("sync", (), {"purpose": "manual refresh"}),
        ("lock", (), {"purpose": "explicit lock"}),
    ]


def test_find_items_default_cap_and_broad_args_pass_through(fake_client: FakeClient) -> None:
    result = read.find_items()

    assert result["method"] == "find_items"
    assert result["kwargs"] == {
        "search": None,
        "url": None,
        "folder_id": None,
        "collection_id": None,
        "organization_id": None,
        "include_trash": False,
        "include_archived": False,
        "item_types": None,
        "limit": 10,
        "allow_all": False,
    }

    read.find_items(
        search="github",
        url="https://github.com",
        folder_id="folder-id",
        collection_id="collection-id",
        organization_id="organization-id",
        include_trash=True,
        include_archived=True,
        item_types=["login"],
        limit=25,
        allow_all=True,
    )

    assert fake_client.calls[-1] == (
        "find_items",
        (),
        {
            "search": "github",
            "url": "https://github.com",
            "folder_id": "folder-id",
            "collection_id": "collection-id",
            "organization_id": "organization-id",
            "include_trash": True,
            "include_archived": True,
            "item_types": ["login"],
            "limit": 25,
            "allow_all": True,
        },
    )


def test_get_item_delegates_selector_and_secret_options(fake_client: FakeClient) -> None:
    result = read.get_item(
        "github",
        include_secret_fields=True,
        field_selectors=["username"],
        purpose="confirm username",
    )

    assert result == {
        "method": "get_item",
        "args": ["github"],
        "kwargs": {
            "include_secret_fields": True,
            "field_selectors": ["username"],
            "purpose": "confirm username",
        },
    }


def test_get_secret_requires_purpose_before_client_call(fake_client: FakeClient) -> None:
    with pytest.raises(ValueError, match="purpose is required"):
        read.get_secret("github", field="password", purpose="")

    assert fake_client.calls == []

    result = read.get_secret("github", field="password", purpose="authenticate cli")

    assert result == {
        "method": "get_secret",
        "args": ["github"],
        "kwargs": {"field": "password", "purpose": "authenticate cli"},
    }


def test_get_totp_requires_purpose_before_client_call(fake_client: FakeClient) -> None:
    with pytest.raises(ValueError, match="purpose is required"):
        read.get_totp("github", purpose="")

    assert fake_client.calls == []

    result = read.get_totp("github", purpose="complete mfa")

    assert result == {
        "method": "get_totp",
        "args": ["github"],
        "kwargs": {"purpose": "complete mfa"},
    }


def test_catalog_discovers_auth_and_read_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(PACK_ROOT))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "nexus_tools_vaultwarden")
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)

    expected = {
        "vaultwarden.status",
        "vaultwarden.sync",
        "vaultwarden.lock",
        "vaultwarden.find_items",
        "vaultwarden.get_item",
        "vaultwarden.get_secret",
        "vaultwarden.get_totp",
    }
    assert expected.issubset(catalog)
    for name in expected:
        assert catalog[name].description
        assert catalog[name].examples
