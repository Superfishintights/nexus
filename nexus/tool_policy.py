"""Runtime tool authorization policy for Nexus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Optional

from .env import get_setting


POLICY_MODE_ENV = "NEXUS_TOOL_POLICY_MODE"
POLICY_NAME_ENV = "NEXUS_TOOL_POLICY_NAME"
POLICY_PRESET_ENV = "NEXUS_TOOL_POLICY_PRESET"
ALLOWED_NAMESPACES_ENV = "NEXUS_ALLOWED_TOOL_NAMESPACES"
ALLOWED_TOOLS_ENV = "NEXUS_ALLOWED_TOOLS"
DENIED_TOOLS_ENV = "NEXUS_DENIED_TOOLS"
ALLOWED_CLASSES_ENV = "NEXUS_ALLOWED_TOOL_CLASSES"
DENIED_CLASSES_ENV = "NEXUS_DENIED_TOOL_CLASSES"

MODE_UNRESTRICTED = "unrestricted"
MODE_RESTRICTED = "restricted"

CLASS_READ = "read"
CLASS_WRITE = "write"
CLASS_DESTRUCTIVE = "destructive"
CLASS_ADMIN = "admin"

_ADMIN_TOKENS = {
    "activate",
    "backup",
    "deactivate",
    "import",
    "logout",
    "pull_source_control",
    "refresh",
    "register",
    "restart",
    "restore",
    "shutdown",
    "stop",
    "terminate",
}
_WRITE_PREFIXES = {
    "add",
    "change",
    "create",
    "insert",
    "retry",
    "set",
    "transfer",
    "update",
    "upsert",
}


class ToolAccessError(PermissionError):
    """Raised when a tool is blocked by the active policy."""


def _csv_to_frozenset(value: Optional[str]) -> FrozenSet[str]:
    if not value:
        return frozenset()
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def classify_tool_name(name: str) -> str:
    """Infer a coarse safety class from the canonical tool name."""

    base = name.split(".", 1)[-1]
    if base.startswith("delete_"):
        return CLASS_DESTRUCTIVE
    if any(token in base for token in _ADMIN_TOKENS):
        return CLASS_ADMIN
    if any(base.startswith(prefix + "_") for prefix in _WRITE_PREFIXES):
        return CLASS_WRITE
    return CLASS_READ


@dataclass(frozen=True)
class ToolPolicy:
    """Server-wide policy applied to discovery and tool loading."""

    name: str = MODE_UNRESTRICTED
    mode: str = MODE_UNRESTRICTED
    allowed_namespaces: FrozenSet[str] = frozenset()
    allowed_tools: FrozenSet[str] = frozenset()
    denied_tools: FrozenSet[str] = frozenset()
    allowed_classes: FrozenSet[str] = frozenset()
    denied_classes: FrozenSet[str] = frozenset()

    @property
    def is_restricted(self) -> bool:
        return self.mode == MODE_RESTRICTED

    def check_canonical(
        self,
        canonical_name: str,
        *,
        namespace: str,
        tool_class: str,
    ) -> bool:
        """Return True when a canonical tool is allowed."""

        if not self.is_restricted:
            return True
        if canonical_name in self.denied_tools:
            return False
        if tool_class in self.denied_classes:
            return False
        if canonical_name in self.allowed_tools:
            return True
        if self.allowed_classes and tool_class in self.allowed_classes:
            return True
        if self.allowed_namespaces and namespace in self.allowed_namespaces:
            return True
        return False

    def assert_canonical_allowed(
        self,
        canonical_name: str,
        *,
        namespace: str,
        tool_class: str,
    ) -> None:
        if self.check_canonical(
            canonical_name,
            namespace=namespace,
            tool_class=tool_class,
        ):
            return
        raise ToolAccessError(
            f"Tool '{canonical_name}' is not permitted by the active Nexus tool policy"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "mode": self.mode,
            "allowedNamespaces": sorted(self.allowed_namespaces),
            "allowedTools": sorted(self.allowed_tools),
            "deniedTools": sorted(self.denied_tools),
            "allowedClasses": sorted(self.allowed_classes),
            "deniedClasses": sorted(self.denied_classes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ToolPolicy":
        return cls(
            name=str(payload.get("name", MODE_UNRESTRICTED)),
            mode=str(payload.get("mode", MODE_UNRESTRICTED)),
            allowed_namespaces=frozenset(str(v) for v in payload.get("allowedNamespaces", [])),
            allowed_tools=frozenset(str(v) for v in payload.get("allowedTools", [])),
            denied_tools=frozenset(str(v) for v in payload.get("deniedTools", [])),
            allowed_classes=frozenset(str(v) for v in payload.get("allowedClasses", [])),
            denied_classes=frozenset(str(v) for v in payload.get("deniedClasses", [])),
        )


def policy_from_preset(name: str) -> ToolPolicy:
    normalized = name.strip().lower()
    if normalized in {"", MODE_UNRESTRICTED}:
        return ToolPolicy(name=MODE_UNRESTRICTED, mode=MODE_UNRESTRICTED)
    if normalized == "plex-readonly":
        return ToolPolicy(
            name="plex-readonly",
            mode=MODE_RESTRICTED,
            allowed_namespaces=frozenset({"tautulli", "sonarr", "radarr"}),
            allowed_classes=frozenset({CLASS_READ}),
        )
    if normalized == "plex-safe-write":
        return ToolPolicy(
            name="plex-safe-write",
            mode=MODE_RESTRICTED,
            allowed_namespaces=frozenset({"tautulli", "sonarr", "radarr"}),
            allowed_classes=frozenset({CLASS_READ, CLASS_WRITE}),
            denied_classes=frozenset({CLASS_DESTRUCTIVE, CLASS_ADMIN}),
        )
    if normalized == "work-n8n":
        return ToolPolicy(
            name="work-n8n",
            mode=MODE_RESTRICTED,
            allowed_namespaces=frozenset({"n8n"}),
            allowed_classes=frozenset({CLASS_READ, CLASS_WRITE}),
            denied_classes=frozenset({CLASS_DESTRUCTIVE, CLASS_ADMIN}),
        )
    if normalized == "personal-admin":
        return ToolPolicy(name="personal-admin", mode=MODE_UNRESTRICTED)
    raise ValueError(f"Unknown Nexus tool policy preset: {name}")


def get_active_tool_policy() -> ToolPolicy:
    preset = (get_setting(POLICY_PRESET_ENV) or "").strip()
    if preset:
        return policy_from_preset(preset)

    mode = (get_setting(POLICY_MODE_ENV) or MODE_UNRESTRICTED).strip().lower()
    if mode not in {MODE_UNRESTRICTED, MODE_RESTRICTED}:
        mode = MODE_UNRESTRICTED
    if mode == MODE_UNRESTRICTED:
        return ToolPolicy(
            name=(get_setting(POLICY_NAME_ENV) or MODE_UNRESTRICTED).strip() or MODE_UNRESTRICTED,
            mode=MODE_UNRESTRICTED,
        )

    return ToolPolicy(
        name=(get_setting(POLICY_NAME_ENV) or MODE_RESTRICTED).strip() or MODE_RESTRICTED,
        mode=MODE_RESTRICTED,
        allowed_namespaces=_csv_to_frozenset(get_setting(ALLOWED_NAMESPACES_ENV)),
        allowed_tools=_csv_to_frozenset(get_setting(ALLOWED_TOOLS_ENV)),
        denied_tools=_csv_to_frozenset(get_setting(DENIED_TOOLS_ENV)),
        allowed_classes=_csv_to_frozenset(get_setting(ALLOWED_CLASSES_ENV)),
        denied_classes=_csv_to_frozenset(get_setting(DENIED_CLASSES_ENV)),
    )


def namespace_for_tool(name: str) -> str:
    if "." not in name:
        return ""
    return name.split(".", 1)[0]


def unique_canonical_names(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


__all__ = [
    "ALLOWED_CLASSES_ENV",
    "ALLOWED_NAMESPACES_ENV",
    "ALLOWED_TOOLS_ENV",
    "CLASS_ADMIN",
    "CLASS_DESTRUCTIVE",
    "CLASS_READ",
    "CLASS_WRITE",
    "DENIED_CLASSES_ENV",
    "DENIED_TOOLS_ENV",
    "MODE_RESTRICTED",
    "MODE_UNRESTRICTED",
    "POLICY_MODE_ENV",
    "POLICY_NAME_ENV",
    "POLICY_PRESET_ENV",
    "ToolAccessError",
    "ToolPolicy",
    "classify_tool_name",
    "get_active_tool_policy",
    "namespace_for_tool",
    "policy_from_preset",
    "unique_canonical_names",
]
