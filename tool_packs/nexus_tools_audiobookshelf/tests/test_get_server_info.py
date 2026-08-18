from __future__ import annotations

from nexus_tools_audiobookshelf import get_server_info as server_info_module


def test_get_server_info_posts_to_authorize(monkeypatch):
    expected = {"user": {"id": "user-1"}, "serverVersion": "2.36.0", "settings": {}}
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class FakeClient:
        def post(self, endpoint, *args, **kwargs):
            calls.append((endpoint, args, kwargs))
            return expected

    monkeypatch.setattr(server_info_module, "get_client", lambda: FakeClient())

    assert server_info_module.get_server_info() == expected
    assert calls == [("authorize", (), {})]
