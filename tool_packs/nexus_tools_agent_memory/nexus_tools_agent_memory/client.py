"""Shared HTTP client for the agent-memory service."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


def _normalize_base_url(value: Optional[str]) -> str:
    base_url = (value or "").strip()
    if not base_url:
        return ""
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    return base_url.rstrip("/")


def _float_setting(name: str, default: float) -> float:
    raw = get_setting(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class AgentMemoryClient:
    """Standard-library HTTP client for the agent-memory service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        default_profile: Optional[str] = None,
        default_agent_id: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ):
        self.base_url = _normalize_base_url(base_url or get_setting("AGENT_MEMORY_BASE_URL"))
        self.token = token or get_setting("AGENT_MEMORY_TOKEN")
        self.default_profile = default_profile or get_setting("AGENT_MEMORY_DEFAULT_PROFILE")
        self.default_agent_id = default_agent_id or get_setting("AGENT_MEMORY_AGENT_ID") or "nexus"
        self.timeout_s = timeout_s if timeout_s is not None else _float_setting("AGENT_MEMORY_TIMEOUT_S", 30.0)

        if not self.base_url:
            raise ValueError(
                "AGENT_MEMORY_BASE_URL is required (set env var or put it in a `.env` file)."
            )
        if not self.token:
            raise ValueError(
                "AGENT_MEMORY_TOKEN is required (set env var or put it in a `.env` file)."
            )

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        encoded_body = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, method=method.upper(), data=encoded_body)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", DEFAULT_USER_AGENT)

        if body is not None:
            request.add_header("Content-Type", "application/json")

        if require_auth:
            request.add_header("Authorization", f"Bearer {self.token}")
            request.add_header("X-Agent-Id", agent_id or self.default_agent_id)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            raise RuntimeError(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"URL Error: {exc.reason}") from exc

    def resolve_profile(self, profile: Optional[str]) -> str:
        chosen = profile or self.default_profile
        if not chosen:
            raise ValueError(
                "A profile is required. Set AGENT_MEMORY_DEFAULT_PROFILE or pass profile explicitly."
            )
        return chosen


_default_client: Optional[AgentMemoryClient] = None
_default_client_key: Optional[tuple[str, str, str, str, float]] = None


def get_client() -> AgentMemoryClient:
    """Get or create the default agent-memory client instance."""

    global _default_client, _default_client_key
    base_url = _normalize_base_url(get_setting("AGENT_MEMORY_BASE_URL"))
    token = get_setting("AGENT_MEMORY_TOKEN") or ""
    default_profile = get_setting("AGENT_MEMORY_DEFAULT_PROFILE") or ""
    default_agent_id = get_setting("AGENT_MEMORY_AGENT_ID") or "nexus"
    timeout_s = _float_setting("AGENT_MEMORY_TIMEOUT_S", 30.0)
    key = (base_url, token, default_profile, default_agent_id, timeout_s)

    if _default_client is None or _default_client_key != key:
        _default_client = AgentMemoryClient(
            base_url=base_url,
            token=token,
            default_profile=default_profile,
            default_agent_id=default_agent_id,
            timeout_s=timeout_s,
        )
        _default_client_key = key

    return _default_client
