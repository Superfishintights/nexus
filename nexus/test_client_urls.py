from nexus.test_helpers import add_tool_pack_paths

add_tool_pack_paths(
    (
        "nexus_tools_jira",
        "nexus_tools_n8n",
        "nexus_tools_radarr",
    )
)

from nexus_tools_jira.client import JiraClient
from nexus_tools_n8n.client import N8NClient
from nexus_tools_radarr.client import RadarrClient


def test_n8n_build_url_encodes_query_params() -> None:
    client = N8NClient(host="https://n8n.example", api_key="test")

    url = client._build_url(
        "/executions",
        query_params={
            "filter": "a b",
            "status": ["success", "error"],
            "limit": 10,
            "path": "foo/bar",
            "unused": None,
        },
    )

    assert (
        url
        == "https://n8n.example/api/v1/executions"
        "?filter=a+b&status=success&status=error&limit=10&path=foo%2Fbar"
    )


def test_n8n_build_url_omits_query_string_when_all_values_none() -> None:
    client = N8NClient(host="https://n8n.example", api_key="test")

    url = client._build_url("workflows", query_params={"a": None})

    assert url == "https://n8n.example/api/v1/workflows"


def test_jira_build_url_normalizes_leading_slash() -> None:
    client = JiraClient(hostname="https://jira.example", pat="test")

    assert (
        client._build_url("/issue/PROJ-1")
        == "https://jira.example/rest/api/2/issue/PROJ-1"
    )


def test_radarr_build_url_uses_v3_by_default() -> None:
    client = RadarrClient(base_url="https://radarr.example", api_key="test")

    assert client._build_url("/movie", None) == "https://radarr.example/api/v3/movie"


def test_radarr_legacy_token_fallback(monkeypatch) -> None:
    monkeypatch.setenv("RADARR_URL", "https://radarr.example")
    monkeypatch.delenv("RADARR_API_KEY", raising=False)
    monkeypatch.setenv("RADARR_TOKEN", "legacy-token")

    client = RadarrClient()

    assert client.api_key == "legacy-token"
