from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from nexus_tools_sabnzbd.client import SabnzbdClient


def test_build_url_adds_api_key_output_and_csv_values() -> None:
    client = SabnzbdClient(base_url="localhost:8080", api_key="secret")

    url = client.build_url(
        "queue",
        {"limit": 10, "paused": False, "nzo_ids": ["a", "b"], "skip": None},
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "http"
    assert parsed.netloc == "localhost:8080"
    assert parsed.path == "/api"
    assert query["mode"] == ["queue"]
    assert query["output"] == ["json"]
    assert query["apikey"] == ["secret"]
    assert query["limit"] == ["10"]
    assert query["paused"] == ["0"]
    assert query["nzo_ids"] == ["a,b"]
    assert "skip" not in query


def test_build_url_can_omit_api_key_for_version_and_auth() -> None:
    client = SabnzbdClient(base_url="http://sab.example", api_key="secret")

    url = client.build_url("version", include_api_key=False)

    query = parse_qs(urlparse(url).query)
    assert query["mode"] == ["version"]
    assert "apikey" not in query


def test_request_parses_json_and_plain_text(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SabnzbdClient(base_url="http://sab.example", api_key="secret")

    class Response:
        headers = {"Content-Type": "application/json; charset=utf-8"}

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"status": True}).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())

    assert client.call("pause") == {"status": True}

    class TextResponse(Response):
        headers = {"Content-Type": "text/plain"}

        def read(self) -> bytes:
            return b"5.0.0"

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: TextResponse())

    assert client.call("version", include_api_key=False) == "5.0.0"


def test_request_raises_for_json_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SabnzbdClient(base_url="http://sab.example", api_key="secret")

    class Response:
        headers = {"Content-Type": "application/json"}

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"error": "API Key Incorrect"}'

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())

    with pytest.raises(Exception, match="API Key Incorrect"):
        client.call("queue")


def test_upload_file_uses_multipart_form_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = SabnzbdClient(base_url="http://sab.example", api_key="secret")
    nzb_file = tmp_path / "sample.nzb"
    nzb_file.write_text("<nzb />", encoding="utf-8")
    captured: dict[str, object] = {}

    class Response:
        headers = {"Content-Type": "application/json"}

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"status": true, "nzo_ids": ["SABnzbd_nzo_1"]}'

    def fake_urlopen(request: object, timeout: float) -> Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert client.upload_file("addfile", str(nzb_file), {"cat": "tv"}) == {
        "status": True,
        "nzo_ids": ["SABnzbd_nzo_1"],
    }

    request = captured["request"]
    assert getattr(request, "full_url") == "http://sab.example/api"
    assert b'name="mode"\r\n\r\naddfile' in request.data
    assert b'name="apikey"\r\n\r\nsecret' in request.data
    assert b'name="cat"\r\n\r\ntv' in request.data
    assert b'name="nzbfile"; filename="sample.nzb"' in request.data
    assert request.headers["Content-type"].startswith("multipart/form-data; boundary=")
