from __future__ import annotations

import base64
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACK_ROOT))

from nexus_tools_waha import api  # noqa: E402
from nexus_tools_waha import client  # noqa: E402
from nexus_tools_waha.client import WahaClient, encode_local_file  # noqa: E402


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, *, params=None, accept="application/json"):
        self.calls.append(("GET", path, params, accept))
        return {"ok": True}

    def post(self, path, body=None, *, params=None, accept="application/json"):
        self.calls.append(("POST", path, body, params, accept))
        return {"ok": True}


def test_get_messages_encodes_path_and_forwards_filters(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)

    result = api.get_messages(
        "447700900123@c.us",
        limit=25,
        since_timestamp=123,
        from_me=False,
    )

    assert result == {"ok": True}
    assert fake.calls == [
        (
            "GET",
            "/api/default/chats/447700900123%40c.us/messages",
            {
                "limit": 25,
                "offset": 0,
                "filter.timestamp.gte": 123,
                "filter.timestamp.lte": None,
                "filter.fromMe": False,
                "downloadMedia": False,
            },
            "application/json",
        )
    ]


def test_send_text_only_includes_requested_optional_fields(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)

    api.send_text("447700900123@c.us", "Hello", reply_to="msg-1", link_preview=False)

    assert fake.calls == [
        (
            "POST",
            "/api/sendText",
            {
                "session": "default",
                "chatId": "447700900123@c.us",
                "text": "Hello",
                "reply_to": "msg-1",
                "linkPreview": False,
            },
            None,
            "application/json",
        )
    ]


def test_list_chats_uses_live_gows_sort_field(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)

    api.list_chats(limit=1)

    assert fake.calls == [
        (
            "GET",
            "/api/default/chats",
            {
                "limit": 1,
                "offset": 0,
                "sortBy": "conversationTimestamp",
                "sortOrder": "desc",
            },
            "application/json",
        )
    ]


def test_query_encoding_uses_lowercase_booleans():
    query = WahaClient._encode_params(
        {"downloadMedia": False, "ids": ["a@c.us", "b@g.us"], "skip": None}
    )
    assert query == "downloadMedia=false&ids=a%40c.us&ids=b%40g.us"


def test_configured_timeout_is_parsed_and_invalid_value_uses_default(monkeypatch):
    monkeypatch.setenv("WAHA_TIMEOUT_S", "12.5")
    assert client._timeout() == 12.5
    monkeypatch.setenv("WAHA_TIMEOUT_S", "invalid")
    assert client._timeout() == 30.0


def test_qr_uses_control_client(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_control_client", lambda: fake)

    api.get_qr("default")

    assert fake.calls == [
        (
            "GET",
            "/api/default/auth/qr",
            {"format": "image"},
            "application/json",
        )
    ]


def test_send_file_url_accepts_only_public_http_targets(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)
    monkeypatch.setattr(
        api.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )

    api.send_file_url(
        "447700900123@c.us",
        "https://example.com/report.pdf",
        "report.pdf",
        "application/pdf",
    )

    assert fake.calls[0][2]["file"]["url"] == "https://example.com/report.pdf"


def test_send_file_url_rejects_private_or_non_http_targets(monkeypatch):
    monkeypatch.setattr(
        api.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("192.168.1.10", 80))],
    )

    for url in ("http://internal.example/file", "file:///etc/passwd"):
        try:
            api.send_file_url(
                "447700900123@c.us",
                url,
                "file.bin",
                "application/octet-stream",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {url}")


def test_send_video_url_uses_inline_video_endpoint(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)
    monkeypatch.setattr(
        api.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )

    api.send_video_url(
        "447700900123@c.us",
        "https://example.com/video.mp4",
        "clip.mp4",
        caption="Watch this",
        convert=False,
    )

    assert fake.calls == [
        (
            "POST",
            "/api/sendVideo",
            {
                "session": "default",
                "chatId": "447700900123@c.us",
                "file": {
                    "url": "https://example.com/video.mp4",
                    "filename": "clip.mp4",
                    "mimetype": "video/mp4",
                },
                "convert": False,
                "asNote": False,
                "caption": "Watch this",
            },
            None,
            "application/json",
        )
    ]


def test_send_video_url_rejects_private_or_non_http_targets(monkeypatch):
    monkeypatch.setattr(
        api.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("192.168.1.10", 80))],
    )

    for url in ("http://internal.example/video.mp4", "file:///tmp/video.mp4"):
        try:
            api.send_video_url("447700900123@c.us", url)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {url}")


def test_encode_local_file_detects_mime_and_encodes_data_url(tmp_path):
    source = tmp_path / "report.html"
    source.write_bytes(b"<h1>Private report</h1>")

    result = encode_local_file(str(source), filename="safe-report.html")

    assert result == {
        "data": base64.b64encode(b"<h1>Private report</h1>").decode("ascii"),
        "filename": "safe-report.html",
        "mimetype": "text/html",
    }


def test_encode_local_file_rejects_relative_empty_directory_symlink_and_oversize(
    tmp_path, monkeypatch
):
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    target = tmp_path / "target.bin"
    target.write_bytes(b"abc")
    link = tmp_path / "link.bin"
    link.symlink_to(target)
    large = tmp_path / "large.bin"
    large.write_bytes(b"abcd")
    monkeypatch.setenv("WAHA_LOCAL_FILE_MAX_BYTES", "3")

    for path in ("relative.bin", str(empty), str(tmp_path), str(link), str(large)):
        try:
            encode_local_file(path)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {path}")


def test_encode_local_file_rejects_unsafe_filename_and_mimetype(tmp_path):
    source = tmp_path / "file.bin"
    source.write_bytes(b"abc")

    for kwargs in (
        {"filename": "../secret.bin"},
        {"filename": "bad\nname.bin"},
        {"mimetype": "not a mime type"},
    ):
        try:
            encode_local_file(str(source), **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")


def test_send_file_local_posts_direct_data_url(monkeypatch, tmp_path):
    source = tmp_path / "report.html"
    source.write_bytes(b"report")
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)

    api.send_file_local(
        "447700900123@c.us",
        str(source),
        filename="shared-report.html",
        caption="Report",
    )

    assert fake.calls == [
        (
            "POST",
            "/api/sendFile",
            {
                "session": "default",
                "chatId": "447700900123@c.us",
                "file": {
                    "data": "cmVwb3J0",
                    "filename": "shared-report.html",
                    "mimetype": "text/html",
                },
                "caption": "Report",
            },
            None,
            "application/json",
        )
    ]


def test_local_media_tools_use_inline_endpoints(monkeypatch, tmp_path):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"jpg")
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"mp4")
    voice = tmp_path / "note.ogg"
    voice.write_bytes(b"ogg")

    api.send_image_local("447700900123@c.us", str(image))
    api.send_video_local("447700900123@c.us", str(video), convert=False)
    api.send_voice_local("447700900123@c.us", str(voice))

    assert [call[1] for call in fake.calls] == [
        "/api/sendImage",
        "/api/sendVideo",
        "/api/sendVoice",
    ]
    assert fake.calls[1][2]["convert"] is False
    assert fake.calls[1][2]["asNote"] is False
    assert fake.calls[2][2]["convert"] is True


def test_local_uploads_require_exact_chat_id_and_matching_media_type(
    monkeypatch, tmp_path
):
    fake = FakeClient()
    monkeypatch.setattr(api, "get_client", lambda: fake)
    source = tmp_path / "file.bin"
    source.write_bytes(b"abc")

    for chat_id in ("Jay", "447700900123", "all", "a b@c.us"):
        try:
            api.send_file_local(chat_id, str(source))
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {chat_id}")

    for function in (api.send_image_local, api.send_video_local, api.send_voice_local):
        try:
            function("447700900123@c.us", str(source))
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected MIME ValueError from {function.__name__}")
