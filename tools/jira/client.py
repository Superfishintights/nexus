"""Shared Jira HTTP client for all Jira tools."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class JiraClient:
    """Simple Jira REST API client using only standard library."""

    def __init__(self, hostname: Optional[str] = None, pat: Optional[str] = None):
        self.hostname = hostname or os.getenv("JIRA_HOSTNAME")
        self.pat = pat or os.getenv("JIRA_PAT")

        if not self.hostname:
            raise ValueError("JIRA_HOSTNAME environment variable is required")
        if not self.pat:
            raise ValueError("JIRA_PAT environment variable is required")

        if not self.hostname.startswith(("http://", "https://")):
            self.hostname = f"https://{self.hostname}"

        self.hostname = self.hostname.rstrip("/")
        self.base_url = f"{self.hostname}/rest/api/2"
        self.auth_header = f"Bearer {self.pat}"

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the Jira API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            request = urllib.request.Request(url)
            request.add_header("Authorization", self.auth_header)
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request) as response:
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


def get_client() -> JiraClient:
    """Get or create the default Jira client instance."""
    global _default_client
    if _default_client is None:
        _default_client = JiraClient()
    return _default_client
