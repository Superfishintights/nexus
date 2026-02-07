from tools.jira.client import JiraClient
from tools.n8n.client import N8NClient


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

