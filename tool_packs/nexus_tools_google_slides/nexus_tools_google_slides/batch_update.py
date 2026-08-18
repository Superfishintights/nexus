"""Low-level Google Slides batchUpdate tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .helpers import normalize_requests


class BatchUpdateTools:
    """Batch update executor and request validation helpers."""

    def __init__(self, client: Any):
        self.client = client

    def validate(self, requests: Any) -> Dict[str, Any]:
        normalized = normalize_requests(requests)
        return {
            "valid": True,
            "requestCount": len(normalized),
            "requestTypes": [next(iter(request.keys())) for request in normalized],
        }

    def execute(
        self,
        presentation_id: str,
        requests: Any,
        required_revision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized = normalize_requests(requests)
        return self.client.batch_update(
            presentation_id,
            normalized,
            required_revision_id=required_revision_id,
        )

    def bundle(
        self,
        presentation_id: str,
        bundle: Any,
        required_revision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if isinstance(bundle, dict) and "requests" in bundle:
            requests = bundle["requests"]
        else:
            requests = bundle
        return self.execute(presentation_id, requests, required_revision_id)


def _tools() -> BatchUpdateTools:
    return BatchUpdateTools(get_client())


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Run a raw presentations.batchUpdate request list.",
    examples=['load_tool("google_slides.batch_update")("presentation-id", [{"createSlide": {}}])'],
    tool_class="write",
)
def batch_update(
    presentation_id: str,
    requests: List[Dict[str, Any]],
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().execute(presentation_id, requests, required_revision_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Validate local shape of a Slides batchUpdate request list.",
    examples=['load_tool("google_slides.validate_requests")([{"createSlide": {}}])'],
    tool_class="read",
)
def validate_requests(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    return _tools().validate(requests)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Apply a request bundle or request list to a presentation.",
    examples=['load_tool("google_slides.apply_request_bundle")("presentation-id", {"requests": [{"createSlide": {}}]})'],
    tool_class="write",
)
def apply_request_bundle(
    presentation_id: str,
    bundle: Dict[str, Any],
    required_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().bundle(presentation_id, bundle, required_revision_id)
