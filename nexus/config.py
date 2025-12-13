"""Public configuration surface for Nexus (backwards compatible).

This project started with a single `nexus/config.py` module that contained both:
- `.env` parsing helpers (`get_setting`)
- per-service, typed settings classes (Jira/GitLab/etc.)

As the number of services grows, keeping everything in one file becomes hard to
maintain. The implementation now lives in:
- `nexus/env.py` for env + `.env` handling
- `nexus/settings/*` for per-service settings

This module re-exports the original API so existing imports keep working.
"""

from __future__ import annotations

from .env import ConfigurationError, get_setting
from .settings.confluence import ConfluenceSettings
from .settings.gitlab import GitLabSettings
from .settings.jenkins import JenkinsSettings
from .settings.jira import JiraSettings
from .settings.runner import RunnerSettings
from .settings.sonarr import SonarrSettings
from .settings.sourcegraph import SourcegraphSettings
from .settings.talos import TalosSettings
from .settings.tautulli import TautulliSettings

__all__ = [
    "ConfigurationError",
    "ConfluenceSettings",
    "GitLabSettings",
    "JenkinsSettings",
    "JiraSettings",
    "RunnerSettings",
    "SonarrSettings",
    "SourcegraphSettings",
    "TalosSettings",
    "TautulliSettings",
    "get_setting",
]

