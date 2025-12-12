"""Configuration helpers for the nexus runner."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing."""


_ENV_FILE_CACHE: dict[Path, tuple[float, dict[str, str]]] = {}


def _parse_env_value(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    values: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _parse_env_value(value)
    return values


def _get_env_file_values(path: Path) -> dict[str, str]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        _ENV_FILE_CACHE.pop(path, None)
        return {}

    cached = _ENV_FILE_CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    parsed = _read_env_file(path)
    _ENV_FILE_CACHE[path] = (mtime, parsed)
    return parsed


def _default_env_file_paths() -> list[Path]:
    """Return env file candidates, lowest precedence first."""

    explicit = os.getenv("NEXUS_ENV_FILE")
    if explicit:
        return [Path(explicit).expanduser()]

    home = Path.home()
    paths: list[Path] = []

    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    paths.append(xdg_config_home / "nexus" / ".env")
    paths.append(home / ".nexus" / ".env")
    paths.append(home / "Library" / "Application Support" / "nexus" / ".env")

    appdata = os.getenv("APPDATA")
    if appdata:
        paths.append(Path(appdata) / "nexus" / ".env")

    paths.append(Path.cwd() / ".env")

    return paths


def get_setting(name: str, *fallback_names: str) -> Optional[str]:
    """Return a setting from the process environment or a `.env` file.

    Resolution order (highest precedence first):
    1) Process environment variables
    2) `.env` in current working directory
    3) User-level `.env` in standard config locations

    Set `NEXUS_ENV_FILE` to force a specific `.env` file path.
    """

    candidates = (name,) + fallback_names

    for candidate in candidates:
        value = os.getenv(candidate) or os.getenv(candidate.lower())
        if value:
            return value

    merged: dict[str, str] = {}
    for path in _default_env_file_paths():
        merged.update(_get_env_file_values(path))

    for candidate in candidates:
        value = merged.get(candidate) or merged.get(candidate.lower())
        if value:
            return value

    return None


@dataclass(frozen=True)
class JiraSettings:
    """Configuration required to interact with a Jira instance."""

    hostname: str
    pat: str

    @classmethod
    def from_env(cls, *, hostname_var: str = "JIRA_HOSTNAME", pat_var: str = "JIRA_PAT") -> "JiraSettings":
        """Create settings by reading environment variables.

        Parameters
        ----------
        hostname_var:
            Environment variable holding the Jira hostname/URL.
        pat_var:
            Environment variable holding the Jira Personal Access Token.
        """

        hostname = get_setting(hostname_var)
        pat = get_setting(pat_var)
        if not hostname:
            raise ConfigurationError(
                f"Missing Jira hostname. Set the `{hostname_var}` environment variable."
            )
        if not pat:
            raise ConfigurationError(
                f"Missing Jira PAT. Set the `{pat_var}` environment variable."
            )

        if not hostname.startswith(('http://', 'https://')):
            hostname = f"https://{hostname}"

        return cls(hostname=hostname.rstrip("/"), pat=pat)


@dataclass(frozen=True)
class SourcegraphSettings:
    """Configuration required to interact with a Sourcegraph instance."""

    host: str
    pat: str
    sgs_cookie: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SourcegraphSettings":
        """Create settings by reading environment variables.

        Reads from SOURCEGRAPH_HOST (default: sourcegraph.ab1.op.lb.local),
        SOURCEGRAPH_PAT/SOURCEGRAPH_TOKEN/X_PAT,
        and optionally SOURCEGRAPH_SGS_COOKIE for Deepsearch.
        """
        host = get_setting("SOURCEGRAPH_HOST") or "sourcegraph.ab1.op.lb.local"
        pat = (
            get_setting("SOURCEGRAPH_PAT", "SOURCEGRAPH_TOKEN", "X_PAT")
        )
        sgs_cookie = get_setting("SOURCEGRAPH_SGS_COOKIE")

        if not pat:
            raise ConfigurationError(
                "Missing Sourcegraph PAT. Set SOURCEGRAPH_PAT, SOURCEGRAPH_TOKEN, or X_PAT environment variable."
            )

        if not host.startswith(('http://', 'https://')):
            host = f"https://{host}"

        return cls(host=host.rstrip("/"), pat=pat, sgs_cookie=sgs_cookie)


@dataclass(frozen=True)
class ConfluenceSettings:
    """Configuration required to interact with a Confluence instance."""

    url: str
    pat: str

    @classmethod
    def from_env(cls) -> "ConfluenceSettings":
        """Create settings by reading environment variables.

        Reads from CONFLUENCE_URL and CONFLUENCE_PAT.
        """
        url = get_setting("CONFLUENCE_URL")
        pat = get_setting("CONFLUENCE_PAT")

        if not url:
            raise ConfigurationError(
                "Missing Confluence URL. Set the CONFLUENCE_URL environment variable."
            )
        if not pat:
            raise ConfigurationError(
                "Missing Confluence PAT. Set the CONFLUENCE_PAT environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), pat=pat)


@dataclass(frozen=True)
class GitLabSettings:
    """Configuration required to interact with a GitLab instance."""

    url: str
    token: str

    @classmethod
    def from_env(cls) -> "GitLabSettings":
        """Create settings by reading environment variables.

        Reads from GITLAB_URL and GITLAB_TOKEN.
        """
        url = get_setting("GITLAB_URL")
        token = get_setting("GITLAB_TOKEN")

        if not url:
            raise ConfigurationError(
                "Missing GitLab URL. Set the GITLAB_URL environment variable."
            )
        if not token:
            raise ConfigurationError(
                "Missing GitLab token. Set the GITLAB_TOKEN environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), token=token)


@dataclass(frozen=True)
class JenkinsSettings:
    """Configuration required to interact with a Jenkins instance."""

    url: str
    username: str
    token: str

    @classmethod
    def from_env(cls) -> "JenkinsSettings":
        """Create settings by reading environment variables.

        Reads from JENKINS_URL, JENKINS_USERNAME, and JENKINS_TOKEN.
        """
        url = get_setting("JENKINS_URL")
        username = get_setting("JENKINS_USERNAME")
        token = get_setting("JENKINS_TOKEN")

        if not url:
            raise ConfigurationError(
                "Missing Jenkins URL. Set the JENKINS_URL environment variable."
            )
        if not username:
            raise ConfigurationError(
                "Missing Jenkins username. Set the JENKINS_USERNAME environment variable."
            )
        if not token:
            raise ConfigurationError(
                "Missing Jenkins token. Set the JENKINS_TOKEN environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), username=username, token=token)


@dataclass(frozen=True)
class TalosSettings:
    """Configuration required to interact with a Talos instance."""

    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "TalosSettings":
        """Create settings by reading environment variables.

        Reads from TALOS_URL and TALOS_API_KEY.
        """
        base_url = get_setting("TALOS_URL")
        api_key = get_setting("TALOS_API_KEY")

        if not base_url:
            raise ConfigurationError(
                "Missing Talos URL. Set the TALOS_URL environment variable."
            )
        if not api_key:
            raise ConfigurationError(
                "Missing Talos API key. Set the TALOS_API_KEY environment variable."
            )

        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"

        return cls(base_url=base_url.rstrip("/"), api_key=api_key)


@dataclass(frozen=True)
class TautulliSettings:
    """Configuration required to interact with a Tautulli instance."""

    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "TautulliSettings":
        """Create settings by reading environment variables.

        Reads from TAUTULLI_URL and TAUTULLI_API_KEY.
        """
        base_url = get_setting("TAUTULLI_URL")
        api_key = get_setting("TAUTULLI_API_KEY")

        if not base_url:
            raise ConfigurationError(
                "Missing Tautulli URL. Set the TAUTULLI_URL environment variable."
            )
        if not api_key:
            raise ConfigurationError(
                "Missing Tautulli API key. Set the TAUTULLI_API_KEY environment variable."
            )

        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        return cls(base_url=base_url.rstrip("/"), api_key=api_key)


@dataclass(frozen=True)
class RunnerSettings:
    """Top-level settings for the runner environment."""

    jira: Optional[JiraSettings] = None
    sourcegraph: Optional[SourcegraphSettings] = None
    confluence: Optional[ConfluenceSettings] = None
    gitlab: Optional[GitLabSettings] = None
    jenkins: Optional[JenkinsSettings] = None
    talos: Optional[TalosSettings] = None
    tautulli: Optional[TautulliSettings] = None

    @classmethod
    def from_env(cls) -> "RunnerSettings":
        try:
            jira = JiraSettings.from_env()
        except ConfigurationError:
            jira = None

        try:
            sourcegraph = SourcegraphSettings.from_env()
        except ConfigurationError:
            sourcegraph = None

        try:
            confluence = ConfluenceSettings.from_env()
        except ConfigurationError:
            confluence = None

        try:
            gitlab = GitLabSettings.from_env()
        except ConfigurationError:
            gitlab = None

        try:
            jenkins = JenkinsSettings.from_env()
        except ConfigurationError:
            jenkins = None

        try:
            talos = TalosSettings.from_env()
        except ConfigurationError:
            talos = None

        try:
            tautulli = TautulliSettings.from_env()
        except ConfigurationError:
            tautulli = None

        return cls(
            jira=jira,
            sourcegraph=sourcegraph,
            confluence=confluence,
            gitlab=gitlab,
            jenkins=jenkins,
            talos=talos,
            tautulli=tautulli,
        )
