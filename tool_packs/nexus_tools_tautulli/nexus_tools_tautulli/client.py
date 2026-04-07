"""Shared Tautulli HTTP client for all Tautulli tools."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


class TautulliClient:
    """Simple Tautulli API client using only standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_s: float = 30.0,
        api_path: str = "/api/v2",
    ):
        self.base_url = base_url or get_setting("TAUTULLI_URL")
        self.api_key = api_key or get_setting("TAUTULLI_API_KEY")
        self.timeout_s = timeout_s
        self.api_path = api_path

        if not self.base_url:
            raise ValueError(
                "TAUTULLI_URL is required (set env var or put it in a `.env` file)."
            )
        if not self.api_key:
            raise ValueError(
                "TAUTULLI_API_KEY is required (set env var or put it in a `.env` file)."
            )

        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"https://{self.base_url}"

        self.base_url = self.base_url.rstrip("/")

    def call(self, cmd: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Call Tautulli API command and return the decoded `data` payload."""
        query: Dict[str, str] = {"apikey": self.api_key, "cmd": cmd}
        if params:
            for key, value in params.items():
                if value is None:
                    continue
                if isinstance(value, bool):
                    query[key] = "1" if value else "0"
                else:
                    query[key] = str(value)

        url = f"{self.base_url}{self.api_path}?{urllib.parse.urlencode(query)}"

        try:
            request = urllib.request.Request(url)
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", DEFAULT_USER_AGENT)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                data = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}") from exc

        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise Exception("Invalid JSON from Tautulli API") from exc

        response_payload = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(response_payload, dict):
            raise Exception("Unexpected Tautulli response shape (missing `response`)")

        result = response_payload.get("result")
        if result != "success":
            message = response_payload.get("message") or "Tautulli API returned error"
            raise Exception(f"{message} (cmd={cmd})")

        return response_payload.get("data")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        """Compatibility method for generated modules."""
        del api_path
        return self.call(endpoint.strip("/"), params=params)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        """Compatibility method for generated modules."""
        del api_path
        return self.call(endpoint.strip("/"), params=params)

    def head(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        """Compatibility method for generated modules."""
        del api_path
        return self.call(endpoint.strip("/"), params=params)

    def post(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        """Compatibility method for generated modules."""
        del api_path
        merged: Dict[str, Any] = {}
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})
        if isinstance(body, dict):
            merged.update({k: v for k, v in body.items() if v is not None})
        elif body is not None:
            merged["body"] = body
        return self.call(endpoint.strip("/"), params=merged or None)

    def put(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        """Compatibility method for generated modules."""
        del api_path
        merged: Dict[str, Any] = {}
        if params:
            merged.update({k: v for k, v in params.items() if v is not None})
        if isinstance(body, dict):
            merged.update({k: v for k, v in body.items() if v is not None})
        elif body is not None:
            merged["body"] = body
        return self.call(endpoint.strip("/"), params=merged or None)


_default_client: Optional[TautulliClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> TautulliClient:
    """Get or create the default Tautulli client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("TAUTULLI_URL")
    api_key = get_setting("TAUTULLI_API_KEY")
    if not base_url or not api_key:
        _default_client = None
        _default_client_key = None
        return TautulliClient(base_url=base_url, api_key=api_key)

    new_key = (base_url, api_key)
    if _default_client is None or _default_client_key != new_key:
        _default_client = TautulliClient(base_url=base_url, api_key=api_key)
        _default_client_key = new_key
    return _default_client
