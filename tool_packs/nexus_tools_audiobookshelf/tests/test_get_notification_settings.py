from __future__ import annotations

from nexus_tools_audiobookshelf import get_notification_settings as notification_settings_module


def test_get_notification_settings_delegates_to_notifications_endpoint(monkeypatch):
    expected = {"events": [{"eventName": "onMediaItemAdded"}], "notifications": []}
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    class FakeClient:
        def get(self, endpoint, *args, **kwargs):
            calls.append((endpoint, args, kwargs))
            return expected

    monkeypatch.setattr(notification_settings_module, "get_client", lambda: FakeClient())

    assert notification_settings_module.get_notification_settings() == expected
    assert calls == [("notifications", (), {})]
