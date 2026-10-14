from __future__ import annotations

import importlib
import inspect
import sys
import types

import nexus.tool_registry


def test_declares_exact_runtime_tools(monkeypatch) -> None:
    captured = []

    def register_tool(**metadata):
        def decorator(func):
            captured.append((func.__name__, metadata))
            return func

        return decorator

    registry = types.ModuleType("nexus.tool_registry")
    registry.register_tool = register_tool
    monkeypatch.setitem(sys.modules, "nexus.tool_registry", registry)
    monkeypatch.setattr(nexus.tool_registry, "register_tool", register_tool)
    sys.modules.pop("nexus_tools_agent_blackboard.api", None)

    importlib.import_module("nexus_tools_agent_blackboard.api")

    assert {name for name, _metadata in captured} == {
        "get_or_create_identity",
        "register_actor",
        "search_topics",
        "find_or_create_topic",
        "read_topic",
        "post_message",
        "claim_work",
        "release_work",
        "post_handoff",
        "link_artifact",
        "poll_inbox",
        "propose_doc_revision",
        "get_run_status",
    }
    assert len(captured) == 13
    assert all(metadata["namespace"] == "agent_blackboard" for _name, metadata in captured)
    assert all(metadata["aliases"] == [] for _name, metadata in captured)
    assert all(metadata["tool_class"] in {"read", "write"} for _name, metadata in captured)
    metadata_by_name = dict(captured)
    assert "free-form Markdown" in metadata_by_name["post_message"]["description"]
    assert "natural-language Markdown" in metadata_by_name["post_handoff"]["description"]
    assert "body_md is the human conversation" in metadata_by_name["propose_doc_revision"]["description"]


def test_register_actor_keeps_session_token_in_client_memory(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_BLACKBOARD_BASE_URL", "http://blackboard.test")
    monkeypatch.setenv("AGENT_BLACKBOARD_BOOTSTRAP_TOKEN", "bootstrap-token")
    session_file = tmp_path / "session.token"
    monkeypatch.setenv("AGENT_BLACKBOARD_SESSION_TOKEN_FILE", str(session_file))

    from nexus_tools_agent_blackboard.client import AgentBlackboardClient

    client = AgentBlackboardClient()
    client.write_session_token("session-token")

    assert client.session_token == "session-token"
    assert session_file.read_text(encoding="utf-8").strip() == "session-token"
    assert oct(session_file.stat().st_mode & 0o777) == "0o600"


def test_session_token_file_is_optional_after_registration(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_BLACKBOARD_BASE_URL", "http://blackboard.test")
    monkeypatch.delenv("AGENT_BLACKBOARD_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("AGENT_BLACKBOARD_SESSION_TOKEN_FILE", raising=False)

    from nexus_tools_agent_blackboard.client import AgentBlackboardClient

    client = AgentBlackboardClient()
    client.write_session_token("session-token")

    assert client.session_token == "session-token"


def test_session_request_rereads_shared_session_token_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_BLACKBOARD_BASE_URL", "http://blackboard.test")
    monkeypatch.delenv("AGENT_BLACKBOARD_SESSION_TOKEN", raising=False)
    session_file = tmp_path / "session.token"
    monkeypatch.setenv("AGENT_BLACKBOARD_SESSION_TOKEN_FILE", str(session_file))

    from nexus_tools_agent_blackboard.client import AgentBlackboardClient

    first_worker = AgentBlackboardClient()
    second_worker = AgentBlackboardClient()
    captured_tokens: list[str | None] = []

    def capture_request(self, method, path, *, body=None, params=None, token=None):
        captured_tokens.append(token)
        return {"ok": True}

    monkeypatch.setattr(AgentBlackboardClient, "request", capture_request)

    first_worker.write_session_token("old-token")
    second_worker.session_request("GET", "/v1/topics")

    first_worker.write_session_token("new-token")
    second_worker.session_request("GET", "/v1/topics")

    assert captured_tokens == ["old-token", "new-token"]


def test_session_request_falls_back_to_memory_when_session_file_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AGENT_BLACKBOARD_BASE_URL", "http://blackboard.test")
    monkeypatch.delenv("AGENT_BLACKBOARD_SESSION_TOKEN", raising=False)
    monkeypatch.setenv("AGENT_BLACKBOARD_SESSION_TOKEN_FILE", str(tmp_path / "missing.token"))

    from nexus_tools_agent_blackboard.client import AgentBlackboardClient

    client = AgentBlackboardClient()
    client.session_token = "just-issued-token"
    captured_tokens: list[str | None] = []

    def capture_request(self, method, path, *, body=None, params=None, token=None):
        captured_tokens.append(token)
        return {"ok": True}

    monkeypatch.setattr(AgentBlackboardClient, "request", capture_request)

    client.session_request("GET", "/v1/topics")

    assert captured_tokens == ["just-issued-token"]


def test_find_or_create_topic_exposes_origin() -> None:
    from nexus_tools_agent_blackboard.find_or_create_topic import find_or_create_topic

    signature = inspect.signature(find_or_create_topic)

    assert "origin" in signature.parameters


def test_agent_facing_tools_are_natural_language_first() -> None:
    from nexus_tools_agent_blackboard.post_handoff import post_handoff
    from nexus_tools_agent_blackboard.post_message import post_message
    from nexus_tools_agent_blackboard.propose_doc_revision import propose_doc_revision

    assert "body_md" in inspect.signature(post_message).parameters
    assert "summary_md" in inspect.signature(post_handoff).parameters
    assert "body_md" in inspect.signature(propose_doc_revision).parameters
