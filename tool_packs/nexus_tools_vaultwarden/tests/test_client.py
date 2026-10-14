from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nexus_tools_vaultwarden.client import (  # noqa: E402
    BroadQueryError,
    VaultwardenClient,
    _redact_text,
    redact_payload,
    sanitize_item,
)


ITEM_ID = "11111111-2222-3333-4444-555555555555"


class RunRecorder:
    def __init__(self, responses: list[tuple[str, str, int]]):
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def __call__(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append({"args": args, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError(f"Unexpected subprocess call: {args}")
        stdout, stderr, returncode = self.responses.pop(0)
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)


def make_client(tmp_path: Path) -> VaultwardenClient:
    password_file = tmp_path / "master-password"
    password_file.write_text("not-used-by-tests", encoding="utf-8")
    return VaultwardenClient(
        bw_path="/usr/bin/bw",
        password_file=password_file,
        aliases_file=tmp_path / "aliases.json",
        audit_file=tmp_path / "audit.jsonl",
    )


def test_find_items_blocks_broad_query(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    with pytest.raises(BroadQueryError):
        client.find_items()


def test_unlock_session_is_passed_without_secret_in_argv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recorder = RunRecorder(
        [
            ("SESSIONSECRET\n", "", 0),
            (json.dumps([]), "", 0),
        ]
    )
    monkeypatch.setattr(subprocess, "run", recorder)
    client = make_client(tmp_path)

    result = client.list_folders()

    assert result["folders"] == []
    assert recorder.calls[0]["args"] == [
        "/usr/bin/bw",
        "unlock",
        "--passwordfile",
        str(client.password_file),
        "--raw",
        "--nointeraction",
    ]
    assert "--session" in recorder.calls[1]["args"]
    assert "SESSIONSECRET" in recorder.calls[1]["args"]
    assert "not-used-by-tests" not in " ".join(recorder.calls[0]["args"])


def test_stale_session_retries_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recorder = RunRecorder(
        [
            ("OLDSESSION\n", "", 0),
            ("", "Vault is locked.", 1),
            ("NEWSESSION\n", "", 0),
            (json.dumps([]), "", 0),
        ]
    )
    monkeypatch.setattr(subprocess, "run", recorder)
    client = make_client(tmp_path)

    result = client.list_folders()

    assert result["count"] == 0
    assert recorder.calls[0]["args"][1] == "unlock"
    assert recorder.calls[2]["args"][1] == "unlock"
    assert recorder.calls[3]["args"][-1] == "NEWSESSION"


def test_redaction_helpers_remove_secret_material() -> None:
    redacted = _redact_text("failed --session SECRET BW_SESSION=ABC password", ["SECRET", "password"])
    payload = redact_payload({"login": {"password": "secret"}, "name": "safe"})

    assert "SECRET" not in redacted
    assert "ABC" not in redacted
    assert "password" not in redacted
    assert payload == {"login": {"password": "[REDACTED]"}, "name": "safe"}


def test_schema_sanitization_hides_secret_values(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    payload = client.build_login_payload(
        name="Example",
        username="user@example.com",
        password="secret-password",
        url="https://example.com",
        fields=[{"name": "api key", "value": "secret-key", "type": "hidden"}],
    )
    safe = sanitize_item({"id": ITEM_ID, **payload})

    assert payload["type"] == 1
    assert payload["login"]["password"] == "secret-password"
    assert safe["login"]["hasPassword"] is True
    assert "secret-password" not in json.dumps(safe)
    assert "secret-key" not in json.dumps(safe)


def test_create_item_command_uses_encoded_json_not_raw_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recorder = RunRecorder(
        [
            ("ENCODED\n", "", 0),
            ("SESSIONSECRET\n", "", 0),
            (
                json.dumps(
                    {
                        "id": ITEM_ID,
                        "type": 1,
                        "name": "Example",
                        "login": {"username": "u", "password": "secret"},
                    }
                ),
                "",
                0,
            ),
        ]
    )
    monkeypatch.setattr(subprocess, "run", recorder)
    client = make_client(tmp_path)

    result = client.create_item(client.build_login_payload(name="Example", password="secret"))

    assert result["id"] == ITEM_ID
    assert recorder.calls[0]["args"][1] == "encode"
    assert "secret" in recorder.calls[0]["kwargs"]["input"]
    create_argv = " ".join(recorder.calls[2]["args"])
    assert "ENCODED" in create_argv
    assert "secret" not in create_argv


def test_destructive_delete_requires_exact_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    with pytest.raises(ValueError, match="exact Bitwarden item id"):
        client.delete_item("not-an-id", purpose="test", permanent=True)
