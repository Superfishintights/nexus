"""Shared Jira HTTP client for all Jira tools."""
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


class JiraClient:
    """Simple Jira REST API client using only standard library."""

    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        hostname: Optional[str] = None,
        pat: Optional[str] = None,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.hostname = hostname or get_setting("JIRA_HOSTNAME")
        self.pat = pat or get_setting("JIRA_PAT")
        self.timeout_seconds = timeout_seconds

        if not self.hostname:
            raise ValueError(
                "JIRA_HOSTNAME is required (set env var or put it in a `.env` file)."
            )
        if not self.pat:
            raise ValueError("JIRA_PAT is required (set env var or put it in a `.env` file).")

        if not self.hostname.startswith(("http://", "https://")):
            self.hostname = f"https://{self.hostname}"

        self.hostname = self.hostname.rstrip("/")
        self.base_url = f"{self.hostname}/rest/api/2"
        self.auth_header = f"Bearer {self.pat}"

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the Jira API."""
        url = self._build_url(endpoint)

        try:
            request = urllib.request.Request(url)
            request.add_header("Authorization", self.auth_header)
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", DEFAULT_USER_AGENT)

            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                if response.status == 200:
                    data = response.read().decode("utf-8")
                    return json.loads(data)
                raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}")
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}")
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}")


_default_client: Optional[JiraClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> JiraClient:
    """Get or create the default Jira client instance."""
    global _default_client, _default_client_key
    hostname = get_setting("JIRA_HOSTNAME")
    pat = get_setting("JIRA_PAT")
    if not hostname or not pat:
        _default_client = None
        _default_client_key = None
        return JiraClient(hostname=hostname, pat=pat)

    new_key = (hostname, pat)
    if _default_client is None or _default_client_key != new_key:
        _default_client = JiraClient(hostname=hostname, pat=pat)
        _default_client_key = new_key
    return _default_client
