"""Page-level Google Slides tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client
from .helpers import text_runs


class PageTools:
    """Slide page retrieval and thumbnail helpers."""

    def __init__(self, client: Any):
        self.client = client

    def get_page(self, presentation_id: str, page_object_id: str) -> Dict[str, Any]:
        return self.client.get_page(presentation_id, page_object_id)

    def get_thumbnail(
        self,
        presentation_id: str,
        page_object_id: str,
        thumbnail_size: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client.get_thumbnail(
            presentation_id,
            page_object_id,
            thumbnail_size=thumbnail_size,
            mime_type=mime_type,
        )

    def get_thumbnails(
        self,
        presentation_id: str,
        page_object_ids: Optional[List[str]] = None,
        thumbnail_size: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if page_object_ids is None:
            presentation = self.client.get_presentation(
                presentation_id,
                fields="presentationId,slides(objectId)",
            )
            page_object_ids = [
                slide["objectId"]
                for slide in presentation.get("slides", [])
                if slide.get("objectId")
            ]
        return {
            "presentationId": presentation_id,
            "thumbnails": [
                {
                    "pageObjectId": page_object_id,
                    "thumbnail": self.get_thumbnail(
                        presentation_id,
                        page_object_id,
                        thumbnail_size,
                        mime_type,
                    ),
                }
                for page_object_id in page_object_ids
            ],
        }

    def find_page_elements(
        self,
        presentation_id: str,
        page_object_id: str,
        text_contains: Optional[str] = None,
    ) -> Dict[str, Any]:
        page = self.get_page(presentation_id, page_object_id)
        matches: List[Dict[str, Any]] = []
        for element in page.get("pageElements", []):
            element_text = " ".join(
                run.get("content") or "" for run in text_runs({"pageElements": [element]})
            )
            if text_contains and text_contains.lower() not in element_text.lower():
                continue
            matches.append(
                {
                    "objectId": element.get("objectId"),
                    "size": element.get("size"),
                    "transform": element.get("transform"),
                    "hasText": bool(element_text),
                    "text": element_text,
                    "keys": sorted(element.keys()),
                }
            )
        return {
            "presentationId": presentation_id,
            "pageObjectId": page_object_id,
            "matches": matches,
        }


def _tools() -> PageTools:
    return PageTools(get_client())


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Get a slide page by presentation ID and page object ID.",
    examples=['load_tool("google_slides.get_page")("presentation-id", "slide-id")'],
    tool_class="read",
)
def get_page(presentation_id: str, page_object_id: str) -> Dict[str, Any]:
    return _tools().get_page(presentation_id, page_object_id)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Get a temporary thumbnail URL for a slide page.",
    examples=['load_tool("google_slides.get_page_thumbnail")("presentation-id", "slide-id")'],
    tool_class="read",
)
def get_page_thumbnail(
    presentation_id: str,
    page_object_id: str,
    thumbnail_size: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().get_thumbnail(presentation_id, page_object_id, thumbnail_size, mime_type)


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Get temporary thumbnail URLs for selected or all slides.",
    examples=['load_tool("google_slides.get_slide_thumbnails")("presentation-id")'],
    tool_class="read",
)
def get_slide_thumbnails(
    presentation_id: str,
    page_object_ids: Optional[List[str]] = None,
    thumbnail_size: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().get_thumbnails(
        presentation_id,
        page_object_ids,
        thumbnail_size,
        mime_type,
    )


@register_tool(
    namespace="google_slides",
    aliases=[],
    description="Find page elements on a slide, optionally filtered by contained text.",
    examples=['load_tool("google_slides.find_page_elements")("presentation-id", "slide-id")'],
    tool_class="read",
)
def find_page_elements(
    presentation_id: str,
    page_object_id: str,
    text_contains: Optional[str] = None,
) -> Dict[str, Any]:
    return _tools().find_page_elements(presentation_id, page_object_id, text_contains)
