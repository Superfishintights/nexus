from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACK_ROOT))

from nexus_tools_nzbget.client import NZBGetClient, NZBGetRPCError


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_rpc_call_posts_positional_json_with_basic_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"id": 1, "result": {"ok": True}, "error": None})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = NZBGetClient(
        base_url="http://nzbget.local:6789",
        username="nzbget",
        password="secret",
        timeout_s=12,
    )

    result = client.call("log", [0, 10])

    assert result == {"ok": True}
    assert captured["url"] == "http://nzbget.local:6789/jsonrpc"
    assert captured["timeout"] == 12
    assert captured["body"] == {"method": "log", "params": [0, 10], "id": 1}
    expected_auth = base64.b64encode(b"nzbget:secret").decode("ascii")
    assert captured["headers"]["Authorization"] == f"Basic {expected_auth}"
    assert captured["headers"]["Content-type"] == "application/json"


def test_rpc_url_keeps_explicit_jsonrpc_path() -> None:
    client = NZBGetClient(base_url="https://example.test/nzbget/jsonrpc")

    assert client.rpc_url == "https://example.test/nzbget/jsonrpc"


def test_rpc_error_object_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse({"id": 1, "result": None, "error": {"code": -1, "message": "Nope"}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = NZBGetClient(base_url="http://nzbget.local:6789")

    with pytest.raises(NZBGetRPCError, match="Nope"):
        client.call("status")


def test_requires_both_username_and_password() -> None:
    with pytest.raises(ValueError, match="both NZBGET_USERNAME and NZBGET_PASSWORD"):
        NZBGetClient(base_url="http://nzbget.local:6789", username="nzbget", password="")
