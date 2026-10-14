"""Vaultwarden secret command helper tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .structure import _require_purpose


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Use one selected secret from the user's authorized personal Vaultwarden vault with an allowlisted local command without returning the secret.",
    examples=[
        'load_tool("vaultwarden.use_secret_with_command")("alias:github", field="password", command=["gh", "auth", "status"], purpose="check auth")',
    ],
    tool_class="write",
)
def use_secret_with_command(
    selector: str,
    *,
    field: str,
    purpose: str,
    command: List[str],
    mode: str = "env",
    secret_env_name: str = "VAULTWARDEN_SECRET_VALUE",
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    return get_client().use_secret_with_command(
        selector,
        field=field,
        purpose=_require_purpose(purpose),
        command=command,
        mode=mode,
        secret_env_name=secret_env_name,
        timeout_s=timeout_s,
    )
