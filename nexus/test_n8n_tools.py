from __future__ import annotations

import pytest

from tools.n8n.add_node import add_node


class FakeClient:
    def __init__(self, workflow):
        self.workflow = workflow
        self.calls = []

    def _make_request(self, endpoint, method="GET", data=None):
        self.calls.append({"endpoint": endpoint, "method": method, "data": data})
        if method == "GET":
            return self.workflow
        return {"ok": True, "payload": data}


def test_add_node_raises_when_connect_source_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient({"nodes": [], "connections": {}})
    monkeypatch.setattr("tools.n8n.add_node.get_client", lambda: fake)

    with pytest.raises(ValueError, match="does not contain a source node"):
        add_node(
            workflow_id="1",
            node_type="n8n-nodes-base.httpRequest",
            node_name="Fetch",
            connect_to="Missing",
        )


def test_add_node_rejects_duplicate_names(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient({"nodes": [{"name": "Fetch", "position": [0, 0]}], "connections": {}})
    monkeypatch.setattr("tools.n8n.add_node.get_client", lambda: fake)

    with pytest.raises(ValueError, match="already contains a node named"):
        add_node(
            workflow_id="1",
            node_type="n8n-nodes-base.httpRequest",
            node_name="Fetch",
        )


def test_add_node_updates_workflow_when_connection_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeClient(
        {
            "nodes": [{"name": "Start", "position": [100, 200]}],
            "connections": {},
        }
    )
    monkeypatch.setattr("tools.n8n.add_node.get_client", lambda: fake)

    result = add_node(
        workflow_id="1",
        node_type="n8n-nodes-base.httpRequest",
        node_name="Fetch",
        connect_to="Start",
    )

    assert result["ok"] is True
    assert fake.calls[1]["method"] == "PUT"
    payload = fake.calls[1]["data"]
    assert payload["nodes"][-1]["name"] == "Fetch"
    assert payload["nodes"][-1]["position"] == [300, 200]
    assert payload["connections"]["Start"]["main"][0][0]["node"] == "Fetch"
