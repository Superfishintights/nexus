from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RunnerSettings:
    """Core runner settings exposed inside `run_code` snippets."""

    tool_packages: Tuple[str, ...] = ()
    tool_policy_name: str = "unrestricted"
    tool_policy_mode: str = "unrestricted"

    @classmethod
    def from_env(cls) -> "RunnerSettings":
        from ..tool_catalog import get_tool_package_names
        from ..tool_policy import get_active_tool_policy

        policy = get_active_tool_policy()
        return cls(
            tool_packages=tuple(get_tool_package_names()),
            tool_policy_name=policy.name,
            tool_policy_mode=policy.mode,
        )
