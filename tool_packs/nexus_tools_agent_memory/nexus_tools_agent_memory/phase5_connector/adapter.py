"""Agent-memory adapter for the shared long-lived connector worker protocol."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from .client import AgentMemoryConnectorClient
from .source import EXPECTED_SOURCE_REVISION_DIGEST, load_source


class AgentMemoryConnectorError(RuntimeError):
    """Credential-safe connector failure."""


class AgentMemoryConnectorAdapter:
    """One reusable HTTP client scoped to one worker-managed Connection."""

    __slots__ = ("_connection_id", "_client", "_tools", "_aliases")

    def __init__(self, connection_id: str, client: AgentMemoryConnectorClient) -> None:
        self._connection_id = connection_id
        self._client: AgentMemoryConnectorClient | None = client
        source = load_source()
        self._tools = {
            item["identityMapping"]["legacyCanonicalName"]: item for item in source["tools"]
        }
        self._aliases = {
            alias: item["identityMapping"]["legacyCanonicalName"]
            for item in source["tools"]
            for alias in item["identityMapping"]["aliases"]
        }

    def __repr__(self) -> str:
        return (
            f"AgentMemoryConnectorAdapter(connection_id={self._connection_id!r}, "
            f"closed={self._client is None})"
        )

    def diagnostics(self) -> dict[str, Any]:
        return {
            "connectionId": self._connection_id,
            "integrationId": "integration.agent-memory",
            "closed": self._client is None,
            "canonicalTools": len(self._tools),
            "aliases": len(self._aliases),
        }

    def resolve_name(self, operation: str) -> str:
        if operation in self._tools:
            return operation
        if operation in self._aliases:
            return self._aliases[operation]
        dot_name = f"agent_memory.{operation.removeprefix('agent_memory:')}"
        if dot_name in self._tools:
            return dot_name
        raise KeyError(operation)

    def describe(self, operation: str) -> Mapping[str, Any]:
        return self._tools[self.resolve_name(operation)]

    def invoke(self, operation: str, arguments: Mapping[str, Any], context: Any) -> Any:
        """Shared-worker Connector.invoke implementation for synchronous calls."""
        _check_context(context)
        canonical = self.resolve_name(operation)
        item = self._tools[canonical]
        args = dict(arguments)
        _validate_arguments(item, args)
        try:
            result = self._invoke_operation(canonical.removeprefix("agent_memory."), args)
            _assert_json_safe(result)
            return result
        except AgentMemoryConnectorError:
            raise
        except (KeyError, TypeError, ValueError, TimeoutError):
            raise
        except Exception:
            raise AgentMemoryConnectorError("Agent-memory connector invocation failed") from None

    def close(self) -> None:
        client = self._client
        self._client = None
        close = getattr(client, "close", None)
        if close is not None:
            try:
                close()
            except Exception:
                raise AgentMemoryConnectorError("Agent-memory connector close failed") from None

    def _invoke_operation(self, operation: str, args: dict[str, Any]) -> dict[str, Any]:
        client = self._require_client()
        agent_id = args.get("agent_id")
        if operation == "get_health":
            return client.request("GET", "/healthz", require_auth=False)
        if operation == "get_ready":
            return client.request("GET", "/readyz", require_auth=False)
        if operation == "remember":
            body = {
                "profile": client.resolve_profile(args.get("profile")),
                "type": args.get("memory_type", "fact"),
                "content": args["content"],
                "source": {
                    "kind": args.get("source_kind", "manual"),
                    "title": args.get("source_title", "Nexus"),
                },
            }
            _copy_truthy(args, body, ("scope", "labels", "metadata"))
            _copy_not_none(args, body, ("importance",))
            return client.request("POST", "/v1/memory/remember", body=body, agent_id=agent_id)
        if operation == "recall":
            body = {
                "profile": client.resolve_profile(args.get("profile")),
                "query": args["query"],
                "mode": args.get("mode", "evidence"),
            }
            if args.get("scope_filters"):
                body["scopeFilters"] = args["scope_filters"]
            _copy_not_none(args, body, ("limit",))
            return client.request("POST", "/v1/memory/recall", body=body, agent_id=agent_id)
        if operation == "list_memories":
            body = {"profile": client.resolve_profile(args.get("profile"))}
            _copy_truthy(args, body, ("scope",))
            _copy_not_none(args, body, ("limit", "cursor"))
            return client.request("POST", "/v1/memory/list", body=body, agent_id=agent_id)
        if operation == "forget":
            body = {
                "profile": client.resolve_profile(args.get("profile")),
                "memoryId": args["memory_id"],
            }
            _copy_truthy(args, body, ("reason",))
            return client.request("POST", "/v1/memory/forget", body=body, agent_id=agent_id)
        if operation == "correct":
            replacement = {
                "type": args.get("replacement_type", "fact"),
                "content": args["replacement_content"],
                "source": {
                    "kind": args.get("replacement_source_kind", "manual"),
                    "title": args.get("replacement_source_title", "Nexus"),
                },
            }
            for source_key, target_key in (
                ("replacement_scope", "scope"),
                ("replacement_labels", "labels"),
                ("replacement_metadata", "metadata"),
            ):
                if args.get(source_key):
                    replacement[target_key] = args[source_key]
            if args.get("replacement_importance") is not None:
                replacement["importance"] = args["replacement_importance"]
            body = {
                "profile": client.resolve_profile(args.get("profile")),
                "memoryId": args["memory_id"],
                "replacement": replacement,
            }
            _copy_truthy(args, body, ("reason",))
            return client.request("POST", "/v1/memory/correct", body=body, agent_id=agent_id)
        if operation == "ingest":
            body = {
                "profile": client.resolve_profile(args.get("profile")),
                "content": args["content"],
                "contentType": args.get("content_type", "text/plain"),
                "source": {
                    "kind": args.get("source_kind", "manual"),
                    "title": args.get("source_title", "Nexus"),
                },
            }
            _copy_truthy(args, body, ("scope", "labels", "metadata"))
            return client.request("POST", "/v1/memory/ingest", body=body, agent_id=agent_id)
        raise KeyError(operation)

    def _require_client(self) -> AgentMemoryConnectorClient:
        if self._client is None:
            raise AgentMemoryConnectorError("Agent-memory connector is closed")
        return self._client


def create_connector(
    configuration: Mapping[str, Any],
    resolved_secrets: Mapping[str, str],
    *,
    client_factory: Any = AgentMemoryConnectorClient,
) -> AgentMemoryConnectorAdapter:
    """Shared worker factory(configuration, resolvedSecrets)."""
    allowed = {"connectionId", "endpoint", "timeoutS", "defaultProfile", "defaultAgentId", "nexusSourceRevisionDigest"}
    unknown = set(configuration) - allowed
    if unknown:
        raise ValueError(f"unsupported agent-memory configuration fields: {sorted(unknown)}")
    connection_id = configuration.get("connectionId")
    endpoint = configuration.get("endpoint")
    timeout = configuration.get("timeoutS", 30.0)
    default_profile = configuration.get("defaultProfile")
    default_agent_id = configuration.get("defaultAgentId", "nexus")
    token = resolved_secrets.get("token")
    if configuration.get("nexusSourceRevisionDigest") != EXPECTED_SOURCE_REVISION_DIGEST:
        raise ValueError("agent-memory source revision does not match gateway acceptance")
    if set(resolved_secrets) != {"token"}:
        raise ValueError("resolved secret names must contain only token")
    if not isinstance(connection_id, str) or not connection_id:
        raise ValueError("connectionId is required")
    if not _safe_http_endpoint(endpoint):
        raise ValueError("agent-memory endpoint must be an HTTP(S) URL")
    if not isinstance(token, str) or not token:
        raise ValueError("resolved token is required")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("timeoutS must be greater than zero")
    if not isinstance(default_profile, str) or not default_profile:
        raise ValueError("defaultProfile must be a non-empty string")
    if not isinstance(default_agent_id, str) or not default_agent_id:
        raise ValueError("defaultAgentId must be a non-empty string")
    try:
        client = client_factory(
            base_url=endpoint,
            token=token,
            default_profile=default_profile,
            default_agent_id=default_agent_id,
            timeout_s=float(timeout),
        )
        return AgentMemoryConnectorAdapter(connection_id, client)
    except Exception:
        raise AgentMemoryConnectorError("Agent-memory connector startup failed") from None


def create_registry() -> Any:
    """Explicit worker-startup registry; importing this module registers nothing."""
    from nexus_connector.registry import ConnectorRegistry

    registry = ConnectorRegistry()
    registry.register("integration.agent-memory", create_connector)
    return registry


def _validate_arguments(item: Mapping[str, Any], arguments: Mapping[str, Any]) -> None:
    schema = item["schemas"]["original"]["inputSchema"]
    allowed = set(schema["properties"])
    unknown = set(arguments) - allowed
    if unknown:
        raise TypeError(f"unexpected arguments: {sorted(unknown)}")
    for required in schema.get("required", ()):
        if required not in arguments:
            raise TypeError(f"missing required argument: {required}")


def _safe_http_endpoint(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def _check_context(context: Any) -> None:
    deadline = getattr(context, "deadline_monotonic", None)
    if isinstance(deadline, (int, float)) and time.monotonic() >= deadline:
        raise TimeoutError("agent-memory invocation deadline elapsed")
    if getattr(context, "cancelled", False):
        raise TimeoutError("agent-memory invocation cancelled")
    cancellation = getattr(context, "cancellation_event", None)
    if cancellation is not None and callable(getattr(cancellation, "is_set", None)) and cancellation.is_set():
        raise TimeoutError("agent-memory invocation cancelled")


def _copy_truthy(source: Mapping[str, Any], target: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        if source.get(key):
            target[key] = source[key]


def _copy_not_none(source: Mapping[str, Any], target: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        if source.get(key) is not None:
            target[key] = source[key]


def _assert_json_safe(value: Any) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        raise AgentMemoryConnectorError("Agent-memory returned a non-JSON-safe result") from None
