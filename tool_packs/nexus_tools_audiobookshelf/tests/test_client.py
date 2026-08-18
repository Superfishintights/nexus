from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexus_tools_audiobookshelf.client import (
    AudiobookshelfClient,
    AudiobookshelfError,
    BACKUP_EXTENSIONS,
    COVER_EXTENSIONS,
)


class FakeResponse:
    def __init__(self, status=200, body=b"{}", content_type="application/json"):
        self.status = status
        self._body = body
        self._content_type = content_type

    def read(self):
        return self._body

    def getheader(self, name, default=None):
        return self._content_type if name.lower() == "content-type" else default


class FakeConnection:
    def __init__(self, response):
        self.response = response
        self.calls = []
        self.closed = False

    def request(self, method, target, body=None, headers=None):
        body_bytes = b"" if body is None else body if isinstance(body, bytes) else b"".join(body)
        self.calls.append((method, target, body_bytes, dict(headers or {})))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


def make_client(**kwargs):
    # Do not inherit a live deployment's hostname-specific resolve override
    # when constructing the synthetic abs.example.com test client.
    kwargs.setdefault("resolve", "")
    return AudiobookshelfClient(
        base_url="https://abs.example.com",
        api_token="super-secret-token",
        **kwargs,
    )


def test_json_request_uses_bearer_header_and_strict_json(monkeypatch):
    client = make_client()
    connection = FakeConnection(FakeResponse(body=b'{"ok":true}'))
    monkeypatch.setattr(client, "_connection", lambda: connection)

    assert client.patch("items/id/media", {"title": "A"}) == {"ok": True}
    method, target, body, headers = connection.calls[0]
    assert method == "PATCH"
    assert target == "/api/items/id/media"
    assert json.loads(body) == {"title": "A"}
    assert headers["Authorization"] == "Bearer super-secret-token"
    assert "super-secret-token" not in target


def test_json_response_recursively_redacts_returned_credentials(monkeypatch):
    client = make_client()
    response = FakeResponse(
        body=b'{"user":{"token":"other-user-token","password":"hash","name":"Jay"},"apiKey":"key"}'
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(response))

    assert client.get("users") == {
        "user": {"token": "[REDACTED]", "password": "[REDACTED]", "name": "Jay"},
        "apiKey": "[REDACTED]",
    }


def test_notification_urls_and_embedded_log_credentials_are_redacted(monkeypatch):
    client = make_client()
    response = FakeResponse(
        body=(
            b'{"settings":{"appriseApiUrl":"https://apprise.example/api",'
            b'"notifications":[{"urls":["discord://secret"]}]},'
            b'"logs":["Authorization: Bearer leaked"]}'
        )
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(response))

    assert client.get("notifications") == {
        "settings": {
            "appriseApiUrl": "[REDACTED]",
            "notifications": [{"urls": "[REDACTED]"}],
        },
        "logs": ["Authorization: Bearer [REDACTED]"],
    }


def test_status_can_be_unauthenticated(monkeypatch):
    client = make_client()
    connection = FakeConnection(FakeResponse(body=b'{"isInit":true}'))
    monkeypatch.setattr(client, "_connection", lambda: connection)

    assert client.get("status", api_path="", authenticated=False) == {"isInit": True}
    assert "Authorization" not in connection.calls[0][3]


def test_empty_text_and_binary_responses_are_json_serializable(monkeypatch):
    client = make_client()
    responses = iter(
        [
            FakeResponse(status=204, body=b"", content_type=""),
            FakeResponse(body=b"plain", content_type="text/plain"),
            FakeResponse(body=b"\xff\x00", content_type="application/octet-stream"),
        ]
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(next(responses)))

    assert client.get("one") is None
    assert client.get("two") == "plain"
    binary = client.get("three")
    assert binary == {"contentType": "application/octet-stream", "size": 2, "base64": "/wA="}
    json.dumps(binary)


def test_malformed_json_response_is_returned_safely_and_redacted(monkeypatch):
    client = make_client()
    response = FakeResponse(
        body=b'{"token":"remote-secret", broken',
        content_type="application/json; charset=utf-8",
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(response))

    result = client.get("broken")
    assert result == '{"token":"[REDACTED]", broken'
    json.dumps(result)


def test_http_error_redacts_token_and_omits_query(monkeypatch):
    client = make_client()
    response = FakeResponse(
        status=400,
        body=b'bad token super-secret-token and Authorization: Bearer leaked',
        content_type="text/plain",
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(response))

    with pytest.raises(AudiobookshelfError) as raised:
        client.get("search/books", {"q": "private title"})
    message = str(raised.value)
    assert "super-secret-token" not in message
    assert "private title" not in message
    assert "[REDACTED]" in message


def test_http_error_redacts_other_credential_fields(monkeypatch):
    client = make_client()
    response = FakeResponse(
        status=500,
        body=b'{"apiKey":"remote-key","password":"remote-password"}',
        content_type="application/json",
    )
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(response))

    with pytest.raises(AudiobookshelfError) as raised:
        client.get("users")
    message = str(raised.value)
    assert "remote-key" not in message
    assert "remote-password" not in message
    assert message.count("[REDACTED]") == 2


def test_path_segments_and_endpoint_traversal_are_controlled():
    client = make_client()
    assert client.segment("a/b c") == "a%2Fb%20c"
    with pytest.raises(ValueError):
        client.segment("..")
    with pytest.raises(ValueError):
        client.get("items/../users")


def test_query_booleans_use_audiobookshelf_numeric_flags(monkeypatch):
    client = make_client()
    connection = FakeConnection(FakeResponse())
    monkeypatch.setattr(client, "_connection", lambda: connection)

    client.get(
        "libraries/lib/items",
        {"minified": True, "collapseseries": True, "desc": False},
    )

    assert connection.calls[0][1] == (
        "/api/libraries/lib/items?minified=1&collapseseries=1&desc=0"
    )


def test_resolve_must_match_url_and_use_literal_ip():
    client = make_client(resolve="abs.example.com:443:192.0.2.10")
    assert client._resolve_address == "192.0.2.10"
    with pytest.raises(ValueError):
        make_client(resolve="other.example.com:443:192.0.2.10")
    with pytest.raises(ValueError):
        make_client(resolve="abs.example.com:443:host.example.com")


def test_resolve_changes_only_socket_target_and_preserves_tls_hostname(monkeypatch):
    client = make_client(resolve="abs.example.com:443:192.0.2.10")
    targets = []

    def fake_create_connection(target, **kwargs):
        targets.append((target, kwargs))
        return object()

    monkeypatch.setattr("nexus_tools_audiobookshelf.client.socket.create_connection", fake_create_connection)
    connection = client._connection()

    assert connection.host == "abs.example.com"
    assert connection._context.check_hostname is True
    assert connection._context.verify_mode.name == "CERT_REQUIRED"
    assert connection._create_connection(("abs.example.com", 443), timeout=3) is not None
    assert targets == [(('192.0.2.10', 443), {"timeout": 3, "source_address": None})]


def test_upload_rejects_outside_root_and_streams_allowed_file(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    cover = allowed / "cover.jpg"
    cover.write_bytes(b"jpeg-data")
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"no")
    client = make_client(upload_roots=[allowed])
    connection = FakeConnection(FakeResponse(body=b'{"success":true}'))
    monkeypatch.setattr(client, "_connection", lambda: connection)

    assert client.upload_cover("item/1", cover) == {"success": True}
    method, target, body, headers = connection.calls[0]
    assert method == "POST"
    assert target == "/api/items/item%2F1/cover"
    assert b"jpeg-data" in body
    assert str(cover).encode() not in body
    assert int(headers["Content-Length"]) == len(body)
    with pytest.raises(ValueError):
        client.multipart(
            "items/x/cover",
            fields=None,
            files=[("cover", outside)],
            allowed_extensions=COVER_EXTENSIONS,
        )


def test_upload_rejects_symlink_that_escapes_allowlisted_root(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"no")
    link = allowed / "cover.jpg"
    link.symlink_to(outside)
    client = make_client(upload_roots=[allowed])

    with pytest.raises(ValueError, match="outside AUDIOBOOKSHELF_UPLOAD_ROOTS"):
        client.upload_cover("item", link)


def test_upload_rejects_extension_and_size_limit(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    bad = root / "cover.exe"
    bad.write_bytes(b"x")
    good = root / "cover.jpg"
    good.write_bytes(b"123456789")
    client = make_client(upload_roots=[root], max_upload_bytes=5)

    with pytest.raises(ValueError, match="unsupported upload extension"):
        client.upload_cover("item", bad)
    with pytest.raises(ValueError, match="exceeds"):
        client.upload_cover("item", good)


def test_backup_upload_accepts_only_audiobookshelf_extension(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    backup = root / "server-backup.audiobookshelf"
    backup.write_bytes(b"backup-data")
    archive = root / "server-backup.zip"
    archive.write_bytes(b"zip-data")
    client = make_client(upload_roots=[root])
    connection = FakeConnection(FakeResponse(body=b'{"success":true}'))
    monkeypatch.setattr(client, "_connection", lambda: connection)

    assert client.upload_backup(backup) == {"success": True}
    assert connection.calls[0][0:2] == ("POST", "/api/backups/upload")
    with pytest.raises(ValueError, match="unsupported upload extension"):
        client.multipart(
            "backups/upload",
            fields=None,
            files=[("file", archive)],
            allowed_extensions=BACKUP_EXTENSIONS,
        )


def test_json_serialization_rejects_nan(monkeypatch):
    client = make_client()
    monkeypatch.setattr(client, "_connection", lambda: FakeConnection(FakeResponse()))
    with pytest.raises(ValueError, match="strictly JSON serializable"):
        client.post("items", {"duration": float("nan")})


@pytest.mark.parametrize("value", [0, -1, 0.01, 601, "not-a-number"])
def test_timeout_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="AUDIOBOOKSHELF_TIMEOUT_S"):
        make_client(timeout_s=value)


def test_find_duplicate_items_paginates_and_groups(monkeypatch):
    client = make_client()
    pages = [
        {
            "results": [
                {"id": "1", "path": "/books/a", "media": {"metadata": {"title": "Book", "authorName": "A", "isbn": "X"}}},
                {"id": "2", "path": "/books/b", "media": {"metadata": {"title": " book ", "authorName": "a", "isbn": "X"}}},
            ],
            "total": 2,
        }
    ]
    monkeypatch.setattr(client, "get", lambda *args, **kwargs: pages.pop(0))

    result = client.find_duplicate_items("lib", page_size=2)
    assert result["scanned"] == 2
    assert result["duplicateGroupCount"] == 2
    assert {group["key"] for group in result["groups"]} == {"isbn", "title_author"}
