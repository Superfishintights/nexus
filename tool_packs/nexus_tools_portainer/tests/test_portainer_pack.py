from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ROOT = REPO_ROOT / "tool_packs" / "nexus_tools_portainer"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACK_ROOT))

from nexus.tool_catalog import scan_package  # noqa: E402
from nexus_tools_portainer.client import PortainerClient  # noqa: E402


class FakeResponse:
    def __init__(self, payload: Any = None, *, content_type: str = "application/json"):
        self.payload = payload
        self.headers = SimpleNamespace(
            get=lambda key, default=None: content_type if key.lower() == "content-type" else default,
            get_content_charset=lambda: "utf-8",
        )

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        if self.payload is None:
            return b""
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


def test_api_key_auth_and_request_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeResponse({"ok": True})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = PortainerClient(base_url="portainer.local", api_key="key-123", timeout_s=12)

    assert client.get("system/version") == {"ok": True}
    assert captured["url"] == "https://portainer.local/api/system/version"
    assert captured["headers"]["X-api-key"] == "key-123"
    assert captured["method"] == "GET"
    assert captured["timeout"] == 12


def test_jwt_login_auth_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        calls.append((request.full_url, request.get_method(), dict(request.header_items())))
        if request.full_url.endswith("/api/auth"):
            return FakeResponse({"jwt": "jwt-token"})
        return FakeResponse({"ok": True})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("nexus_tools_portainer.client.get_setting", lambda *_names: None)
    client = PortainerClient(
        base_url="https://portainer.example",
        username="admin",
        password="secret",
    )

    assert client.get("system/status") == {"ok": True}
    assert client.get("system/version") == {"ok": True}
    assert calls[0][0] == "https://portainer.example/api/auth"
    assert calls[1][2]["Authorization"] == "Bearer jwt-token"
    assert calls[2][2]["Authorization"] == "Bearer jwt-token"
    assert len([call for call in calls if call[0].endswith("/api/auth")]) == 1


def test_docker_proxy_paths_and_container_control(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        captured.append((request.full_url, request.get_method()))
        return FakeResponse(None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = PortainerClient(base_url="https://portainer.example/", api_key="key")

    client.list_containers(7)
    client.inspect_container(7, "plex/container")
    client.control_container("restart", 7, "plex", timeout_s=20)

    assert captured == [
        ("https://portainer.example/api/endpoints/7/docker/containers/json?all=true", "GET"),
        ("https://portainer.example/api/endpoints/7/docker/containers/plex%2Fcontainer/json", "GET"),
        ("https://portainer.example/api/endpoints/7/docker/containers/plex/restart?t=20", "POST"),
    ]


def test_container_search_and_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    containers = [
        {
            "Id": "abc123",
            "Names": ["/plex"],
            "Image": "linuxserver/plex:latest",
            "State": "running",
            "Status": "Up 10 minutes",
            "Labels": {"com.docker.compose.service": "plex"},
        },
        {
            "Id": "def456",
            "Names": ["/postgres"],
            "Image": "postgres:16",
            "State": "running",
            "Status": "Up 10 minutes",
        },
    ]

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        return FakeResponse(containers)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = PortainerClient(base_url="https://portainer.example", api_key="key")

    media = client.list_containers(1, media_only=True)
    assert [item["names"] for item in media] == [["plex"]]
    assert client.resolve_container(1, "plex")["id"] == "abc123"
    assert client.resolve_container(1, "abc")["id"] == "abc123"


def test_catalog_discovers_literal_portainer_metadata() -> None:
    specs = list(scan_package("nexus_tools_portainer", PACK_ROOT / "nexus_tools_portainer"))
    names = {spec.name for spec in specs}

    assert "portainer.get_health" in names
    assert "portainer.list_containers" in names
    assert "portainer.restart_container" in names
    restart = next(spec for spec in specs if spec.name == "portainer.restart_container")
    assert restart.description == "Restart a Docker container through Portainer, optionally with Docker timeout seconds."
    assert restart.examples == ('load_tool("portainer.restart_container")(1, "plex", timeout_s=30)',)
