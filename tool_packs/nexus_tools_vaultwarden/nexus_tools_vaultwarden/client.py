"""Shared Vaultwarden client built on the official Bitwarden `bw` CLI."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from nexus.config import get_setting

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "bitwarden-codex"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "bitwarden-codex"
DEFAULT_PASSWORD_FILE = DEFAULT_CONFIG_DIR / "master-password"
DEFAULT_ALIASES_FILE = DEFAULT_CONFIG_DIR / "aliases.json"
DEFAULT_AUDIT_FILE = DEFAULT_STATE_DIR / "audit.jsonl"
DEFAULT_ATTACHMENTS_DIR = DEFAULT_STATE_DIR / "attachments"
DEFAULT_TIMEOUT_S = 45.0
MAX_FIND_LIMIT = 50

ITEM_TYPE_TO_ID = {
    "login": 1,
    "secure_note": 2,
    "secureNote": 2,
    "note": 2,
    "card": 3,
    "identity": 4,
}
ITEM_ID_TO_TYPE = {1: "login", 2: "secure_note", 3: "card", 4: "identity"}

FIELD_TYPES = {
    "text": 0,
    "hidden": 1,
    "boolean": 2,
    "linked": 3,
}

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STALE_SESSION_MARKERS = (
    "invalid session",
    "session key is invalid",
    "vault is locked",
    "not logged in",
    "unauthorized",
    "you are not logged in",
)
SECRET_KEY_HINTS = {
    "password",
    "totp",
    "notes",
    "code",
    "number",
    "securitycode",
    "value",
    "session",
    "clientsecret",
    "token",
    "key",
}


class VaultwardenError(RuntimeError):
    """Raised when the Bitwarden CLI fails in a redacted way."""


class BroadQueryError(ValueError):
    """Raised when a query would enumerate too much of the vault."""


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def _setting_path(name: str, default: Path) -> Path:
    raw = get_setting(name)
    return Path(raw).expanduser() if raw else default


def _float_setting(name: str, default: float) -> float:
    raw = get_setting(name)
    if raw in (None, ""):
        return default
    try:
        return float(str(raw))
    except ValueError:
        return default


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _short_hash(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _is_exact_id(value: str) -> bool:
    return bool(UUID_RE.fullmatch(value.strip()))


def _compact_error(text: str) -> str:
    return " ".join((text or "").strip().split())


def _redact_text(value: str, secrets: Iterable[Optional[str]] = ()) -> str:
    redacted = value or ""
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(r"BW_SESSION=[^\s]+", "BW_SESSION=[REDACTED]", redacted)
    redacted = re.sub(r"--session\s+\S+", "--session [REDACTED]", redacted)
    return redacted


def _secretish_key(key: str) -> bool:
    lowered = key.replace("_", "").replace("-", "").lower()
    return any(hint in lowered for hint in SECRET_KEY_HINTS)


def redact_payload(payload: Any) -> Any:
    """Return a JSON-serializable copy with obvious secret values redacted."""

    if isinstance(payload, Mapping):
        result: Dict[str, Any] = {}
        for key, value in payload.items():
            if _secretish_key(str(key)):
                result[str(key)] = "[REDACTED]" if isinstance(value, str) and value else value
            else:
                result[str(key)] = redact_payload(value)
        return result
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    return payload


def normalize_item_type(item_type: str | int) -> int:
    if isinstance(item_type, int):
        if item_type in ITEM_ID_TO_TYPE:
            return item_type
        raise ValueError(f"Unsupported item type id: {item_type}")
    normalized = item_type.strip()
    if normalized not in ITEM_TYPE_TO_ID:
        raise ValueError(f"Unsupported item type: {item_type}")
    return ITEM_TYPE_TO_ID[normalized]


def normalize_custom_fields(fields: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for field in fields or []:
        name = str(field.get("name") or "").strip()
        if not name:
            raise ValueError("Custom field name is required")
        raw_type = field.get("type", "text")
        if isinstance(raw_type, int):
            field_type = raw_type
        else:
            field_type = FIELD_TYPES.get(str(raw_type).strip().lower())
        if field_type not in FIELD_TYPES.values():
            raise ValueError(f"Unsupported custom field type for {name!r}")
        item: Dict[str, Any] = {"name": name, "type": field_type}
        if field_type == FIELD_TYPES["linked"]:
            if "linkedId" not in field and "linked_id" not in field:
                raise ValueError("Linked custom fields require linkedId")
            item["linkedId"] = field.get("linkedId", field.get("linked_id"))
        else:
            value = field.get("value")
            if field_type == FIELD_TYPES["boolean"] and isinstance(value, bool):
                value = "true" if value else "false"
            item["value"] = "" if value is None else str(value)
        normalized.append(item)
    return normalized


def _clean_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _summarize_uri(uri: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "uri": uri.get("uri"),
        "match": uri.get("match"),
    }


def _summarize_attachment(attachment: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "id": attachment.get("id"),
        "fileName": attachment.get("fileName"),
        "size": attachment.get("size"),
        "sizeName": attachment.get("sizeName"),
        "url": attachment.get("url"),
    }


def sanitize_item(
    item: Mapping[str, Any],
    *,
    selected_secrets: Optional[Mapping[str, Any]] = None,
    include_notes: bool = False,
) -> Dict[str, Any]:
    """Return item metadata without password/card/custom-field values by default."""

    item_type = item.get("type")
    login = item.get("login") or {}
    card = item.get("card") or {}
    identity = item.get("identity") or {}
    attachments = item.get("attachments") or []
    fields = item.get("fields") or []

    safe: Dict[str, Any] = {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": item_type,
        "typeName": ITEM_ID_TO_TYPE.get(item_type, str(item_type)),
        "folderId": item.get("folderId"),
        "organizationId": item.get("organizationId"),
        "collectionIds": item.get("collectionIds") or [],
        "favorite": item.get("favorite"),
        "deletedDate": item.get("deletedDate"),
        "revisionDate": item.get("revisionDate"),
        "creationDate": item.get("creationDate"),
        "archivedDate": item.get("archivedDate"),
        "hasNotes": bool(item.get("notes")),
        "hasAttachments": bool(attachments),
        "attachmentCount": len(attachments),
        "customFields": [
            {
                "name": field.get("name"),
                "type": field.get("type"),
                "hasValue": bool(field.get("value") or field.get("linkedId")),
            }
            for field in fields
        ],
    }
    if item_type == 1:
        safe["login"] = {
            "username": login.get("username"),
            "uris": [_summarize_uri(uri) for uri in login.get("uris") or []],
            "hasPassword": bool(login.get("password")),
            "hasTotp": bool(login.get("totp")),
        }
    elif item_type == 3:
        safe["card"] = {
            "cardholderName": card.get("cardholderName"),
            "brand": card.get("brand"),
            "expMonth": card.get("expMonth"),
            "expYear": card.get("expYear"),
            "hasNumber": bool(card.get("number")),
            "hasCode": bool(card.get("code")),
        }
    elif item_type == 4:
        safe["identity"] = {
            "title": identity.get("title"),
            "firstName": identity.get("firstName"),
            "middleName": identity.get("middleName"),
            "lastName": identity.get("lastName"),
            "company": identity.get("company"),
            "email": identity.get("email"),
            "username": identity.get("username"),
            "address1": identity.get("address1"),
            "address2": identity.get("address2"),
            "address3": identity.get("address3"),
            "city": identity.get("city"),
            "state": identity.get("state"),
            "postalCode": identity.get("postalCode"),
            "country": identity.get("country"),
            "phone": identity.get("phone"),
            "ssnPresent": bool(identity.get("ssn")),
            "passportNumberPresent": bool(identity.get("passportNumber")),
            "licenseNumberPresent": bool(identity.get("licenseNumber")),
        }
    if include_notes:
        safe["notes"] = item.get("notes")
    if attachments:
        safe["attachments"] = [_summarize_attachment(attachment) for attachment in attachments]
    if selected_secrets:
        safe["selectedSecrets"] = dict(selected_secrets)
    return safe


class VaultwardenClient:
    """Small, secret-aware wrapper around the official Bitwarden CLI."""

    def __init__(
        self,
        *,
        bw_path: Optional[str] = None,
        password_file: Optional[Path] = None,
        aliases_file: Optional[Path] = None,
        audit_file: Optional[Path] = None,
        timeout_s: Optional[float] = None,
    ):
        self.bw_path = bw_path or get_setting("VAULTWARDEN_BW_PATH") or shutil.which("bw") or "/usr/bin/bw"
        self.password_file = password_file or _setting_path("VAULTWARDEN_PASSWORD_FILE", DEFAULT_PASSWORD_FILE)
        self.aliases_file = aliases_file or _setting_path("VAULTWARDEN_ALIASES_FILE", DEFAULT_ALIASES_FILE)
        self.audit_file = audit_file or _setting_path("VAULTWARDEN_AUDIT_FILE", DEFAULT_AUDIT_FILE)
        self.timeout_s = timeout_s if timeout_s is not None else _float_setting("VAULTWARDEN_TIMEOUT_S", DEFAULT_TIMEOUT_S)
        self.attachments_dir = _setting_path("VAULTWARDEN_ATTACHMENTS_DIR", DEFAULT_ATTACHMENTS_DIR)
        self._session: Optional[str] = None

    def _bw_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        xdg_config_home = get_setting("VAULTWARDEN_XDG_CONFIG_HOME")
        if xdg_config_home:
            env["XDG_CONFIG_HOME"] = str(Path(xdg_config_home).expanduser())
        appdata_dir = get_setting("VAULTWARDENCLI_APPDATA_DIR")
        if appdata_dir:
            env["BITWARDENCLI_APPDATA_DIR"] = str(Path(appdata_dir).expanduser())
        return env

    def audit(
        self,
        *,
        tool: str,
        operation: str,
        purpose: Optional[str] = None,
        item_id: Optional[str] = None,
        alias: Optional[str] = None,
        field: Optional[str] = None,
        result: str = "success",
        error_class: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        event = {
            "timestamp": _now(),
            "tool": tool,
            "operation": operation,
            "purpose": purpose,
            "itemIdHash": _short_hash(item_id),
            "alias": alias,
            "field": field,
            "result": result,
            "errorClass": error_class,
            "metadata": redact_payload(dict(metadata or {})),
        }
        self.audit_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.audit_file.exists():
            self.audit_file.touch(mode=0o600)
        with self.audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")

    def _run(
        self,
        args: Sequence[str],
        *,
        input_text: Optional[str] = None,
        session_required: bool = False,
        allow_retry: bool = True,
    ) -> CommandResult:
        session = self.ensure_session() if session_required else None
        full_args = [self.bw_path, *args, "--nointeraction"]
        if session:
            full_args.extend(["--session", session])
        process = subprocess.run(
            full_args,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=self.timeout_s,
            check=False,
            env=self._bw_env(),
        )
        stdout = _redact_text(process.stdout, [self._session])
        stderr = _redact_text(process.stderr, [self._session])
        if process.returncode == 0:
            return CommandResult(stdout=stdout, stderr=stderr, returncode=0)

        combined = f"{stdout}\n{stderr}".lower()
        if session_required and allow_retry and any(marker in combined for marker in STALE_SESSION_MARKERS):
            self._session = None
            return self._run(args, input_text=input_text, session_required=True, allow_retry=False)

        raise VaultwardenError(_compact_error(stderr or stdout or f"bw exited {process.returncode}"))

    def _run_json(self, args: Sequence[str], *, session_required: bool = True) -> Any:
        result = self._run(args, session_required=session_required)
        if not result.stdout.strip():
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise VaultwardenError("bw returned invalid JSON") from exc

    def _encode_json(self, payload: Any) -> str:
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        result = self._run(["encode"], input_text=raw, session_required=False)
        encoded = result.stdout.strip()
        if not encoded:
            raise VaultwardenError("bw encode returned no data")
        return encoded

    def ensure_session(self) -> str:
        if self._session:
            status = self.status(use_session=True)
            if status.get("status") == "unlocked":
                return self._session
            self._session = None

        if not self.password_file.exists():
            raise VaultwardenError(f"Vaultwarden password file is missing: {self.password_file}")
        result = self._run(
            ["unlock", "--passwordfile", str(self.password_file), "--raw"],
            session_required=False,
            allow_retry=False,
        )
        session = result.stdout.strip()
        if not session:
            raise VaultwardenError("bw unlock returned no session")
        self._session = session
        return session

    def status(self, *, use_session: bool = False) -> Dict[str, Any]:
        version_result = self._run(["--version"], session_required=False, allow_retry=False)
        args = ["status"]
        if use_session and self._session:
            args.extend(["--session", self._session])
        result = self._run(args, session_required=False, allow_retry=False)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise VaultwardenError("bw status returned invalid JSON") from exc
        payload["cliVersion"] = version_result.stdout.strip()
        payload["passwordFileConfigured"] = self.password_file.exists()
        payload["auditFile"] = str(self.audit_file)
        return redact_payload(payload)

    def sync(self, *, purpose: str = "explicit sync") -> Dict[str, Any]:
        self._run(["sync"], session_required=True)
        status = self.status(use_session=True)
        self.audit(tool="vaultwarden.sync", operation="sync", purpose=purpose)
        return {"synced": True, "status": status}

    def lock(self, *, purpose: str = "explicit lock") -> Dict[str, Any]:
        try:
            self._run(["lock"], session_required=bool(self._session), allow_retry=False)
        finally:
            self._session = None
        self.audit(tool="vaultwarden.lock", operation="lock", purpose=purpose)
        return {"locked": True, "status": self.status()}

    def aliases(self) -> Dict[str, Any]:
        if not self.aliases_file.exists():
            return {}
        try:
            payload = json.loads(self.aliases_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise VaultwardenError(f"Invalid aliases JSON: {self.aliases_file}") from exc
        if isinstance(payload, dict) and "aliases" in payload and isinstance(payload["aliases"], dict):
            return dict(payload["aliases"])
        if isinstance(payload, dict):
            return dict(payload)
        raise VaultwardenError("aliases.json must be an object")

    def resolve_selector(self, selector: str, *, allow_alias: bool = True) -> tuple[str, Optional[str]]:
        value = selector.strip()
        if not value:
            raise ValueError("An item id or alias is required")
        if value.startswith("alias:"):
            value = value.split(":", 1)[1].strip()
            if not value:
                raise ValueError("Alias name is required")
        if _is_exact_id(value):
            return value, None
        if allow_alias:
            alias_value = self.aliases().get(value)
            if isinstance(alias_value, str) and _is_exact_id(alias_value):
                return alias_value, value
            if isinstance(alias_value, Mapping):
                item_id = str(alias_value.get("itemId") or alias_value.get("id") or "")
                if _is_exact_id(item_id):
                    return item_id, value
        raise ValueError("Selector must be an exact item id or configured alias")

    def require_exact_item_id(self, item_id: str) -> str:
        value = item_id.strip()
        if not _is_exact_id(value):
            raise ValueError("This operation requires an exact Bitwarden item id")
        return value

    def require_exact_folder_id(self, folder_id: str) -> str:
        value = folder_id.strip()
        if not _is_exact_id(value):
            raise ValueError("This operation requires an exact Bitwarden folder id")
        return value

    def find_items(
        self,
        *,
        search: Optional[str] = None,
        url: Optional[str] = None,
        folder_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        include_trash: bool = False,
        include_archived: bool = False,
        item_types: Optional[List[str]] = None,
        limit: int = 10,
        allow_all: bool = False,
    ) -> Dict[str, Any]:
        constrained = any([search, url, folder_id, collection_id, organization_id, include_trash, include_archived])
        if not constrained and not allow_all:
            raise BroadQueryError("Refusing broad vault enumeration; pass a search/filter or explicit allow_all=True")
        if search is not None and len(search.strip()) < 3:
            raise BroadQueryError("Search terms must be at least 3 characters")
        capped_limit = max(1, min(int(limit), MAX_FIND_LIMIT))
        args = ["list", "items"]
        if search:
            args.extend(["--search", search])
        if url:
            args.extend(["--url", url])
        if folder_id:
            args.extend(["--folderid", folder_id])
        if collection_id:
            args.extend(["--collectionid", collection_id])
        if organization_id:
            args.extend(["--organizationid", organization_id])
        if include_trash:
            args.append("--trash")
        if include_archived:
            args.append("--archived")
        items = self._run_json(args, session_required=True) or []
        requested_types = {normalize_item_type(item_type) for item_type in item_types or []}
        if requested_types:
            items = [item for item in items if item.get("type") in requested_types]
        safe_items = [sanitize_item(item) for item in items[:capped_limit]]
        self.audit(
            tool="vaultwarden.find_items",
            operation="find_items",
            metadata={"search": bool(search), "url": bool(url), "resultCount": len(safe_items), "truncated": len(items) > capped_limit},
        )
        return {
            "count": len(safe_items),
            "totalMatched": len(items),
            "truncated": len(items) > capped_limit,
            "limit": capped_limit,
            "items": safe_items,
        }

    def get_raw_item(self, item_id: str) -> Dict[str, Any]:
        return self._run_json(["get", "item", item_id], session_required=True)

    def get_item(
        self,
        selector: str,
        *,
        include_secret_fields: bool = False,
        field_selectors: Optional[List[str]] = None,
        purpose: Optional[str] = None,
    ) -> Dict[str, Any]:
        item_id, alias = self.resolve_selector(selector)
        if include_secret_fields and not purpose:
            raise ValueError("purpose is required when returning selected secret fields")
        raw = self.get_raw_item(item_id)
        selected: Dict[str, Any] = {}
        if include_secret_fields:
            for field in field_selectors or []:
                selected[field] = self.extract_field(raw, field)
        self.audit(
            tool="vaultwarden.get_item",
            operation="get_item",
            purpose=purpose,
            item_id=item_id,
            alias=alias,
            metadata={"includeSecretFields": include_secret_fields, "fieldCount": len(selected)},
        )
        return sanitize_item(raw, selected_secrets=selected or None)

    def extract_field(self, item: Mapping[str, Any], field: str) -> Any:
        normalized = field.strip()
        if not normalized:
            raise ValueError("field selector is required")
        login = item.get("login") or {}
        card = item.get("card") or {}
        identity = item.get("identity") or {}
        lookup = {
            "password": login.get("password"),
            "login.password": login.get("password"),
            "username": login.get("username"),
            "login.username": login.get("username"),
            "notes": item.get("notes"),
            "card.number": card.get("number"),
            "card.code": card.get("code"),
            "card.exp_month": card.get("expMonth"),
            "card.exp_year": card.get("expYear"),
            "identity.ssn": identity.get("ssn"),
            "identity.passport_number": identity.get("passportNumber"),
            "identity.license_number": identity.get("licenseNumber"),
            "identity.email": identity.get("email"),
            "identity.phone": identity.get("phone"),
        }
        if normalized in lookup:
            return lookup[normalized]
        if normalized.startswith("custom:"):
            wanted = normalized.split(":", 1)[1]
            for custom_field in item.get("fields") or []:
                if custom_field.get("name") == wanted:
                    return custom_field.get("value") or custom_field.get("linkedId")
            raise KeyError(f"Custom field not found: {wanted}")
        raise ValueError(f"Unsupported field selector: {field}")

    def get_secret(self, selector: str, *, field: str, purpose: str) -> Dict[str, Any]:
        if not purpose:
            raise ValueError("purpose is required")
        item_id, alias = self.resolve_selector(selector)
        raw = self.get_raw_item(item_id)
        value = self.extract_field(raw, field)
        self.audit(
            tool="vaultwarden.get_secret",
            operation="get_secret",
            purpose=purpose,
            item_id=item_id,
            alias=alias,
            field=field,
            metadata={"returned": value is not None},
        )
        return {"itemId": item_id, "alias": alias, "field": field, "value": value}

    def get_totp(self, selector: str, *, purpose: str) -> Dict[str, Any]:
        if not purpose:
            raise ValueError("purpose is required")
        item_id, alias = self.resolve_selector(selector)
        result = self._run(["get", "totp", item_id], session_required=True)
        code = result.stdout.strip()
        self.audit(
            tool="vaultwarden.get_totp",
            operation="get_totp",
            purpose=purpose,
            item_id=item_id,
            alias=alias,
            field="totp",
            metadata={"returned": bool(code)},
        )
        return {"itemId": item_id, "alias": alias, "totp": code}

    def create_item(self, payload: Dict[str, Any], *, purpose: str = "create item") -> Dict[str, Any]:
        self.validate_item_payload(payload)
        encoded = self._encode_json(payload)
        created = self._run_json(["create", "item", encoded], session_required=True)
        item_id = created.get("id") if isinstance(created, Mapping) else None
        self.audit(tool="vaultwarden.create_item", operation="create_item", purpose=purpose, item_id=item_id)
        return sanitize_item(created)

    def edit_item(self, item_id: str, payload: Dict[str, Any], *, tool: str, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        self.validate_item_payload(payload)
        encoded = self._encode_json(payload)
        updated = self._run_json(["edit", "item", exact_id, encoded], session_required=True)
        self.audit(tool=tool, operation="edit_item", purpose=purpose, item_id=exact_id)
        return sanitize_item(updated)

    def validate_item_payload(self, payload: Mapping[str, Any]) -> None:
        if not str(payload.get("name") or "").strip():
            raise ValueError("Item name is required")
        normalize_item_type(payload.get("type"))

    def build_login_payload(
        self,
        *,
        name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        uris: Optional[List[Dict[str, Any]]] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        folder_id: Optional[str] = None,
        favorite: bool = False,
        fields: Optional[List[Dict[str, Any]]] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
        totp: Optional[str] = None,
    ) -> Dict[str, Any]:
        login_uris = list(uris or [])
        if url:
            login_uris.append({"uri": url})
        return _clean_none(
            {
                "type": 1,
                "name": name,
                "notes": notes,
                "folderId": folder_id,
                "favorite": favorite,
                "organizationId": organization_id,
                "collectionIds": collection_ids,
                "fields": normalize_custom_fields(fields),
                "login": {
                    "username": username,
                    "password": password,
                    "totp": totp,
                    "uris": login_uris,
                },
            }
        )

    def build_secure_note_payload(
        self,
        *,
        name: str,
        notes: str,
        folder_id: Optional[str] = None,
        favorite: bool = False,
        fields: Optional[List[Dict[str, Any]]] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return _clean_none(
            {
                "type": 2,
                "name": name,
                "notes": notes,
                "folderId": folder_id,
                "favorite": favorite,
                "organizationId": organization_id,
                "collectionIds": collection_ids,
                "fields": normalize_custom_fields(fields),
                "secureNote": {"type": 0},
            }
        )

    def build_card_payload(
        self,
        *,
        name: str,
        cardholder_name: Optional[str] = None,
        brand: Optional[str] = None,
        number: Optional[str] = None,
        exp_month: Optional[str] = None,
        exp_year: Optional[str] = None,
        code: Optional[str] = None,
        notes: Optional[str] = None,
        folder_id: Optional[str] = None,
        favorite: bool = False,
        fields: Optional[List[Dict[str, Any]]] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return _clean_none(
            {
                "type": 3,
                "name": name,
                "notes": notes,
                "folderId": folder_id,
                "favorite": favorite,
                "organizationId": organization_id,
                "collectionIds": collection_ids,
                "fields": normalize_custom_fields(fields),
                "card": {
                    "cardholderName": cardholder_name,
                    "brand": brand,
                    "number": number,
                    "expMonth": exp_month,
                    "expYear": exp_year,
                    "code": code,
                },
            }
        )

    def build_identity_payload(
        self,
        *,
        name: str,
        identity: Dict[str, Any],
        notes: Optional[str] = None,
        folder_id: Optional[str] = None,
        favorite: bool = False,
        fields: Optional[List[Dict[str, Any]]] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return _clean_none(
            {
                "type": 4,
                "name": name,
                "notes": notes,
                "folderId": folder_id,
                "favorite": favorite,
                "organizationId": organization_id,
                "collectionIds": collection_ids,
                "fields": normalize_custom_fields(fields),
                "identity": dict(identity),
            }
        )

    def update_login(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        raw = self.get_raw_item(self.require_exact_item_id(item_id))
        if raw.get("type") != 1:
            raise ValueError("Item is not a login")
        login = dict(raw.get("login") or {})
        for key in ("username", "password", "totp"):
            if key in updates and updates[key] is not None:
                login[key] = updates[key]
        if "uris" in updates and updates["uris"] is not None:
            login["uris"] = updates["uris"]
        if "url" in updates and updates["url"]:
            login["uris"] = [{"uri": updates["url"]}]
        return self._update_common(raw, "login", login, tool="vaultwarden.update_login", purpose=purpose, updates=updates)

    def update_secure_note(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        raw = self.get_raw_item(self.require_exact_item_id(item_id))
        if raw.get("type") != 2:
            raise ValueError("Item is not a secure note")
        raw.setdefault("secureNote", {"type": 0})
        return self._update_common(raw, None, None, tool="vaultwarden.update_secure_note", purpose=purpose, updates=updates)

    def update_card(self, item_id: str, *, purpose: str, **updates: Any) -> Dict[str, Any]:
        raw = self.get_raw_item(self.require_exact_item_id(item_id))
        if raw.get("type") != 3:
            raise ValueError("Item is not a card")
        card = dict(raw.get("card") or {})
        mapping = {
            "cardholder_name": "cardholderName",
            "brand": "brand",
            "number": "number",
            "exp_month": "expMonth",
            "exp_year": "expYear",
            "code": "code",
        }
        for source, target in mapping.items():
            if source in updates and updates[source] is not None:
                card[target] = updates[source]
        return self._update_common(raw, "card", card, tool="vaultwarden.update_card", purpose=purpose, updates=updates)

    def update_identity(self, item_id: str, *, purpose: str, identity_updates: Dict[str, Any], **updates: Any) -> Dict[str, Any]:
        raw = self.get_raw_item(self.require_exact_item_id(item_id))
        if raw.get("type") != 4:
            raise ValueError("Item is not an identity")
        identity = dict(raw.get("identity") or {})
        identity.update({key: value for key, value in identity_updates.items() if value is not None})
        return self._update_common(raw, "identity", identity, tool="vaultwarden.update_identity", purpose=purpose, updates=updates)

    def _update_common(
        self,
        raw: Dict[str, Any],
        section_name: Optional[str],
        section_value: Optional[Dict[str, Any]],
        *,
        tool: str,
        purpose: str,
        updates: Mapping[str, Any],
    ) -> Dict[str, Any]:
        for key in ("name", "notes", "folderId", "folder_id", "favorite"):
            if key in updates and updates[key] is not None:
                target = "folderId" if key == "folder_id" else key
                raw[target] = updates[key]
        if "fields" in updates and updates["fields"] is not None:
            raw["fields"] = normalize_custom_fields(updates["fields"])
        if "collection_ids" in updates and updates["collection_ids"] is not None:
            raw["collectionIds"] = updates["collection_ids"]
        if section_name and section_value is not None:
            raw[section_name] = section_value
        return self.edit_item(str(raw["id"]), raw, tool=tool, purpose=purpose)

    def update_custom_field(
        self,
        item_id: str,
        *,
        name: str,
        value: Optional[str] = None,
        field_type: str = "text",
        purpose: str,
        create_if_missing: bool = True,
    ) -> Dict[str, Any]:
        raw = self.get_raw_item(self.require_exact_item_id(item_id))
        fields = list(raw.get("fields") or [])
        updated = False
        for field in fields:
            if field.get("name") == name:
                replacement = normalize_custom_fields([{"name": name, "value": value, "type": field_type}])[0]
                field.clear()
                field.update(replacement)
                updated = True
                break
        if not updated:
            if not create_if_missing:
                raise KeyError(f"Custom field not found: {name}")
            fields.extend(normalize_custom_fields([{"name": name, "value": value, "type": field_type}]))
        raw["fields"] = fields
        return self.edit_item(str(raw["id"]), raw, tool="vaultwarden.update_custom_field", purpose=purpose)

    def move_item(
        self,
        item_id: str,
        *,
        purpose: str,
        folder_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        if folder_id and organization_id:
            raise ValueError("Pass either folder_id or organization_id, not both")
        if folder_id is not None:
            raw = self.get_raw_item(exact_id)
            raw["folderId"] = None if folder_id == "null" else self.require_exact_folder_id(folder_id)
            return self.edit_item(exact_id, raw, tool="vaultwarden.move_item", purpose=purpose)
        if organization_id:
            args = ["move", exact_id, organization_id]
            if collection_ids is not None:
                args.append(self._encode_json(collection_ids))
            moved = self._run_json(args, session_required=True)
            self.audit(tool="vaultwarden.move_item", operation="move_item", purpose=purpose, item_id=exact_id)
            return sanitize_item(moved)
        raise ValueError("folder_id or organization_id is required")

    def archive_item(self, item_id: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        archived = self._run_json(["archive", "item", exact_id], session_required=True)
        self.audit(tool="vaultwarden.archive_item", operation="archive_item", purpose=purpose, item_id=exact_id)
        return sanitize_item(archived)

    def restore_item(self, item_id: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        restored = self._run_json(["restore", "item", exact_id], session_required=True)
        self.audit(tool="vaultwarden.restore_item", operation="restore_item", purpose=purpose, item_id=exact_id)
        return sanitize_item(restored)

    def delete_item(self, item_id: str, *, purpose: str, permanent: bool = False) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        args = ["delete", "item", exact_id]
        if permanent:
            args.append("--permanent")
        self._run(args, session_required=True)
        tool = "vaultwarden.permanently_delete_item" if permanent else "vaultwarden.delete_item"
        self.audit(tool=tool, operation="delete_item", purpose=purpose, item_id=exact_id, metadata={"permanent": permanent})
        return {"deleted": True, "permanent": permanent, "itemId": exact_id}

    def list_folders(self, *, search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        args = ["list", "folders"]
        if search:
            args.extend(["--search", search])
        folders = self._run_json(args, session_required=True) or []
        capped = max(1, min(int(limit), 100))
        safe = [{"id": folder.get("id"), "name": folder.get("name")} for folder in folders[:capped]]
        self.audit(tool="vaultwarden.list_folders", operation="list_folders", metadata={"count": len(safe)})
        return {"count": len(safe), "totalMatched": len(folders), "truncated": len(folders) > capped, "folders": safe}

    def create_folder(self, name: str, *, purpose: str) -> Dict[str, Any]:
        if not name.strip():
            raise ValueError("Folder name is required")
        folder = self._run_json(["create", "folder", self._encode_json({"name": name})], session_required=True)
        self.audit(tool="vaultwarden.create_folder", operation="create_folder", purpose=purpose, metadata={"folderIdHash": _short_hash(folder.get("id"))})
        return {"id": folder.get("id"), "name": folder.get("name")}

    def update_folder(self, folder_id: str, name: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_folder_id(folder_id)
        if not name.strip():
            raise ValueError("Folder name is required")
        folder = self._run_json(["edit", "folder", exact_id, self._encode_json({"name": name})], session_required=True)
        self.audit(tool="vaultwarden.update_folder", operation="update_folder", purpose=purpose, metadata={"folderIdHash": _short_hash(exact_id)})
        return {"id": folder.get("id"), "name": folder.get("name")}

    def delete_folder(self, folder_id: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_folder_id(folder_id)
        self._run(["delete", "folder", exact_id], session_required=True)
        self.audit(tool="vaultwarden.delete_folder", operation="delete_folder", purpose=purpose, metadata={"folderIdHash": _short_hash(exact_id)})
        return {"deleted": True, "folderId": exact_id}

    def list_collections(self, *, organization_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        args = ["list", "collections"]
        if organization_id:
            args.extend(["--organizationid", organization_id])
        collections = self._run_json(args, session_required=True) or []
        capped = max(1, min(int(limit), 100))
        safe = [
            {
                "id": collection.get("id"),
                "name": collection.get("name"),
                "organizationId": collection.get("organizationId"),
                "externalId": collection.get("externalId"),
            }
            for collection in collections[:capped]
        ]
        self.audit(tool="vaultwarden.list_collections", operation="list_collections", metadata={"count": len(safe)})
        return {"count": len(safe), "totalMatched": len(collections), "truncated": len(collections) > capped, "collections": safe}

    def assign_item_collections(self, item_id: str, collection_ids: List[str], *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        assigned = self._run_json(
            ["edit", "item-collections", exact_id, self._encode_json(list(collection_ids))],
            session_required=True,
        )
        self.audit(
            tool="vaultwarden.assign_item_collections",
            operation="assign_item_collections",
            purpose=purpose,
            item_id=exact_id,
            metadata={"collectionCount": len(collection_ids)},
        )
        return sanitize_item(assigned) if isinstance(assigned, Mapping) else {"itemId": exact_id, "collectionIds": list(collection_ids)}

    def list_attachments(self, item_id: str, *, purpose: str = "list attachments") -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        raw = self.get_raw_item(exact_id)
        attachments = [_summarize_attachment(attachment) for attachment in raw.get("attachments") or []]
        self.audit(tool="vaultwarden.list_attachments", operation="list_attachments", purpose=purpose, item_id=exact_id, metadata={"count": len(attachments)})
        return {"itemId": exact_id, "count": len(attachments), "attachments": attachments}

    def download_attachment(
        self,
        item_id: str,
        attachment_id: str,
        *,
        output_path: Optional[str] = None,
        purpose: str,
    ) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        if not attachment_id.strip():
            raise ValueError("attachment_id is required")
        if output_path:
            output = Path(output_path).expanduser()
        else:
            output = self.attachments_dir / exact_id / attachment_id
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._run(
            ["get", "attachment", attachment_id, "--itemid", exact_id, "--output", str(output)],
            session_required=True,
        )
        self.audit(
            tool="vaultwarden.download_attachment",
            operation="download_attachment",
            purpose=purpose,
            item_id=exact_id,
            metadata={"attachmentIdHash": _short_hash(attachment_id), "outputPath": str(output)},
        )
        return {"downloaded": True, "itemId": exact_id, "attachmentId": attachment_id, "outputPath": str(output)}

    def upload_attachment(self, item_id: str, file_path: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            raise ValueError(f"Attachment file does not exist: {path}")
        uploaded = self._run_json(["create", "attachment", "--file", str(path), "--itemid", exact_id], session_required=True)
        self.audit(
            tool="vaultwarden.upload_attachment",
            operation="upload_attachment",
            purpose=purpose,
            item_id=exact_id,
            metadata={"fileName": path.name},
        )
        return sanitize_item(uploaded) if isinstance(uploaded, Mapping) else {"uploaded": True, "itemId": exact_id}

    def delete_attachment(self, item_id: str, attachment_id: str, *, purpose: str) -> Dict[str, Any]:
        exact_id = self.require_exact_item_id(item_id)
        if not attachment_id.strip():
            raise ValueError("attachment_id is required")
        self._run(["delete", "attachment", attachment_id, "--itemid", exact_id], session_required=True)
        self.audit(
            tool="vaultwarden.delete_attachment",
            operation="delete_attachment",
            purpose=purpose,
            item_id=exact_id,
            metadata={"attachmentIdHash": _short_hash(attachment_id)},
        )
        return {"deleted": True, "itemId": exact_id, "attachmentId": attachment_id}

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
        if not command:
            raise ValueError("command is required")
        self._assert_command_allowed(command)
        secret = self.get_secret(selector, field=field, purpose=purpose)["value"]
        env = os.environ.copy()
        stdin = None
        if mode == "env":
            env[secret_env_name] = "" if secret is None else str(secret)
        elif mode == "stdin":
            stdin = "" if secret is None else str(secret)
        else:
            raise ValueError("mode must be 'env' or 'stdin'")
        process = subprocess.run(
            command,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout_s or self.timeout_s,
            check=False,
            env=env,
        )
        stdout = _redact_text(process.stdout, [str(secret) if secret is not None else None])
        stderr = _redact_text(process.stderr, [str(secret) if secret is not None else None])
        item_id, alias = self.resolve_selector(selector)
        self.audit(
            tool="vaultwarden.use_secret_with_command",
            operation="use_secret_with_command",
            purpose=purpose,
            item_id=item_id,
            alias=alias,
            field=field,
            result="success" if process.returncode == 0 else "error",
            metadata={"command": command[0], "returnCode": process.returncode},
        )
        return {
            "returnCode": process.returncode,
            "stdout": stdout[-8000:],
            "stderr": stderr[-8000:],
            "secretReturned": False,
        }

    def _assert_command_allowed(self, command: Sequence[str]) -> None:
        configured = get_setting("VAULTWARDEN_ALLOWED_COMMANDS") or ""
        allowed = {item.strip() for item in configured.split(",") if item.strip()}
        allow_file = _setting_path("VAULTWARDEN_ALLOWED_COMMANDS_FILE", DEFAULT_CONFIG_DIR / "allowed-commands.json")
        if allow_file.exists():
            try:
                payload = json.loads(allow_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise VaultwardenError(f"Invalid allowed command file: {allow_file}") from exc
            if isinstance(payload, list):
                allowed.update(str(item) for item in payload)
            elif isinstance(payload, Mapping):
                allowed.update(str(item) for item in payload.get("commands", []))
        executable = command[0]
        basename = Path(executable).name
        if executable not in allowed and basename not in allowed:
            raise PermissionError("Command is not in the Vaultwarden allowlist")


_default_client: Optional[VaultwardenClient] = None
_default_client_key: Optional[tuple[str, str, str, str, float]] = None


def get_client() -> VaultwardenClient:
    """Get or create the process-local Vaultwarden client."""

    global _default_client, _default_client_key
    bw_path = get_setting("VAULTWARDEN_BW_PATH") or shutil.which("bw") or "/usr/bin/bw"
    password_file = _setting_path("VAULTWARDEN_PASSWORD_FILE", DEFAULT_PASSWORD_FILE)
    aliases_file = _setting_path("VAULTWARDEN_ALIASES_FILE", DEFAULT_ALIASES_FILE)
    audit_file = _setting_path("VAULTWARDEN_AUDIT_FILE", DEFAULT_AUDIT_FILE)
    timeout_s = _float_setting("VAULTWARDEN_TIMEOUT_S", DEFAULT_TIMEOUT_S)
    key = (bw_path, str(password_file), str(aliases_file), str(audit_file), timeout_s)
    if _default_client is None or _default_client_key != key:
        _default_client = VaultwardenClient(
            bw_path=bw_path,
            password_file=password_file,
            aliases_file=aliases_file,
            audit_file=audit_file,
            timeout_s=timeout_s,
        )
        _default_client_key = key
    return _default_client
