from __future__ import annotations

from nexus_tools_prowlarr.client import ProwlarrClient


def test_build_url_uses_v1_by_default() -> None:
    client = ProwlarrClient(base_url="https://prowlarr.example", api_key="test")

    assert (
        client._build_url("/indexer", None)
        == "https://prowlarr.example/api/v1/indexer"
    )


def test_build_url_can_call_root_paths() -> None:
    client = ProwlarrClient(base_url="https://prowlarr.example", api_key="test")

    assert client._build_url("/ping", "") == "https://prowlarr.example/ping"


def test_request_uses_x_api_key_and_serializes_query(monkeypatch) -> None:
    captured = {}

    class FakeHeaders:
        def get_content_charset(self) -> str:
            return "utf-8"

        def get(self, name: str, default: str = "") -> str:
            if name == "Content-Type":
                return "application/json"
            return default

    class FakeResponse:
        headers = FakeHeaders()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = ProwlarrClient(base_url="https://prowlarr.example", api_key="secret")

    result = client.get(
        "search",
        params={
            "query": "ubuntu iso",
            "indexerIds": [1, 2],
            "interactive": True,
            "unused": None,
        },
    )

    assert result == {"ok": True}
    assert captured["method"] == "GET"
    assert captured["timeout"] == 30.0
    assert captured["headers"]["X-api-key"] == "secret"
    assert captured["url"] == (
        "https://prowlarr.example/api/v1/search"
        "?query=ubuntu+iso&indexerIds=1&indexerIds=2&interactive=true"
    )
