from __future__ import annotations

import urllib.request

from nexus_tools_bazarr.client import BazarrClient, _encode_body, _encode_params


def test_build_url_uses_api_prefix() -> None:
    client = BazarrClient(base_url="localhost:6767", api_key="secret")
    assert client._build_url("system/status") == "http://localhost:6767/api/system/status"


def test_query_encoding_repeats_lists_and_booleans() -> None:
    assert _encode_params({"id[]": [1, 2], "enabled": True, "skip": None}) == "id%5B%5D=1&id%5B%5D=2&enabled=true"


def test_request_uses_bazarr_api_key_header(monkeypatch) -> None:
    captured = {}

    class Response:
        class Headers(dict):
            def get_content_charset(self):
                return "utf-8"

        headers = Headers({"Content-Type": "application/json"})

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = BazarrClient(base_url="http://bazarr.local", api_key="secret", timeout_s=4)
    assert client.patch("movies", params={"radarrid": 9, "action": "scan"}, body={"x": 1}) == {"ok": True}
    assert captured["url"] == "http://bazarr.local/api/movies?radarrid=9&action=scan"
    assert captured["method"] == "PATCH"
    assert captured["headers"]["X-api-key"] == "secret"
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["timeout"] == 4


def test_multipart_body_accepts_file_path(tmp_path) -> None:
    subtitle = tmp_path / "sample.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    body, content_type = _encode_body({"fields": {"language": "en"}, "file": subtitle})
    assert content_type.startswith("multipart/form-data; boundary=")
    assert b'name="language"' in body
    assert b'name="file"; filename="sample.srt"' in body
    assert b"Hi" in body
