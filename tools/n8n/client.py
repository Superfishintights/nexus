"""Shared n8n HTTP client."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from nexus.config import get_setting


class N8NClient:
    """Simple n8n REST API client using only standard library."""

    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.host = host or get_setting("N8N_HOST")
        self.api_key = api_key or get_setting("N8N_API_KEY")
        self.timeout_seconds = timeout_seconds

        if not self.host:
            raise ValueError(
                "N8N_HOST is required (set env var or put it in a .env file)."
            )
        if not self.api_key:
            raise ValueError("N8N_API_KEY is required (set env var or put it in a .env file).")

        if not self.host.startswith(("http://", "https://")):
            self.host = f"https://{self.host}"

        self.host = self.host.rstrip("/")
        # API v1 base URL
        self.base_url = f"{self.host}/api/v1"
        self.auth_header = self.api_key

    def _build_url(self, endpoint: str, query_params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if not query_params:
            return url

        # Drop `None` values; allow lists/tuples via `doseq=True`.
        filtered = {k: v for k, v in query_params.items() if v is not None}
        if not filtered:
            return url

        return url + "?" + urllib.parse.urlencode(filtered, doseq=True)

    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        data: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], list]:
        """Make a request to the n8n API."""
        url = self._build_url(endpoint, query_params=query_params)

        try:
            req = urllib.request.Request(url, method=method)
            req.add_header("X-N8N-API-KEY", self.auth_header)
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")

            if data is not None:
                json_data = json.dumps(data).encode("utf-8")
                req.data = json_data

            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                if response.status in (200, 201):
                    response_data = response.read().decode("utf-8")
                    if not response_data:
                        return {}
                    return json.loads(response_data)
                elif response.status == 204:
                    return {}
                
                raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}")
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}")
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}")


_default_client: Optional[N8NClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> N8NClient:
    """Get or create the default n8n client instance."""
    global _default_client, _default_client_key
    host = get_setting("N8N_HOST")
    api_key = get_setting("N8N_API_KEY")
    
    if not host or not api_key:
        _default_client = None
        _default_client_key = None
        return N8NClient(host=host, api_key=api_key)

    new_key = (host, api_key)
    if _default_client is None or _default_client_key != new_key:
        _default_client = N8NClient(host=host, api_key=api_key)
        _default_client_key = new_key
    return _default_client
