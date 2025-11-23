"""Shared Jira HTTP client for all Jira tools."""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional


class JiraClient:
    """Simple Jira REST API client using only standard library."""

    def __init__(self, hostname: Optional[str] = None, pat: Optional[str] = None):
        self.hostname = hostname or os.getenv("JIRA_HOSTNAME")
        self.pat = pat or os.getenv("JIRA_PAT")

        if not self.hostname:
            raise ValueError("JIRA_HOSTNAME environment variable is required")
        if not self.pat:
            raise ValueError("JIRA_PAT environment variable is required")

        if not self.hostname.startswith(('http://', 'https://')):
            self.hostname = f"https://{self.hostname}"

        self.hostname = self.hostname.rstrip('/')
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
                    data = response.read().decode('utf-8')
                    return json.loads(data)
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"HTTP {e.code}: {e.reason}. Details: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def _make_post_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the Jira API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(url, data=json_data, method='POST')
            request.add_header("Authorization", self.auth_header)
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request) as response:
                if response.status in [200, 201, 204]:
                    response_data = response.read().decode('utf-8')
                    if response_data:
                        return json.loads(response_data)
                    else:
                        return {'status': 'success', 'code': response.status}
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"HTTP {e.code}: {e.reason}. Details: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def _make_put_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the Jira API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(url, data=json_data, method='PUT')
            request.add_header("Authorization", self.auth_header)
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request) as response:
                if response.status in [200, 204]:
                    response_data = response.read().decode('utf-8')
                    if response_data:
                        return json.loads(response_data)
                    else:
                        return {'status': 'success', 'code': response.status}
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"HTTP {e.code}: {e.reason}. Details: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def _make_delete_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the Jira API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            request = urllib.request.Request(url, method='DELETE')
            request.add_header("Authorization", self.auth_header)
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request) as response:
                if response.status in [200, 204]:
                    response_data = response.read().decode('utf-8')
                    if response_data:
                        return json.loads(response_data)
                    else:
                        return {'status': 'success', 'code': response.status}
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"HTTP {e.code}: {e.reason}. Details: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")


_default_client: Optional[JiraClient] = None


def get_client() -> JiraClient:
    """Get or create the default Jira client instance."""
    global _default_client
    if _default_client is None:
        _default_client = JiraClient()
    return _default_client
