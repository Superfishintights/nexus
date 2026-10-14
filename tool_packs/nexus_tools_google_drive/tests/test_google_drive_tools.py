from __future__ import annotations

import base64
import ast
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
for path in (PACKAGE_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from nexus_tools_google_drive import api
from nexus_tools_google_drive.client import DriveClient


EXPECTED_TOOL_CLASSES = {
    "approve_approval": "write",
    "cancel_approval": "write",
    "comment_approval": "write",
    "copy_file": "write",
    "create_comment": "write",
    "create_drive": "admin",
    "create_file_metadata": "write",
    "create_folder": "write",
    "create_permission": "admin",
    "create_reply": "write",
    "decline_approval": "write",
    "delete_comment": "destructive",
    "delete_drive": "destructive",
    "delete_file": "destructive",
    "delete_permission": "admin",
    "delete_reply": "destructive",
    "delete_revision": "destructive",
    "download_file": "read",
    "empty_trash": "destructive",
    "export_file": "read",
    "generate_file_ids": "read",
    "get_about": "read",
    "get_access_proposal": "read",
    "get_app": "read",
    "get_approval": "read",
    "get_comment": "read",
    "get_drive": "read",
    "get_file": "read",
    "get_operation": "read",
    "get_permission": "read",
    "get_reply": "read",
    "get_revision": "read",
    "get_start_page_token": "read",
    "hide_drive": "write",
    "list_access_proposals": "read",
    "list_approvals": "read",
    "list_apps": "read",
    "list_changes": "read",
    "list_comments": "read",
    "list_drives": "read",
    "list_file_labels": "read",
    "list_files": "read",
    "list_permissions": "read",
    "list_replies": "read",
    "list_revisions": "read",
    "modify_file_labels": "write",
    "move_file": "write",
    "reassign_approval": "write",
    "resolve_access_proposal": "admin",
    "search_files": "read",
    "share_file": "admin",
    "start_approval": "write",
    "stop_channel": "write",
    "trash_file": "destructive",
    "unhide_drive": "write",
    "untrash_file": "write",
    "update_comment": "write",
    "update_drive": "admin",
    "update_file_content": "write",
    "update_file_metadata": "write",
    "update_permission": "admin",
    "update_reply": "write",
    "update_revision": "write",
    "upload_file": "write",
    "watch_changes": "write",
}


class FakeGoogleClient:
    def __init__(self):
        self.calls = []

    def request_json(self, service, path, *, method="GET", params=None, body=None, headers=None):
        self.calls.append(
            {
                "kind": "json",
                "service": service,
                "path": path,
                "method": method,
                "params": params,
                "body": body,
                "headers": headers,
            }
        )
        return {"ok": True, "path": path, "params": params, "body": body}

    def request_bytes(self, service, path, *, method="GET", params=None, body=None, headers=None):
        self.calls.append(
            {
                "kind": "bytes",
                "service": service,
                "path": path,
                "method": method,
                "params": params,
                "body": body,
                "headers": headers,
            }
        )
        return {"contentBase64": base64.b64encode(b"payload").decode("ascii"), "size": 7}


def install_fake(monkeypatch):
    fake = FakeGoogleClient()
    monkeypatch.setattr(api, "get_client", lambda: DriveClient(fake))
    return fake


def test_all_registered_tools_have_explicit_expected_tool_class():
    source = (PACKAGE_ROOT / "nexus_tools_google_drive" / "api.py").read_text()
    tree = ast.parse(source)
    found = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if getattr(decorator.func, "id", getattr(decorator.func, "attr", "")) != "register_tool":
                continue
            keywords = {keyword.arg: keyword.value for keyword in decorator.keywords}
            assert keywords["namespace"].value == "google_drive"
            assert "tool_class" in keywords, node.name
            tool_class = keywords["tool_class"]
            assert isinstance(tool_class, ast.Constant), node.name
            found[node.name] = tool_class.value

    assert found == EXPECTED_TOOL_CLASSES


def test_search_files_builds_drive_query(monkeypatch):
    fake = install_fake(monkeypatch)

    result = api.search_files(q="name contains 'report'", page_size=5, drive_id="drive-1")

    assert result["path"] == "files"
    call = fake.calls[-1]
    assert call["service"] == "drive"
    assert call["method"] == "GET"
    assert call["params"]["q"] == "name contains 'report'"
    assert call["params"]["pageSize"] == 5
    assert call["params"]["supportsAllDrives"] is True
    assert call["params"]["includeItemsFromAllDrives"] is True


def test_update_file_metadata_merges_body_and_parent_params(monkeypatch):
    fake = install_fake(monkeypatch)

    api.update_file_metadata(
        "file/with space",
        name="New name",
        body={"description": "Current"},
        add_parents="folder2",
        remove_parents="folder1",
    )

    call = fake.calls[-1]
    assert call["path"] == "files/file%2Fwith%20space"
    assert call["method"] == "PATCH"
    assert call["body"] == {"description": "Current", "name": "New name"}
    assert call["params"]["addParents"] == "folder2"
    assert call["params"]["removeParents"] == "folder1"


def test_upload_file_uses_multipart_with_base64(monkeypatch):
    fake = install_fake(monkeypatch)

    api.upload_file(content_base64=base64.b64encode(b"hello").decode("ascii"), name="hello.txt", mime_type="text/plain")

    call = fake.calls[-1]
    assert call["path"] == "files"
    assert call["method"] == "POST"
    assert call["params"]["uploadType"] == "multipart"
    assert call["headers"]["Content-Type"].startswith("multipart/related; boundary=")
    assert b'"name":"hello.txt"' in call["body"]
    assert b"hello" in call["body"]


def test_download_and_export_request_bytes(monkeypatch):
    fake = install_fake(monkeypatch)

    assert api.download_file("file1")["size"] == 7
    assert fake.calls[-1]["kind"] == "bytes"
    assert fake.calls[-1]["path"] == "files/file1"
    assert fake.calls[-1]["params"]["alt"] == "media"

    assert api.export_file("doc1", "application/pdf")["size"] == 7
    assert fake.calls[-1]["path"] == "files/doc1/export"
    assert fake.calls[-1]["params"]["mimeType"] == "application/pdf"


def test_permissions_comments_replies_and_revisions_paths(monkeypatch):
    fake = install_fake(monkeypatch)

    api.create_permission("f", role="reader", email_address="a@example.com")
    assert fake.calls[-1]["path"] == "files/f/permissions"
    assert fake.calls[-1]["body"]["emailAddress"] == "a@example.com"

    api.create_comment("f", content="Review")
    assert fake.calls[-1]["path"] == "files/f/comments"
    assert fake.calls[-1]["body"] == {"content": "Review"}

    api.create_reply("f", "c", content="Done")
    assert fake.calls[-1]["path"] == "files/f/comments/c/replies"

    api.update_revision("f", "2", keep_forever=True)
    assert fake.calls[-1]["path"] == "files/f/revisions/2"
    assert fake.calls[-1]["body"] == {"keepForever": True}


def test_changes_drives_labels_and_misc_paths(monkeypatch):
    fake = install_fake(monkeypatch)

    api.get_start_page_token(drive_id="d")
    assert fake.calls[-1]["path"] == "changes/startPageToken"

    api.create_drive("req-1", name="Team")
    assert fake.calls[-1]["path"] == "drives"
    assert fake.calls[-1]["params"]["requestId"] == "req-1"

    api.modify_file_labels("f", body={"labelModifications": []})
    assert fake.calls[-1]["path"] == "files/f/modifyLabels"

    api.get_operation("operations/export-1")
    assert fake.calls[-1]["path"] == "operations/export-1"

    api.resolve_access_proposal("f", "p", body={})
    assert fake.calls[-1]["path"] == "files/f/accessproposals/p:resolve"

    api.approve_approval("f", "a", body={})
    assert fake.calls[-1]["path"] == "files/f/approvals/a:approve"
