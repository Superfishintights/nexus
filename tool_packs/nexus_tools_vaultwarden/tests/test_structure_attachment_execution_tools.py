from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

from nexus.tool_catalog import scan_package  # noqa: E402

from nexus_tools_vaultwarden import attachments, execution, structure  # noqa: E402


class MockClient:
    def __init__(self) -> None:
        self.calls: List[tuple[str, tuple[Any, ...], Dict[str, Any]]] = []

    def _record(self, name: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append((name, args, kwargs))
        return {"method": name, "args": args, "kwargs": kwargs}

    def move_item(
        self,
        item_id: str,
        *,
        purpose: str,
        folder_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self._record(
            "move_item",
            item_id,
            purpose=purpose,
            folder_id=folder_id,
            organization_id=organization_id,
            collection_ids=collection_ids,
        )

    def archive_item(self, item_id: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("archive_item", item_id, purpose=purpose)

    def restore_item(self, item_id: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("restore_item", item_id, purpose=purpose)

    def delete_item(self, item_id: str, *, purpose: str, permanent: bool = False) -> Dict[str, Any]:
        return self._record("delete_item", item_id, purpose=purpose, permanent=permanent)

    def list_folders(self, *, search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return self._record("list_folders", search=search, limit=limit)

    def create_folder(self, name: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("create_folder", name, purpose=purpose)

    def update_folder(self, folder_id: str, name: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("update_folder", folder_id, name, purpose=purpose)

    def delete_folder(self, folder_id: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("delete_folder", folder_id, purpose=purpose)

    def list_collections(self, *, organization_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        return self._record("list_collections", organization_id=organization_id, limit=limit)

    def assign_item_collections(self, item_id: str, collection_ids: List[str], *, purpose: str) -> Dict[str, Any]:
        return self._record("assign_item_collections", item_id, collection_ids, purpose=purpose)

    def list_attachments(self, item_id: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("list_attachments", item_id, purpose=purpose)

    def download_attachment(
        self,
        item_id: str,
        attachment_id: str,
        *,
        output_path: Optional[str] = None,
        purpose: str,
    ) -> Dict[str, Any]:
        return self._record(
            "download_attachment",
            item_id,
            attachment_id,
            output_path=output_path,
            purpose=purpose,
        )

    def upload_attachment(self, item_id: str, file_path: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("upload_attachment", item_id, file_path, purpose=purpose)

    def delete_attachment(self, item_id: str, attachment_id: str, *, purpose: str) -> Dict[str, Any]:
        return self._record("delete_attachment", item_id, attachment_id, purpose=purpose)

    def use_secret_with_command(
        self,
        selector: str,
        *,
        field: str,
        purpose: str,
        command: List[str],
        mode: str = "env",
        secret_env_name: str = "VAULTWARDEN_SECRET_VALUE",
        timeout_s: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._record(
            "use_secret_with_command",
            selector,
            field=field,
            purpose=purpose,
            command=command,
            mode=mode,
            secret_env_name=secret_env_name,
            timeout_s=timeout_s,
        )
        return {
            "returnCode": 0,
            "stdout": "redacted output",
            "stderr": "",
            "secretReturned": False,
        }


@pytest.fixture()
def mock_client(monkeypatch: pytest.MonkeyPatch) -> MockClient:
    client = MockClient()
    monkeypatch.setattr(structure, "get_client", lambda: client)
    monkeypatch.setattr(attachments, "get_client", lambda: client)
    monkeypatch.setattr(execution, "get_client", lambda: client)
    return client


def test_structure_tools_pass_exact_arguments_to_client(mock_client: MockClient) -> None:
    assert structure.move_item("item-id", purpose="organize", folder_id="folder-id")["method"] == "move_item"
    assert structure.archive_item("item-id", purpose="archive old")["method"] == "archive_item"
    assert structure.restore_item("item-id", purpose="restore needed")["method"] == "restore_item"
    assert structure.delete_item("item-id", purpose="trash duplicate")["kwargs"]["permanent"] is False
    assert structure.permanently_delete_item("item-id", purpose="purge duplicate")["kwargs"]["permanent"] is True
    assert structure.list_folders(search="work", limit=3)["kwargs"] == {"search": "work", "limit": 3}
    assert structure.create_folder("Work", purpose="organize")["args"] == ("Work",)
    assert structure.update_folder("folder-id", "New", purpose="rename")["args"] == ("folder-id", "New")
    assert structure.delete_folder("folder-id", purpose="cleanup")["method"] == "delete_folder"
    assert structure.list_collections(organization_id="org-id", limit=5)["kwargs"] == {
        "organization_id": "org-id",
        "limit": 5,
    }
    assert structure.assign_item_collections("item-id", ["collection-id"], purpose="share")["args"] == (
        "item-id",
        ["collection-id"],
    )


def test_attachment_and_execution_tools_pass_exact_arguments_to_client(mock_client: MockClient) -> None:
    assert attachments.list_attachments("item-id", purpose="inspect")["method"] == "list_attachments"
    assert attachments.download_attachment(
        "item-id",
        "attachment-id",
        output_path="/tmp/out",
        purpose="download",
    )["kwargs"] == {"output_path": "/tmp/out", "purpose": "download"}
    assert attachments.upload_attachment("item-id", "/tmp/in", purpose="upload")["args"] == ("item-id", "/tmp/in")
    assert attachments.delete_attachment("item-id", "attachment-id", purpose="remove")["method"] == "delete_attachment"

    result = execution.use_secret_with_command(
        "alias:github",
        field="password",
        command=["gh", "auth", "status"],
        purpose="check auth",
        mode="stdin",
        timeout_s=1.5,
    )
    assert result["secretReturned"] is False
    assert "secret" not in result["stdout"]
    assert mock_client.calls[-1] == (
        "use_secret_with_command",
        ("alias:github",),
        {
            "field": "password",
            "purpose": "check auth",
            "command": ["gh", "auth", "status"],
            "mode": "stdin",
            "secret_env_name": "VAULTWARDEN_SECRET_VALUE",
            "timeout_s": 1.5,
        },
    )


@pytest.mark.parametrize(
    ("func", "args"),
    [
        (structure.archive_item, ("item-id",)),
        (structure.delete_item, ("item-id",)),
        (structure.permanently_delete_item, ("item-id",)),
        (structure.create_folder, ("Work",)),
        (attachments.list_attachments, ("item-id",)),
        (execution.use_secret_with_command, ("alias:github",)),
    ],
)
def test_write_destructive_and_secret_helpers_require_purpose(
    mock_client: MockClient,
    func: Any,
    args: tuple[Any, ...],
) -> None:
    kwargs: Dict[str, Any] = {"purpose": " "}
    if func is execution.use_secret_with_command:
        kwargs.update({"field": "password", "command": ["allowed"]})

    with pytest.raises(ValueError, match="purpose is required"):
        func(*args, **kwargs)

    assert mock_client.calls == []


def test_ast_catalog_metadata_for_vaultwarden_tools() -> None:
    package_path = PACKAGE_ROOT / "nexus_tools_vaultwarden"
    specs = {spec.name: spec for spec in scan_package("nexus_tools_vaultwarden", package_path)}

    expected = {
        "vaultwarden.move_item",
        "vaultwarden.archive_item",
        "vaultwarden.restore_item",
        "vaultwarden.delete_item",
        "vaultwarden.permanently_delete_item",
        "vaultwarden.list_folders",
        "vaultwarden.create_folder",
        "vaultwarden.update_folder",
        "vaultwarden.delete_folder",
        "vaultwarden.list_collections",
        "vaultwarden.assign_item_collections",
        "vaultwarden.list_attachments",
        "vaultwarden.download_attachment",
        "vaultwarden.upload_attachment",
        "vaultwarden.delete_attachment",
        "vaultwarden.use_secret_with_command",
    }
    assert expected.issubset(specs)

    for name in [
        "vaultwarden.delete_item",
        "vaultwarden.permanently_delete_item",
        "vaultwarden.delete_folder",
        "vaultwarden.delete_attachment",
    ]:
        assert specs[name].tool_class == "destructive"

    for name in [
        "vaultwarden.move_item",
        "vaultwarden.archive_item",
        "vaultwarden.restore_item",
        "vaultwarden.create_folder",
        "vaultwarden.update_folder",
        "vaultwarden.assign_item_collections",
        "vaultwarden.upload_attachment",
        "vaultwarden.use_secret_with_command",
    ]:
        assert specs[name].tool_class == "write"
