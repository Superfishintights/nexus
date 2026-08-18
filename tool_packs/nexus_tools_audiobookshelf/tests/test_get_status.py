"""Tests for the registered Audiobookshelf status tool."""

from __future__ import annotations

import inspect

from nexus_tools_audiobookshelf import get_status as get_status_module


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def get(self, *args, **kwargs):
        self.calls.append((*args, kwargs))
        return {"isInit": True}


def test_get_status_delegates_without_arguments(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(get_status_module, "get_client", lambda: client)

    assert inspect.signature(get_status_module.get_status).parameters == {}
    assert get_status_module.get_status() == {"isInit": True}
    assert client.calls == [("status", {"api_path": "", "authenticated": False})]
