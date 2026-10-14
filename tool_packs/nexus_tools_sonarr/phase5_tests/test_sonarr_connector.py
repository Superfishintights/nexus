from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
sys.path[:0] = [str(REPO_ROOT), str(PACK_ROOT)]

import nexus_tools_sonarr.phase5_connector.source as source_module  # noqa: E402

from nexus_tools_sonarr.phase5_connector import (  # noqa: E402
    PersistentSonarrClient,
    SonarrConnectorError,
    create_connector,
    load_source,
)

CONNECTOR_DIR = PACK_ROOT / "nexus_tools_sonarr" / "phase5_connector"
CONTEXT = SimpleNamespace(invocation_id="test", deadline_monotonic=time.monotonic() + 60)


class FakeClient:
    def __init__(self, *, base_url: str, api_key: str, timeout_s: float) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.calls: list[tuple[str, str, object, object, object]] = []
        self.responses: dict[tuple[str, str], object] = {}

    def _call(self, method, endpoint, *, params=None, body=None, api_path=None):  # noqa: ANN001
        self.calls.append((method, endpoint, params, body, api_path))
        response = self.responses.get((method, endpoint), {"method": method, "endpoint": endpoint})
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, endpoint, params=None, *, api_path=None):  # noqa: ANN001
        return self._call("GET", endpoint, params=params, api_path=api_path)

    def post(self, endpoint, body=None, params=None, *, api_path=None):  # noqa: ANN001
        return self._call("POST", endpoint, params=params, body=body, api_path=api_path)

    def put(self, endpoint, body=None, params=None, *, api_path=None):  # noqa: ANN001
        return self._call("PUT", endpoint, params=params, body=body, api_path=api_path)

    def delete(self, endpoint, params=None, *, api_path=None):  # noqa: ANN001
        return self._call("DELETE", endpoint, params=params, api_path=api_path)

    def head(self, endpoint, params=None, *, api_path=None):  # noqa: ANN001
        return self._call("HEAD", endpoint, params=params, api_path=api_path)


class FakeResponse:
    status = 200
    will_close = False

    def __init__(self, value: object) -> None:
        self.value = value

    def read(self) -> bytes:
        return json.dumps(self.value).encode("utf-8")


class FakePersistentConnection:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str, object, object]] = []
        self.closed = False

    def request(self, method, path, body=None, headers=None):  # noqa: ANN001
        self.requests.append((method, path, body, headers))

    def getresponse(self) -> FakeResponse:
        return FakeResponse({"request": len(self.requests)})

    def close(self) -> None:
        self.closed = True


def configuration(identifier: str = "connection.sonarr.home") -> dict[str, object]:
    return {
        "connectionId": identifier,
        "endpoint": "https://sonarr.example",
        "timeoutS": 45,
        "nexusSourceRevisionDigest": source_module.EXPECTED_SOURCE_REVISION_DIGEST,
    }


def make_connector(identifier: str = "connection.sonarr.home"):
    clients: list[FakeClient] = []

    def factory(**kwargs):  # noqa: ANN003
        client = FakeClient(**kwargs)
        clients.append(client)
        return client

    connector = create_connector(configuration(identifier), {"api-key": f"secret-{identifier}"}, client_factory=factory)
    return connector, clients


def test_source_is_exact_versioned_compatibility_evidence() -> None:
    source = load_source()
    assert source["schemaVersion"] == "nexus.phase5.sonarr-source/v1"
    assert source["counts"] == {"canonical": 222, "aliases": 14, "deprecatedPlaceholders": 6}
    tools = source["tools"]
    names = [item["identityMapping"]["legacyCanonicalName"] for item in tools]
    aliases = [alias for item in tools for alias in item["identityMapping"]["aliases"]]
    assert len(names) == len(set(names)) == 222
    assert len(aliases) == len(set(aliases)) == 14
    assert not set(names).intersection(aliases)
    assert "sonarr.list_season_releases" in names
    assert {"sonarr.lookup_series", "lookup_series"}.issubset(aliases)
    assert all(item["schemas"]["original"] and item["schemas"]["normalized"] for item in tools)
    assert all("outputSchema" not in item["schemas"]["original"] for item in tools)
    assert all("outputSchema" not in item["schemas"]["normalized"] for item in tools)
    assert all(item["revisionDigest"].startswith("sha256:") for item in tools)


def test_action_metadata_is_exhaustive_without_parallel_policy_outcomes() -> None:
    tools = load_source()["tools"]
    by_name = {item["identityMapping"]["legacyCanonicalName"]: item["action"] for item in tools}
    assert len(by_name) == 222
    assert all(action["reviewed"] is True for action in by_name.values())
    assert all("defaultOutcome" not in action for action in by_name.values())
    assert by_name["sonarr.get_release"]["actionClass"] == "observe"
    assert by_name["sonarr.create_series"]["actionClass"] == "mutate"
    assert by_name["sonarr.delete_series_by_id"]["impact"] == "destructive"
    assert by_name["sonarr.create_system_shutdown"]["actionClass"] == "administer"


def test_source_rebuild_is_deterministic() -> None:
    path = CONNECTOR_DIR / "source.v1.json"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    completed = subprocess.run([sys.executable, "build_source.py"], cwd=CONNECTOR_DIR, check=True, text=True, capture_output=True)
    assert before == hashlib.sha256(path.read_bytes()).hexdigest()
    assert json.loads(completed.stdout)["canonical"] == 222


def test_worker_load_rejects_tool_identity_and_count_tampering(tmp_path, monkeypatch) -> None:
    pristine = json.loads((CONNECTOR_DIR / "source.v1.json").read_text(encoding="utf-8"))

    def rejected(candidate, match):  # noqa: ANN001
        path = tmp_path / "source.v1.json"
        path.write_text(json.dumps(candidate), encoding="utf-8")
        monkeypatch.setattr(source_module, "SOURCE_PATH", path)
        source_module.load_source.cache_clear()
        with pytest.raises(ValueError, match=match):
            source_module.load_source()

    tool_tamper = json.loads(json.dumps(pristine))
    tool_tamper["tools"][0]["description"] = "tampered in worker"
    rejected(tool_tamper, "pinned reviewed revision")

    identity_tamper = json.loads(json.dumps(pristine))
    item = next(tool for tool in identity_tamper["tools"] if tool["identityMapping"]["aliases"])
    item["identityMapping"]["aliases"][0] = "forged-alias"
    material = {key: value for key, value in item.items() if key != "revisionDigest"}
    item["revisionDigest"] = source_module._digest(material)
    rejected(identity_tamper, "pinned reviewed revision")

    count_tamper = json.loads(json.dumps(pristine))
    count_tamper["counts"]["canonical"] = 221
    rejected(count_tamper, "pinned reviewed revision")

    action_tamper = json.loads(json.dumps(pristine))
    item = next(tool for tool in action_tamper["tools"] if tool["identityMapping"]["legacyCanonicalName"] == "sonarr.delete_series_by_id")
    item["action"]["actionClass"] = "observe"
    item["action"]["reviewerRef"] = "review.forged"
    material = {key: value for key, value in item.items() if key != "revisionDigest"}
    item["revisionDigest"] = source_module._digest(material)
    rejected(action_tamper, "pinned reviewed revision")
    source_module.load_source.cache_clear()


def test_worker_factory_shape_reuses_one_client_and_preserves_aliases() -> None:
    connector, clients = make_connector()
    assert connector.invoke("sonarr.lookup_series", {"params": {"term": "Firefly"}}, CONTEXT) == {
        "method": "GET", "endpoint": "series/lookup"
    }
    assert connector.invoke("get_series_by_id", {"id": 42}, CONTEXT) == {
        "method": "GET", "endpoint": "series/42"
    }
    assert connector.resolve_name("lookup_series") == "sonarr.get_series_lookup"
    assert connector.diagnostics() == {
        "connectionId": "connection.sonarr.home", "integrationId": "integration.sonarr",
        "closed": False, "canonicalTools": 222, "aliases": 14,
    }
    assert len(clients) == 1
    assert [call[:2] for call in clients[0].calls] == [("GET", "series/lookup"), ("GET", "series/42")]


def test_concurrent_connection_factories_are_isolated() -> None:
    first, first_clients = make_connector("connection.sonarr.one")
    second, second_clients = make_connector("connection.sonarr.two")
    first.invoke("get_health", {}, CONTEXT)
    second.invoke("get_health", {}, CONTEXT)
    assert first_clients[0] is not second_clients[0]
    assert first_clients[0].api_key == "secret-connection.sonarr.one"
    assert second_clients[0].api_key == "secret-connection.sonarr.two"


def test_persistent_http_session_is_reused_and_isolated_per_connection() -> None:
    created: list[FakePersistentConnection] = []

    def connection_factory(_parsed, _timeout):  # noqa: ANN001
        connection = FakePersistentConnection()
        created.append(connection)
        return connection

    first = PersistentSonarrClient(
        "https://sonarr-one.example",
        "first-secret",
        connection_factory=connection_factory,
    )
    second = PersistentSonarrClient(
        "https://sonarr-two.example",
        "second-secret",
        connection_factory=connection_factory,
    )
    assert first.get("health") == {"request": 1}
    assert first.get("series", params={"monitored": True}) == {"request": 2}
    assert second.get("health") == {"request": 1}
    assert (first.connection_count, first.request_count) == (1, 2)
    assert (second.connection_count, second.request_count) == (1, 1)
    assert len(created) == 2
    assert created[0] is not created[1]
    assert created[0].requests[0][3]["X-Api-Key"] == "first-secret"
    assert created[1].requests[0][3]["X-Api-Key"] == "second-secret"
    first.close()
    second.close()
    assert all(connection.closed for connection in created)


def test_generated_rest_fixture_parity() -> None:
    connector, clients = make_connector()
    assert connector.invoke("get_wanted_missing", {"params": {"page": 2}}, CONTEXT)["endpoint"] == "wanted/missing"
    assert connector.invoke("sonarr.add_series", {"body": {"title": "Firefly"}}, CONTEXT)["endpoint"] == "series"
    assert connector.invoke("sonarr.run_command", {"body": {"name": "MissingEpisodeSearch"}}, CONTEXT)["endpoint"] == "command"
    assert clients[0].calls == [
        ("GET", "wanted/missing", {"page": 2}, None, "/api/v3"),
        ("POST", "series", None, {"title": "Firefly"}, "/api/v3"),
        ("POST", "command", None, {"name": "MissingEpisodeSearch"}, "/api/v3"),
    ]


def test_compact_release_helper_fixture_parity() -> None:
    connector, clients = make_connector()
    clients[0].responses[("GET", "series")] = [{"id": 220, "title": "Game of Thrones"}]
    clients[0].responses[("GET", "release")] = [
        {
            "title": "Game.of.Thrones.S06.1080p.BluRay-GROUP",
            "quality": {"quality": {"name": "Bluray-1080p", "source": "bluray", "resolution": 1080}},
            "customFormatScore": 25, "size": 5368709120, "indexer": "Indexer A",
            "fullSeason": True, "rejected": False, "downloadAllowed": True, "age": 12, "seeders": 14,
        },
        {"title": "rejected", "customFormatScore": 40, "fullSeason": True, "rejected": True},
        {"title": "episode", "customFormatScore": 30, "fullSeason": False, "rejected": False},
    ]
    result = connector.invoke(
        "list_season_releases",
        {"series_title": "Game of Thrones", "season_number": 6, "quality_contains": "1080p", "positive_score_only": True},
        CONTEXT,
    )
    assert (result["seriesId"], result["totalReleases"], result["totalFiltered"]) == (220, 3, 1)
    assert result["releases"][0]["sizeHuman"] == "5.00 GiB"


def test_deadline_json_safety_and_auth_error_redaction() -> None:
    connector, clients = make_connector()
    with pytest.raises(TimeoutError):
        connector.invoke("get_health", {}, SimpleNamespace(deadline_monotonic=time.monotonic() - 1))
    clients[0].responses[("GET", "health")] = {"bad": {1, 2}}
    with pytest.raises(SonarrConnectorError, match="non-JSON-safe"):
        connector.invoke("get_health", {}, CONTEXT)
    secret = "never-emit-this-api-key"
    with pytest.raises(SonarrConnectorError) as exc_info:
        create_connector(configuration(), {"api-key": secret}, client_factory=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError(secret)))
    assert secret not in str(exc_info.value)
    changed = configuration()
    changed["nexusSourceRevisionDigest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="source revision"):
        create_connector(changed, {"api-key": "safe"})


def test_no_generated_pack_import_or_import_time_registration() -> None:
    source = (CONNECTOR_DIR / "adapter.py").read_text(encoding="utf-8")
    assert "import_module" not in source
    assert "nexus.tool_registry" not in source
    assert "from ..get_" not in source
    assert "from ..create_" not in source
    assert "registry.register" in source  # only inside explicit create_registry()
