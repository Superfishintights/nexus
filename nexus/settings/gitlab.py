from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class GitLabSettings:
    """Configuration required to interact with a GitLab instance."""

    url: str
    token: str

    @classmethod
    def from_env(cls) -> "GitLabSettings":
        """Create settings by reading environment variables."""

        url = require_setting(
            "GITLAB_URL",
            message="Missing GitLab URL. Set the GITLAB_URL environment variable.",
        )
        token = require_setting(
            "GITLAB_TOKEN",
            message="Missing GitLab token. Set the GITLAB_TOKEN environment variable.",
        )

        return cls(url=normalize_url(url), token=token)

