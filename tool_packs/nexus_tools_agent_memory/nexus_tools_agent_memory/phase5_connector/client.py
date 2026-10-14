"""Persistent connector-owned HTTP transport for one agent-memory Connection."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit


DEFAULT_USER_AGENT = "Nexus-Agent-Memory-Connector/1"


class AgentMemoryTransportError(RuntimeError):
    """A credential-safe transport failure."""


class AgentMemoryConnectorClient:
    """One lazily opened persistent HTTP session scoped to one Connection."""

    __slots__ = (
        "_base_path",
        "_connection",
        "_connection_factory",
        "_default_agent_id",
        "_default_profile",
        "_host",
        "_lock",
        "_port",
        "_scheme",
        "_timeout_s",
        "_token",
    )

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        default_profile: str,
        default_agent_id: str,
        timeout_s: float,
        connection_factory: Callable[..., http.client.HTTPConnection] | None = None,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("agent-memory endpoint must be an HTTP(S) URL")
        self._scheme = parsed.scheme
        self._host = parsed.hostname
        self._port = parsed.port
        self._base_path = parsed.path.rstrip("/")
        self._token = token
        self._default_profile = default_profile
        self._default_agent_id = default_agent_id
        self._timeout_s = timeout_s
        self._connection_factory = connection_factory
        self._connection: http.client.HTTPConnection | None = None
        self._lock = threading.Lock()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        agent_id: str | None = None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        encoded = None if body is None else json.dumps(body, allow_nan=False).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if encoded is not None:
            headers["Content-Type"] = "application/json"
        if require_auth:
            headers["Authorization"] = f"Bearer {self._token}"
            headers["X-Agent-Id"] = agent_id or self._default_agent_id
        target = f"{self._base_path}/{path.lstrip('/')}" or "/"
        with self._lock:
            connection = self._get_connection()
            try:
                connection.request(method.upper(), target, body=encoded, headers=headers)
                response = connection.getresponse()
                payload = response.read()
            except Exception:
                self._discard_connection()
                raise AgentMemoryTransportError("Agent-memory transport request failed") from None
            if response.status < 200 or response.status >= 300:
                raise AgentMemoryTransportError(
                    f"Agent-memory transport returned HTTP {response.status}"
                )
            if not payload:
                return {}
            try:
                decoded = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise AgentMemoryTransportError("Agent-memory transport returned invalid JSON") from None
            if not isinstance(decoded, dict):
                raise AgentMemoryTransportError("Agent-memory transport returned a non-object result")
            return decoded

    def resolve_profile(self, profile: str | None) -> str:
        return profile or self._default_profile

    def close(self) -> None:
        with self._lock:
            self._discard_connection()

    def _get_connection(self) -> http.client.HTTPConnection:
        if self._connection is None:
            factory = self._connection_factory
            if factory is None:
                factory = (
                    http.client.HTTPSConnection
                    if self._scheme == "https"
                    else http.client.HTTPConnection
                )
            self._connection = factory(self._host, self._port, timeout=self._timeout_s)
        return self._connection

    def _discard_connection(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
