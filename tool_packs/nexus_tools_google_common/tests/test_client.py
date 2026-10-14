from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
import urllib.error
from unittest import mock

from nexus_tools_google_common import (
    GoogleApiClient,
    GoogleApiError,
    GoogleAuthError,
    build_authorization_url,
    coerce_json,
    coerce_list,
    quote_path_segment,
    quote_resource_name,
)
from nexus_tools_google_common import client as client_module


class GoogleCommonClientTests(unittest.TestCase):
    def test_public_helpers(self) -> None:
        self.assertEqual(quote_path_segment("a/b c"), "a%2Fb%20c")
        self.assertEqual(quote_resource_name("people/c 123"), "people/c%20123")
        self.assertEqual(coerce_json('{"a":1}'), {"a": 1})
        self.assertEqual(coerce_list('["x"]'), ["x"])

    @mock.patch("nexus_tools_google_common.client.get_setting")
    def test_build_authorization_url_uses_pkce(self, get_setting: mock.Mock) -> None:
        values = {
            "GOOGLE_CLIENT_ID": "client-1",
            "GOOGLE_AUTH_URL": None,
            "GOOGLE_SCOPES": None,
        }
        get_setting.side_effect = lambda name: values.get(name)
        result = build_authorization_url(scopes=["scope-a", "scope-b"], redirect_uri="http://127.0.0.1:9999/cb")
        self.assertIn("code_challenge=", result["url"])
        self.assertIn("code_challenge_method=S256", result["url"])
        self.assertEqual(result["redirect_uri"], "http://127.0.0.1:9999/cb")
        self.assertGreater(len(result["code_verifier"]), 40)

    def test_manual_redirect_rejects_state_mismatch(self) -> None:
        with self.assertRaises(GoogleAuthError):
            client_module.exchange_authorization_redirect(
                "http://127.0.0.1/callback?state=wrong&code=abc",
                expected_state="expected",
                code_verifier="verifier",
            )

    def test_mutating_requests_are_not_implicitly_retryable(self) -> None:
        self.assertTrue(client_module._retry_allowed("GET", None))
        self.assertFalse(client_module._retry_allowed("POST", None))
        self.assertFalse(client_module._retry_allowed("DELETE", None))

    def test_token_file_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token_path = os.path.join(tmp, "token.json")
            client_module._write_token_file(token_path, {"access_token": "token"})
            mode = stat.S_IMODE(os.stat(token_path).st_mode)
            self.assertEqual(mode, 0o600)
            self.assertEqual(client_module._read_token_file(token_path)["access_token"], "token")
            os.chmod(token_path, 0o644)
            with self.assertRaises(GoogleAuthError):
                client_module._read_token_file(token_path)

    @mock.patch("nexus_tools_google_common.client.get_setting")
    def test_client_config_file_used_below_explicit_env(self, get_setting: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "client.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "installed": {
                            "client_id": "file-client",
                            "client_secret": "file-secret",
                            "auth_uri": "https://auth.example/auth",
                            "token_uri": "https://auth.example/token",
                            "redirect_uris": ["http://127.0.0.1/callback"],
                        }
                    },
                    handle,
                )
            os.chmod(config_path, 0o600)
            values = {
                "GOOGLE_CLIENT_CONFIG_FILE": config_path,
                "GOOGLE_CLIENT_ID": "env-client",
                "GOOGLE_CLIENT_SECRET": None,
                "GOOGLE_TOKEN_URL": None,
                "GOOGLE_TOKEN_FILE": "",
                "GOOGLE_ACCESS_TOKEN": None,
                "GOOGLE_REFRESH_TOKEN": None,
                "GOOGLE_TIMEOUT_SECONDS": None,
                "GOOGLE_RETRY_COUNT": None,
                "GOOGLE_RETRY_BASE_SECONDS": None,
            }
            get_setting.side_effect = lambda name: values.get(name)

            google = GoogleApiClient()

        self.assertEqual(google.client_id, "env-client")
        self.assertEqual(google.client_secret, "file-secret")
        self.assertEqual(google.token_url, "https://auth.example/token")

    @mock.patch("nexus_tools_google_common.client.get_setting")
    def test_client_config_file_permissions_are_strict(self, get_setting: mock.Mock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "client.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"installed": {"client_id": "file-client"}}, handle)
            os.chmod(config_path, 0o644)
            get_setting.side_effect = lambda name: config_path if name == "GOOGLE_CLIENT_CONFIG_FILE" else None
            with self.assertRaises(GoogleAuthError):
                client_module._read_client_config()

    @mock.patch("nexus_tools_google_common.client.get_setting")
    def test_request_json_body_and_headers(self, get_setting: mock.Mock) -> None:
        get_setting.return_value = None
        google = GoogleApiClient(access_token="access", token_file="")
        captured = {}

        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"ok":true}'

            def getheader(self, name):
                return self.headers.get(name)

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["data"] = request.data
            return Response()

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            result = google.request("calendar", "users/me/calendarList", method="POST", payload={"x": 1})

        self.assertEqual(result, {"ok": True})
        self.assertEqual(captured["data"], b'{"x":1}')
        self.assertEqual(captured["headers"]["Content-type"], "application/json")
        self.assertIn("Authorization", captured["headers"])

    @mock.patch("nexus_tools_google_common.client.get_setting")
    def test_http_error_normalized(self, get_setting: mock.Mock) -> None:
        get_setting.return_value = None
        google = GoogleApiClient(access_token="access", token_file="", retry_count=0)
        body = json.dumps({"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}}).encode()

        class ErrorBody:
            def __init__(self, payload):
                self.payload = payload

            def read(self):
                return self.payload

            def close(self):
                return None

        def fake_error(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, ErrorBody(body))

        with mock.patch("urllib.request.urlopen", fake_error):
            with self.assertRaises(GoogleApiError) as raised:
                google.request("calendar", "bad")

        self.assertEqual(raised.exception.status, 400)
        self.assertIn("bad request", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
