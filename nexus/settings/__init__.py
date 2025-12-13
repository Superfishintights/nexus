"""Typed, per-service settings used by the runner.

These settings are optional. When exposed to the execution environment they are
available as `RUNNER_SETTINGS`.
"""

from .confluence import ConfluenceSettings
from .gitlab import GitLabSettings
from .jenkins import JenkinsSettings
from .jira import JiraSettings
from .runner import RunnerSettings
from .sonarr import SonarrSettings
from .sourcegraph import SourcegraphSettings
from .talos import TalosSettings
from .tautulli import TautulliSettings

__all__ = [
    "ConfluenceSettings",
    "GitLabSettings",
    "JenkinsSettings",
    "JiraSettings",
    "RunnerSettings",
    "SonarrSettings",
    "SourcegraphSettings",
    "TalosSettings",
    "TautulliSettings",
]

