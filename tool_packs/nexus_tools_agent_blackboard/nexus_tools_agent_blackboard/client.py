from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from nexus.config import get_setting


DEFAULT_USER_AGENT = "AgentBlackboardNexus/0.1"
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/\-=]+", re.IGNORECASE)


def _setting(name: str, default: str | None = None) -> str | None:
    return get_setting(name) or default


def _normalize_base_url(value: str | None) -> str:
    base_url = (value or "").strip()
    if not base_url:
        raise ValueError("AGENT_BLACKBOARD_BASE_URL is required")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    return base_url.rstrip("/")


def _read_token_file(path: str | None, label: str) -> str:
    if not path:
        raise ValueError(f"{label} token file is not configured")
    token = Path(path).read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError(f"{label} token file is empty")
    return token


def _write_secret_file(path: str, token: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token)
            handle.write("\n")
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, target)
        os.chmod(target, 0o600)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


class AgentBlackboardClient:
    def __init__(self) -> None:
        self.base_url = _normalize_base_url(_setting("AGENT_BLACKBOARD_BASE_URL"))
        self.bootstrap_token_file = _setting("AGENT_BLACKBOARD_BOOTSTRAP_TOKEN_FILE")
        self.session_token_file = _setting("AGENT_BLACKBOARD_SESSION_TOKEN_FILE")
        self.timeout_s = float(_setting("AGENT_BLACKBOARD_TIMEOUT_S", "20") or "20")
        self.session_token = _setting("AGENT_BLACKBOARD_SESSION_TOKEN")
        self.registered_session_token: str | None = None

    def bootstrap_request(self, method: str, path: str, *, body: dict[str, Any] | None = None) -> dict[str, Any]:
        bootstrap_token = _setting("AGENT_BLACKBOARD_BOOTSTRAP_TOKEN") or _read_token_file(self.bootstrap_token_file, "bootstrap")
        return self.request(method, path, body=body, token=bootstrap_token)

    def session_request(self, method: str, path: str, *, body: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
        session_token = self._resolve_session_token()
        consumes_local_pin = bool(self.registered_session_token and session_token == self.registered_session_token)
        try:
            return self.request(method, path, body=body, params=params, token=session_token)
        finally:
            if consumes_local_pin:
                self.registered_session_token = None
                if self.session_token == session_token:
                    self.session_token = None

    def _resolve_session_token(self) -> str | None:
        if self.registered_session_token:
            return self.registered_session_token
        if self.session_token_file:
            try:
                return _read_token_file(self.session_token_file, "session")
            except (OSError, ValueError):
                pass
        env_token = _setting("AGENT_BLACKBOARD_SESSION_TOKEN")
        if env_token:
            return env_token
        return self.session_token

    def request(self, method: str, path: str, *, body: dict[str, Any] | None = None, params: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
        query = ""
        if params:
            clean = {key: value for key, value in params.items() if value is not None}
            query = f"?{urllib.parse.urlencode(clean, doseq=True)}" if clean else ""
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(f"{self.base_url}/{path.lstrip('/')}{query}", data=data, method=method.upper())
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", DEFAULT_USER_AGENT)
        if body is not None:
            request.add_header("Content-Type", "application/json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                text = response.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8") if exc.fp else ""
            problem = _parse_problem(text)
            raise RuntimeError(f"Agent Blackboard HTTP {exc.code}: {_redact(json.dumps(problem, sort_keys=True))}") from exc

    def write_session_token(self, token: str) -> None:
        self.session_token = token
        self.registered_session_token = token
        if not self.session_token_file:
            return
        _write_secret_file(self.session_token_file, token)


def _parse_problem(text: str) -> dict[str, Any]:
    if not text:
        return {"detail": ""}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {"detail": text}
    if isinstance(value, dict):
        return value
    return {"detail": value}


def _redact(text: str) -> str:
    return _BEARER_RE.sub("Bearer [redacted]", text)


_client: AgentBlackboardClient | None = None


def get_client() -> AgentBlackboardClient:
    global _client
    if _client is None:
        _client = AgentBlackboardClient()
    return _client
