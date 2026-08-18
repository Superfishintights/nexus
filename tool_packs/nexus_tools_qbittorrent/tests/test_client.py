from __future__ import annotations

import email.message
import sys
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

from nexus_tools_qbittorrent.client import (  # noqa: E402
    QBittorrentClient,
    _encode_params,
    _extract_sid,
    _extract_sid_from_headers,
)


class FakeResponse:
    def __init__(self, body: bytes, headers: dict[str, str] | None = None):
        self.body = body
        self.headers = email.message.Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def _client() -> QBittorrentClient:
    return QBittorrentClient(
        base_url="http://qbit.example",
        username="admin",
        password="secret",
    )


def test_encode_params_uses_qbittorrent_boolean_and_list_forms() -> None:
    assert _encode_params({"enabled": True, "disabled": False, "ids": [1, 2], "skip": None}) == (
        "enabled=true&disabled=false&ids=1&ids=2"
    )


def test_extract_sid_from_set_cookie_header() -> None:
    assert _extract_sid("SID=abc123; path=/; HttpOnly") == "abc123"
    assert _extract_sid("QBT_SID_8080=abc123; path=/; HttpOnly") == "abc123"
    assert _extract_sid("foo=bar") is None


def test_extract_sid_from_multiple_set_cookie_headers() -> None:
    headers = email.message.Message()
    headers.add_header("Set-Cookie", "authelia_session=proxy; path=/")
    headers.add_header("Set-Cookie", "QBT_SID_8080=session-id; path=/")

    assert _extract_sid_from_headers(headers) == "session-id"


def test_login_fails_fast_when_credentials_are_rejected(monkeypatch: Any) -> None:
    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        return FakeResponse(b"Fails.")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    try:
        _client().login()
    except Exception as exc:
        assert str(exc) == "qBittorrent authentication failed: invalid username or password."
    else:
        raise AssertionError("login should fail without a SID cookie")


def test_login_fails_fast_when_sid_cookie_is_missing(monkeypatch: Any) -> None:
    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        return FakeResponse(b"", {"Set-Cookie": "authelia_session=proxy; path=/"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    try:
        _client().login()
    except Exception as exc:
        message = str(exc)
        assert "login response did not include a SID cookie" in message
        assert "reverse proxy/Authelia" in message
    else:
        raise AssertionError("login should fail without a SID cookie")


def test_authenticated_get_logs_in_and_sends_cookie(monkeypatch: Any) -> None:
    calls = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        calls.append((request, timeout))
        if request.full_url.endswith("/api/v2/auth/login"):
            assert request.data == b"username=admin&password=secret"
            assert request.get_method() == "POST"
            return FakeResponse(b"Ok.", {"Set-Cookie": "SID=session-id; path=/"})
        assert request.full_url == "http://localhost:8080/api/v2/torrents/info?filter=downloading"
        assert request.get_method() == "GET"
        assert request.headers["Cookie"] == "SID=session-id"
        return FakeResponse(b"[]", {"Content-Type": "application/json"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = QBittorrentClient(
        base_url="localhost:8080",
        username="admin",
        password="secret",
        timeout_s=5,
    )

    assert client.get("torrents/info", {"filter": "downloading"}) == []
    assert len(calls) == 2


def test_authenticated_get_preserves_qbt_sid_cookie_name(monkeypatch: Any) -> None:
    calls = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        calls.append(request)
        if request.full_url.endswith("/api/v2/auth/login"):
            return FakeResponse(b"", {"Set-Cookie": "QBT_SID_8080=session-id; path=/"})
        assert request.full_url == "http://qbit.example/api/v2/app/version"
        assert request.headers["Cookie"] == "QBT_SID_8080=session-id"
        return FakeResponse(b"v5.0.0", {"Content-Type": "text/plain"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert _client().get("app/version") == "v5.0.0"
    assert len(calls) == 2


def test_form_post_encodes_body_and_cookie(monkeypatch: Any) -> None:
    requests = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        requests.append(request)
        if request.full_url.endswith("/api/v2/auth/login"):
            return FakeResponse(b"Ok.", {"Set-Cookie": "SID=session-id; path=/"})
        assert request.full_url == "http://qbit.example/api/v2/transfer/setDownloadLimit"
        assert request.data == b"limit=1024"
        assert request.headers["Content-type"] == "application/x-www-form-urlencoded"
        assert request.headers["Cookie"] == "SID=session-id"
        return FakeResponse(b"")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = QBittorrentClient(
        base_url="http://qbit.example/",
        username="admin",
        password="secret",
    )

    assert client.post("transfer/setDownloadLimit", {"limit": 1024}) is None
    assert len(requests) == 2
