from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest


PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
sys.path[:0] = [str(REPO_ROOT), str(PACK_ROOT)]

import nexus_tools_agent_memory.phase5_connector.source as source_module  # noqa: E402

from nexus_tools_agent_memory.phase5_connector import (  # noqa: E402
    AgentMemoryConnectorError,
    create_connector,
    load_source,
)


CONNECTOR_DIR = PACK_ROOT / "nexus_tools_agent_memory" / "phase5_connector"
CONTEXT = SimpleNamespace(invocation_id="test", deadline_monotonic=time.monotonic() + 60)


def test_worker_rejects_recomputed_action_authority_tampering(monkeypatch) -> None:
    candidate = json.loads(json.dumps(source_module.SOURCE))
    item = next(tool for tool in candidate["tools"] if tool["identityMapping"]["legacyCanonicalName"] == "agent_memory.forget")
    item["action"]["actionClass"] = "observe"
    item["action"]["reviewerRef"] = "review.forged"
    material = {key: value for key, value in item.items() if key != "revisionDigest"}
    item["revisionDigest"] = source_module._digest(material)
    monkeypatch.setattr(source_module, "SOURCE", candidate)
    with pytest.raises(ValueError, match="pinned reviewed revision"):
        source_module.load_source()


class CountingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address, handler_class):  # noqa: ANN001
        super().__init__(server_address, handler_class)
        self.connection_count = 0
        self.connection_count_lock = threading.Lock()


class CountingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self) -> None:
        super().setup()
        with self.server.connection_count_lock:
            self.server.connection_count += 1

    def do_GET(self) -> None:
        payload = json.dumps({"ok": True, "path": self.path}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format, *args):  # noqa: ANN001
        return


@pytest.fixture
def counting_http_server():
    server = CountingHTTPServer(("127.0.0.1", 0), CountingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class FakeClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        default_profile: str | None,
        default_agent_id: str,
        timeout_s: float,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.default_profile = default_profile
        self.default_agent_id = default_agent_id
        self.timeout_s = timeout_s
        self.calls: list[dict[str, object]] = []
        self.responses: dict[str, object] = {}
        self.closed = False

    def request(
        self,
        method: str,
        path: str,
        *,
        body=None,  # noqa: ANN001
        agent_id=None,  # noqa: ANN001
        require_auth: bool = True,
    ):
        self.calls.append(
            {
                "method": method,
                "path": path,
                "body": body,
                "agentId": agent_id,
                "requireAuth": require_auth,
            }
        )
        response = self.responses.get(path, {"ok": True, "path": path})
        if isinstance(response, Exception):
            raise response
        return response

    def resolve_profile(self, profile):  # noqa: ANN001
        chosen = profile or self.default_profile
        if not chosen:
            raise ValueError("profile is required")
        return chosen

    def close(self) -> None:
        self.closed = True


def configuration(identifier: str = "connection.agent-memory.local") -> dict[str, object]:
    return {
        "connectionId": identifier,
        "endpoint": "https://memory.example",
        "timeoutS": 45,
        "defaultProfile": "jay",
        "defaultAgentId": "nexus-test",
        "nexusSourceRevisionDigest": source_module.EXPECTED_SOURCE_REVISION_DIGEST,
    }


def make_connector(identifier: str = "connection.agent-memory.local"):
    clients: list[FakeClient] = []

    def factory(**kwargs):  # noqa: ANN003
        client = FakeClient(**kwargs)
        clients.append(client)
        return client

    connector = create_connector(
        configuration(identifier),
        {"token": f"secret-{identifier}"},
        client_factory=factory,
    )
    return connector, clients


def test_source_is_exact_versioned_compatibility_evidence() -> None:
    source = load_source()
    assert source["schemaVersion"] == "nexus.phase5.agent-memory-source/v1"
    assert source["counts"] == {"canonical": 8, "aliases": 22, "deprecatedPlaceholders": 0}
    tools = source["tools"]
    names = [item["identityMapping"]["legacyCanonicalName"] for item in tools]
    aliases = [alias for item in tools for alias in item["identityMapping"]["aliases"]]
    assert names == [
        "agent_memory.get_health",
        "agent_memory.get_ready",
        "agent_memory.remember",
        "agent_memory.recall",
        "agent_memory.list_memories",
        "agent_memory.forget",
        "agent_memory.correct",
        "agent_memory.ingest",
    ]
    assert len(names) == len(set(names)) == 8
    assert len(aliases) == len(set(aliases)) == 22
    assert not set(names).intersection(aliases)
    assert next(
        item for item in tools if item["identityMapping"]["legacyCanonicalName"] == "agent_memory.remember"
    )["identityMapping"]["aliases"] == [
        "add_memory", "store_memory", "save_memory", "memorize", "memorise"
    ]
    assert all(item["schemas"]["original"] and item["schemas"]["normalized"] for item in tools)
    assert all("outputSchema" not in item["schemas"]["original"] for item in tools)
    assert all("outputSchema" not in item["schemas"]["normalized"] for item in tools)
    assert all(item["revisionDigest"].startswith("sha256:") for item in tools)


def test_action_metadata_is_manual_exhaustive_and_policy_free() -> None:
    tools = load_source()["tools"]
    by_name = {
        item["identityMapping"]["legacyCanonicalName"]: item["action"] for item in tools
    }
    assert {name: action["actionClass"] for name, action in by_name.items()} == {
        "agent_memory.get_health": "observe",
        "agent_memory.get_ready": "observe",
        "agent_memory.remember": "mutate",
        "agent_memory.recall": "observe",
        "agent_memory.list_memories": "observe",
        "agent_memory.forget": "mutate",
        "agent_memory.correct": "mutate",
        "agent_memory.ingest": "external-effect",
    }
    assert by_name["agent_memory.forget"]["impact"].startswith("destructive")
    assert all(action["reviewed"] is True for action in by_name.values())
    assert all("defaultOutcome" not in action for action in by_name.values())


def test_source_rebuild_is_deterministic_without_editing_legacy_api() -> None:
    source_path = CONNECTOR_DIR / "source.v1.json"
    python_source_path = CONNECTOR_DIR / "source_v1.py"
    api_path = PACK_ROOT / "nexus_tools_agent_memory" / "api.py"
    source_before = hashlib.sha256(source_path.read_bytes()).hexdigest()
    python_source_before = hashlib.sha256(python_source_path.read_bytes()).hexdigest()
    api_before = hashlib.sha256(api_path.read_bytes()).hexdigest()
    completed = subprocess.run(
        [sys.executable, "build_source.py"],
        cwd=CONNECTOR_DIR,
        check=True,
        text=True,
        capture_output=True,
    )
    assert source_before == hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert python_source_before == hashlib.sha256(python_source_path.read_bytes()).hexdigest()
    assert api_before == hashlib.sha256(api_path.read_bytes()).hexdigest()
    assert json.loads(completed.stdout) == {
        "aliases": 22, "canonical": 8, "deprecatedPlaceholders": 0
    }


def test_factory_reuses_one_client_and_resolves_catalogue_names_and_aliases() -> None:
    connector, clients = make_connector()
    assert connector.resolve_name("memorise") == "agent_memory.remember"
    assert connector.resolve_name("agent_memory:recall") == "agent_memory.recall"
    assert connector.resolve_name("list_memories") == "agent_memory.list_memories"
    assert connector.describe("search_memories")["identityMapping"]["legacyCanonicalName"] == (
        "agent_memory.recall"
    )
    connector.invoke("health", {}, CONTEXT)
    connector.invoke("ready", {}, CONTEXT)
    assert len(clients) == 1
    assert connector.diagnostics() == {
        "connectionId": "connection.agent-memory.local",
        "integrationId": "integration.agent-memory",
        "closed": False,
        "canonicalTools": 8,
        "aliases": 22,
    }
    assert [(call["path"], call["requireAuth"]) for call in clients[0].calls] == [
        ("/healthz", False),
        ("/readyz", False),
    ]


def test_fixture_parity_for_all_eight_operations() -> None:
    connector, clients = make_connector()
    connector.invoke("get_health", {}, CONTEXT)
    connector.invoke("get_ready", {}, CONTEXT)
    connector.invoke(
        "remember",
        {
            "content": "deploy host is hermes-agent",
            "scope": "system:hosts",
            "importance": 9,
            "labels": ["deploy"],
            "metadata": {"source": "test"},
            "agent_id": "agent-a",
        },
        CONTEXT,
    )
    connector.invoke(
        "recall",
        {
            "query": "deploy host",
            "scope_filters": ["system:hosts"],
            "mode": "evidence",
            "limit": 3,
        },
        CONTEXT,
    )
    connector.invoke(
        "list_memories",
        {"scope": "system:hosts", "limit": 10, "cursor": "next"},
        CONTEXT,
    )
    connector.invoke(
        "forget",
        {"memory_id": "mem-1", "reason": "obsolete"},
        CONTEXT,
    )
    connector.invoke(
        "correct",
        {
            "memory_id": "mem-2",
            "replacement_content": "deploy host is atlas",
            "replacement_type": "fact",
            "replacement_scope": "system:hosts",
            "replacement_importance": 8,
            "replacement_labels": ["deploy"],
            "replacement_metadata": {"verified": True},
            "reason": "host migrated",
        },
        CONTEXT,
    )
    connector.invoke(
        "ingest",
        {
            "content": "deployment notes",
            "content_type": "text/plain",
            "scope": "docs:deploy",
            "labels": ["notes"],
            "metadata": {"version": 1},
        },
        CONTEXT,
    )
    calls = clients[0].calls
    assert [call["path"] for call in calls] == [
        "/healthz", "/readyz", "/v1/memory/remember", "/v1/memory/recall",
        "/v1/memory/list", "/v1/memory/forget", "/v1/memory/correct", "/v1/memory/ingest",
    ]
    assert calls[2] == {
        "method": "POST",
        "path": "/v1/memory/remember",
        "body": {
            "profile": "jay",
            "type": "fact",
            "content": "deploy host is hermes-agent",
            "source": {"kind": "manual", "title": "Nexus"},
            "scope": "system:hosts",
            "labels": ["deploy"],
            "metadata": {"source": "test"},
            "importance": 9,
        },
        "agentId": "agent-a",
        "requireAuth": True,
    }
    assert calls[3]["body"] == {
        "profile": "jay", "query": "deploy host", "mode": "evidence",
        "scopeFilters": ["system:hosts"], "limit": 3,
    }
    assert calls[4]["body"] == {
        "profile": "jay", "scope": "system:hosts", "limit": 10, "cursor": "next",
    }
    assert calls[5]["body"] == {
        "profile": "jay", "memoryId": "mem-1", "reason": "obsolete",
    }
    assert calls[6]["body"] == {
        "profile": "jay",
        "memoryId": "mem-2",
        "replacement": {
            "type": "fact",
            "content": "deploy host is atlas",
            "source": {"kind": "manual", "title": "Nexus"},
            "scope": "system:hosts",
            "labels": ["deploy"],
            "metadata": {"verified": True},
            "importance": 8,
        },
        "reason": "host migrated",
    }
    assert calls[7]["body"] == {
        "profile": "jay",
        "content": "deployment notes",
        "contentType": "text/plain",
        "source": {"kind": "manual", "title": "Nexus"},
        "scope": "docs:deploy",
        "labels": ["notes"],
        "metadata": {"version": 1},
    }


def test_connections_are_isolated_and_close_releases_each_client() -> None:
    first, first_clients = make_connector("connection.agent-memory.one")
    second, second_clients = make_connector("connection.agent-memory.two")
    first.invoke("get_health", {}, CONTEXT)
    second.invoke("get_health", {}, CONTEXT)
    assert first_clients[0] is not second_clients[0]
    assert first_clients[0].token == "secret-connection.agent-memory.one"
    assert second_clients[0].token == "secret-connection.agent-memory.two"
    first.close()
    assert first_clients[0].closed is True
    assert second_clients[0].closed is False
    with pytest.raises(AgentMemoryConnectorError, match="closed"):
        first.invoke("get_health", {}, CONTEXT)


def test_connector_owned_http_session_reuses_one_tcp_connection(counting_http_server) -> None:
    config = configuration()
    config["endpoint"] = f"http://127.0.0.1:{counting_http_server.server_port}"
    connector = create_connector(config, {"token": "connection-secret"})
    try:
        assert connector.invoke("health", {}, CONTEXT)["path"] == "/healthz"
        assert connector.invoke("ready", {}, CONTEXT)["path"] == "/readyz"
        assert connector.invoke("health", {}, CONTEXT)["path"] == "/healthz"
        assert counting_http_server.connection_count == 1
    finally:
        connector.close()


def test_connector_owned_sessions_are_isolated_between_connections(counting_http_server) -> None:
    endpoint = f"http://127.0.0.1:{counting_http_server.server_port}"
    first_config = configuration("connection.agent-memory.session-one")
    second_config = configuration("connection.agent-memory.session-two")
    first_config["endpoint"] = endpoint
    second_config["endpoint"] = endpoint
    first = create_connector(first_config, {"token": "secret-one"})
    second = create_connector(second_config, {"token": "secret-two"})
    try:
        first.invoke("health", {}, CONTEXT)
        second.invoke("health", {}, CONTEXT)
        first.invoke("ready", {}, CONTEXT)
        second.invoke("ready", {}, CONTEXT)
        assert counting_http_server.connection_count == 2
    finally:
        first.close()
        second.close()


def test_timeout_cancel_json_safety_and_auth_error_redaction() -> None:
    connector, clients = make_connector()
    with pytest.raises(TimeoutError, match="deadline"):
        connector.invoke(
            "get_health", {}, SimpleNamespace(deadline_monotonic=time.monotonic() - 1)
        )
    with pytest.raises(TimeoutError, match="cancelled"):
        connector.invoke("get_health", {}, SimpleNamespace(cancelled=True))
    clients[0].responses["/healthz"] = {"bad": {1, 2}}
    with pytest.raises(AgentMemoryConnectorError, match="non-JSON-safe"):
        connector.invoke("get_health", {}, CONTEXT)
    secret = "never-emit-this-agent-memory-token"
    with pytest.raises(AgentMemoryConnectorError) as exc_info:
        create_connector(
            configuration(),
            {"token": secret},
            client_factory=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError(secret)),
        )
    assert secret not in str(exc_info.value)

    changed = configuration()
    changed["nexusSourceRevisionDigest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="source revision"):
        create_connector(changed, {"token": "safe"})

    with pytest.raises(ValueError, match="only token"):
        create_connector(configuration(), {"token": "ok", "other": secret})
    embedded = configuration()
    embedded["endpoint"] = f"https://user:{secret}@memory.example"
    with pytest.raises(ValueError, match=r"HTTP\(S\)") as exc_info:
        create_connector(embedded, {"token": "ok"})
    assert secret not in str(exc_info.value)
    connector, clients = make_connector()
    clients[0].responses["/v1/memory/recall"] = RuntimeError(secret)
    with pytest.raises(AgentMemoryConnectorError) as exc_info:
        connector.invoke("recall", {"query": "safe"}, CONTEXT)
    assert secret not in str(exc_info.value)


def test_no_legacy_api_import_registration_or_ambient_secret_resolution() -> None:
    adapter_source = (CONNECTOR_DIR / "adapter.py").read_text(encoding="utf-8")
    assert "nexus.tool_registry" not in adapter_source
    assert "from ..api" not in adapter_source
    assert "from ..client" not in adapter_source
    assert "import_module" not in adapter_source
    assert "get_setting" not in adapter_source
    assert "os.environ" not in adapter_source
    assert "registry.register(\"integration.agent-memory\", create_connector)" in adapter_source
    module_source = (CONNECTOR_DIR / "__init__.py").read_text(encoding="utf-8")
    assert "create_registry" in module_source


def test_live_read_only_smoke_is_opt_in_only() -> None:
    # CI and the Phase 5 suite never contact a live service. Reconciliation may
    # add an explicitly configured health/ready smoke using the shared worker.
    assert "AGENT_MEMORY_PHASE5_LIVE" not in json.dumps(load_source())
