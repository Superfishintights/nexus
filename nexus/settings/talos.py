from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class TalosSettings:
    """Configuration required to interact with a Talos instance."""

    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "TalosSettings":
        """Create settings by reading environment variables."""

        base_url = require_setting(
            "TALOS_URL",
            message="Missing Talos URL. Set the TALOS_URL environment variable.",
        )
        api_key = require_setting(
            "TALOS_API_KEY",
            message="Missing Talos API key. Set the TALOS_API_KEY environment variable.",
        )

        return cls(base_url=normalize_url(base_url), api_key=api_key)

