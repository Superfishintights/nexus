from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest import mock

from nexus_tools_google_gmail import messages
from nexus_tools_google_gmail.client import decode_base64url, encode_base64url, extract_text_parts, user_path
from nexus_tools_google_gmail.mime import build_raw_message


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "nexus_tools_google_gmail"

EXPECTED_TOOL_CLASSES = {
    "batch_delete_messages_permanently": "destructive",
    "batch_modify_messages": "write",
    "create_draft": "write",
    "create_filter": "write",
    "create_label": "write",
    "delete_draft": "destructive",
    "delete_filter": "destructive",
    "delete_label": "destructive",
    "delete_message_permanently": "destructive",
    "delete_thread_permanently": "destructive",
    "get_attachment": "read",
    "get_draft": "read",
    "get_filter": "read",
    "get_imap": "read",
    "get_label": "read",
    "get_language": "read",
    "get_message": "read",
    "get_message_headers": "read",
    "get_message_text": "read",
    "get_pop": "read",
    "get_profile": "read",
    "get_send_as": "read",
    "get_thread": "read",
    "get_thread_text": "read",
    "get_vacation": "read",
    "list_drafts": "read",
    "list_filters": "read",
    "list_forwarding_addresses": "read",
    "list_history": "read",
    "list_labels": "read",
    "list_messages": "read",
    "list_send_as": "read",
    "list_threads": "read",
    "modify_message_labels": "write",
    "modify_thread_labels": "write",
    "patch_label": "write",
    "patch_send_as": "write",
    "reply_to_thread": "write",
    "send_draft": "write",
    "send_message": "write",
    "stop_watch": "admin",
    "trash_message": "destructive",
    "trash_thread": "destructive",
    "untrash_message": "write",
    "untrash_thread": "write",
    "update_draft": "write",
    "update_imap": "write",
    "update_label": "write",
    "update_language": "write",
    "update_pop": "write",
    "update_vacation": "write",
    "watch_mailbox": "admin",
}


def _registered_tool_classes() -> dict[str, str]:
    classes: dict[str, str] = {}
    for path in PACKAGE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not (isinstance(decorator.func, ast.Name) and decorator.func.id == "register_tool"):
                    continue
                tool_class = None
                for keyword in decorator.keywords:
                    if keyword.arg == "tool_class":
                        tool_class = keyword.value
                        break
                if not isinstance(tool_class, ast.Constant) or not isinstance(tool_class.value, str):
                    raise AssertionError(f"{path.name}:{node.name} is missing a literal string tool_class")
                classes[node.name] = tool_class.value
    return classes


class GmailHelperTests(unittest.TestCase):
    def test_tool_classifications_are_explicit_and_security_accurate(self) -> None:
        self.assertEqual(_registered_tool_classes(), EXPECTED_TOOL_CLASSES)

    def test_base64url_roundtrip_without_padding(self) -> None:
        encoded = encode_base64url(b"hello?")
        self.assertNotIn("=", encoded)
        self.assertEqual(decode_base64url(encoded), b"hello?")

    def test_user_path_quotes_segments(self) -> None:
        self.assertEqual(user_path("me@example.com", "messages/a b"), "users/me@example.com/messages/a b")

    def test_build_raw_message_has_expected_headers(self) -> None:
        raw = build_raw_message(to="to@example.com", subject="Hi", body="Hello", from_address="me@example.com")
        decoded = decode_base64url(raw).decode("utf-8", errors="replace")
        self.assertIn("To: to@example.com", decoded)
        self.assertIn("Subject: Hi", decoded)
        self.assertIn("Hello", decoded)

    def test_extract_text_parts_handles_nested_payload(self) -> None:
        message = {
            "id": "m1",
            "threadId": "t1",
            "payload": {
                "headers": [{"name": "Subject", "value": "Hi"}],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": encode_base64url(b"Plain")}},
                    {
                        "mimeType": "multipart/mixed",
                        "parts": [
                            {"filename": "a.txt", "mimeType": "text/plain", "body": {"attachmentId": "att1", "size": 5}},
                            {"mimeType": "text/html", "body": {"data": encode_base64url(b"<b>Html</b>")}},
                        ],
                    },
                ],
            },
        }
        result = extract_text_parts(message)
        self.assertEqual(result["textPlain"], "Plain")
        self.assertEqual(result["textHtml"], "<b>Html</b>")
        self.assertEqual(result["attachments"][0]["attachmentId"], "att1")

    @mock.patch("nexus_tools_google_gmail.messages.gmail_request")
    def test_list_messages_request_shape(self, gmail_request: mock.Mock) -> None:
        gmail_request.return_value = {"messages": []}
        result = messages.list_messages(query="from:me", label_ids=["INBOX", "UNREAD"])
        self.assertEqual(result, {"messages": []})
        gmail_request.assert_called_once_with(
            "users/me/messages",
            params={
                "q": "from:me",
                "maxResults": None,
                "pageToken": None,
                "includeSpamTrash": False,
                "labelIds": ["INBOX", "UNREAD"],
            },
        )

    @mock.patch("nexus_tools_google_gmail.messages.gmail_request")
    def test_send_message_marks_payload(self, gmail_request: mock.Mock) -> None:
        gmail_request.return_value = {"id": "sent"}
        result = messages.send_message(to="to@example.com", subject="Hi", body="Hello", thread_id="t1")
        self.assertEqual(result, {"id": "sent"})
        _, kwargs = gmail_request.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["payload"]["threadId"], "t1")
        self.assertIn("raw", kwargs["payload"])


if __name__ == "__main__":
    unittest.main()
