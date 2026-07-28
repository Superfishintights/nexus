"""Presentation-level Google Slides tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .helpers import object_ids, text_runs


class PresentationTools:
    """Presentation read/create helpers."""

    def __init__(self, client: Any):
        self.client = client

    def create(self, title: str, presentation_id: Optional[str] = None) -> Dict[str, Any]:
        return self.client.create_presentation(title=title, presentation_id=presentation_id)

    def get(self, presentation_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        return self.client.get_presentation(presentation_id, fields=fields)

    def summary(self, presentation_id: str) -> Dict[str, Any]:
        presentation = self.get(presentation_id)
        slides = presentation.get("slides", [])
        return {
            "presentationId": presentation.get("presentationId"),
            "title": presentation.get("title"),
            "revisionId": presentation.get("revisionId"),
            "slides": [
                {
                    "objectId": slide.get("objectId"),
                    "pageType": slide.get("pageType"),
                    "elementCount": len(slide.get("pageElements", [])),
                }
                for slide in slides
            ],
            "slideCount": len(slides),
            "objectIds": object_ids(presentation),
        }

    def list_slides(self, presentation_id: str) -> Dict[str, Any]:
        presentation = self.get(
            presentation_id,
            fields="presentationId,title,revisionId,slides(objectId,pageType,pageElements(objectId))",
        )
        return {
            "presentationId": presentation.get("presentationId"),
            "title": presentation.get("title"),
            "revisionId": presentation.get("revisionId"),
            "slides": [
                {
                    "objectId": slide.get("objectId"),
                    "pageType": slide.get("pageType"),
                    "pageElementObjectIds": [
                        element.get("objectId")
                        for element in slide.get("pageElements", [])
                        if element.get("objectId")
                    ],
                }
                for slide in presentation.get("slides", [])
            ],
        }

    def revision_id(self, presentation_id: str) -> Dict[str, Any]:
        presentation = self.get(presentation_id, fields="presentationId,revisionId")
        return {
            "presentationId": presentation.get("presentationId"),
            "revisionId": presentation.get("revisionId"),
        }

    def slide_text(self, presentation_id: str) -> Dict[str, Any]:
        presentation = self.get(
            presentation_id,
            fields="presentationId,slides(objectId,pageElements(objectId,shape(text(textElements(textRun)))))",
        )
        return {
            "presentationId": presentation.get("presentationId"),
            "textRuns": text_runs(presentation),
        }


def _tools() -> PresentationTools:
    return PresentationTools(get_client())


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Create a blank Google Slides presentation.",
    examples=['load_tool("google_slides.create_presentation")("Quarterly review")'],
    tool_class="write",
)
def create_presentation(title: str, presentation_id: Optional[str] = None) -> Dict[str, Any]:
    return _tools().create(title, presentation_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Get a Google Slides presentation by ID.",
    examples=['load_tool("google_slides.get_presentation")("presentation-id")'],
    tool_class="read",
)
def get_presentation(presentation_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
    return _tools().get(presentation_id, fields)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Summarize slides, revision, and object IDs in a presentation.",
    examples=['load_tool("google_slides.get_presentation_summary")("presentation-id")'],
    tool_class="read",
)
def get_presentation_summary(presentation_id: str) -> Dict[str, Any]:
    return _tools().summary(presentation_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="List slides and page element IDs in a presentation.",
    examples=['load_tool("google_slides.list_slides")("presentation-id")'],
    tool_class="read",
)
def list_slides(presentation_id: str) -> Dict[str, Any]:
    return _tools().list_slides(presentation_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Get the current presentation revision ID for write control.",
    examples=['load_tool("google_slides.get_revision_id")("presentation-id")'],
    tool_class="read",
)
def get_revision_id(presentation_id: str) -> Dict[str, Any]:
    return _tools().revision_id(presentation_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Extract text runs from all slides in a presentation.",
    examples=['load_tool("google_slides.get_slide_text")("presentation-id")'],
    tool_class="read",
)
def get_slide_text(presentation_id: str) -> Dict[str, Any]:
    return _tools().slide_text(presentation_id)
