from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class JiraSettings:
    """Configuration required to interact with a Jira instance."""

    hostname: str
    pat: str

    @classmethod
    def from_env(
        cls, *, hostname_var: str = "JIRA_HOSTNAME", pat_var: str = "JIRA_PAT"
    ) -> "JiraSettings":
        """Create settings by reading environment variables."""

        hostname = require_setting(
            hostname_var,
            message=f"Missing Jira hostname. Set the `{hostname_var}` environment variable.",
        )
        pat = require_setting(
            pat_var,
            message=f"Missing Jira PAT. Set the `{pat_var}` environment variable.",
        )

        return cls(hostname=normalize_url(hostname), pat=pat)

