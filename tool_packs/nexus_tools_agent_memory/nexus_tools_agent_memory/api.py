"""Nexus tools for the agent-memory service."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="agent_memory",
    aliases=["health", "check_health"],
    description="Check whether the agent-memory API health endpoint is responding.",
    examples=['load_tool("agent_memory.get_health")()'],
)
def get_health() -> Dict[str, Any]:
    client = get_client()
    return client.request("GET", "/healthz", require_auth=False)


@register_tool(
    namespace="agent_memory",
    aliases=["ready", "check_ready"],
    description="Check whether the agent-memory API is ready and its database is available.",
    examples=['load_tool("agent_memory.get_ready")()'],
)
def get_ready() -> Dict[str, Any]:
    client = get_client()
    return client.request("GET", "/readyz", require_auth=False)


@register_tool(
    namespace="agent_memory",
    aliases=["add_memory", "store_memory", "save_memory", "memorize"],
    description="Store a memory item in the agent-memory service.",
    examples=[
        'load_tool("agent_memory.remember")("Remember that the deploy host is hermes-agent")',
    ],
)
def remember(
    content: str,
    *,
    profile: Optional[str] = None,
    scope: Optional[str] = None,
    memory_type: str = "fact",
    source_kind: str = "manual",
    source_title: str = "Nexus",
    importance: Optional[int] = None,
    labels: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
        "type": memory_type,
        "content": content,
        "source": {
            "kind": source_kind,
            "title": source_title,
        },
    }
    if scope:
        body["scope"] = scope
    if importance is not None:
        body["importance"] = importance
    if labels:
        body["labels"] = labels
    if metadata:
        body["metadata"] = metadata
    return client.request("POST", "/v1/memory/remember", body=body, agent_id=agent_id)


@register_tool(
    namespace="agent_memory",
    aliases=["get_memories", "search_memories", "retrieve_memory", "retrieve_memories"],
    description="Recall memories from the agent-memory service in evidence or summary mode.",
    examples=[
        'load_tool("agent_memory.recall")("hermes-agent", mode="evidence")',
    ],
)
def recall(
    query: str,
    *,
    profile: Optional[str] = None,
    scope_filters: Optional[List[str]] = None,
    mode: str = "evidence",
    limit: Optional[int] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
        "query": query,
        "mode": mode,
    }
    if scope_filters:
        body["scopeFilters"] = scope_filters
    if limit is not None:
        body["limit"] = limit
    return client.request("POST", "/v1/memory/recall", body=body, agent_id=agent_id)


@register_tool(
    namespace="agent_memory",
    aliases=["list_memory", "browse_memories"],
    description="List stored memories for a profile, optionally filtered by scope.",
    examples=[
        'load_tool("agent_memory.list_memories")(scope="remote:test-agent", limit=10)',
    ],
)
def list_memories(
    *,
    profile: Optional[str] = None,
    scope: Optional[str] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
    }
    if scope:
        body["scope"] = scope
    if limit is not None:
        body["limit"] = limit
    if cursor is not None:
        body["cursor"] = cursor
    return client.request("POST", "/v1/memory/list", body=body, agent_id=agent_id)


@register_tool(
    namespace="agent_memory",
    aliases=["delete_memory", "remove_memory"],
    description="Forget a specific memory item by memory ID.",
    examples=[
        'load_tool("agent_memory.forget")("mem_123", reason="no longer relevant")',
    ],
)
def forget(
    memory_id: str,
    *,
    profile: Optional[str] = None,
    reason: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
        "memoryId": memory_id,
    }
    if reason:
        body["reason"] = reason
    return client.request("POST", "/v1/memory/forget", body=body, agent_id=agent_id)


@register_tool(
    namespace="agent_memory",
    aliases=["update_memory", "replace_memory"],
    description="Correct an existing memory by superseding it with a replacement value.",
    examples=[
        'load_tool("agent_memory.correct")("mem_123", "Updated deploy host is hermes-agent")',
    ],
)
def correct(
    memory_id: str,
    replacement_content: str,
    *,
    profile: Optional[str] = None,
    replacement_type: str = "fact",
    replacement_scope: Optional[str] = None,
    replacement_source_kind: str = "manual",
    replacement_source_title: str = "Nexus",
    replacement_importance: Optional[int] = None,
    replacement_labels: Optional[List[str]] = None,
    replacement_metadata: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    replacement: Dict[str, Any] = {
        "type": replacement_type,
        "content": replacement_content,
        "source": {
            "kind": replacement_source_kind,
            "title": replacement_source_title,
        },
    }
    if replacement_scope:
        replacement["scope"] = replacement_scope
    if replacement_importance is not None:
        replacement["importance"] = replacement_importance
    if replacement_labels:
        replacement["labels"] = replacement_labels
    if replacement_metadata:
        replacement["metadata"] = replacement_metadata

    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
        "memoryId": memory_id,
        "replacement": replacement,
    }
    if reason:
        body["reason"] = reason
    return client.request("POST", "/v1/memory/correct", body=body, agent_id=agent_id)


@register_tool(
    namespace="agent_memory",
    aliases=["ingest_memory", "ingest_notes", "store_document"],
    description="Ingest a larger block of content into the agent-memory service for worker-backed processing.",
    examples=[
        'load_tool("agent_memory.ingest")("deployment notes", content_type="text/plain")',
    ],
)
def ingest(
    content: str,
    *,
    content_type: str = "text/plain",
    profile: Optional[str] = None,
    scope: Optional[str] = None,
    source_kind: str = "manual",
    source_title: str = "Nexus",
    labels: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    body: Dict[str, Any] = {
        "profile": client.resolve_profile(profile),
        "content": content,
        "contentType": content_type,
        "source": {
            "kind": source_kind,
            "title": source_title,
        },
    }
    if scope:
        body["scope"] = scope
    if labels:
        body["labels"] = labels
    if metadata:
        body["metadata"] = metadata
    return client.request("POST", "/v1/memory/ingest", body=body, agent_id=agent_id)
