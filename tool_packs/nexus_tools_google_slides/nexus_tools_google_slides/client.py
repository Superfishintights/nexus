"""Google Slides API client wrapper using the shared Google auth client."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional


class GoogleSlidesClient:
    """Small Slides-specific facade over nexus-tools-google-common."""

    SERVICE = "slides"

    def __init__(self, google_client: Any):
        self.google_client = google_client

    @staticmethod
    def quote(value: str) -> str:
        return urllib.parse.quote(str(value), safe="")

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = self.google_client.request(
            self.SERVICE,
            path,
            method=method,
            params=params,
            payload=payload,
        )
        if isinstance(response, dict):
            return response
        return {"response": response}

    def create_presentation(
        self,
        *,
        title: str,
        presentation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"title": title}
        if presentation_id:
            body["presentationId"] = presentation_id
        return self.request("presentations", method="POST", payload=body)

    def get_presentation(
        self,
        presentation_id: str,
        *,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"fields": fields} if fields else None
        return self.request(f"presentations/{self.quote(presentation_id)}", params=params)

    def batch_update(
        self,
        presentation_id: str,
        requests: List[Dict[str, Any]],
        *,
        required_revision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"requests": requests}
        if required_revision_id:
            body["writeControl"] = {"requiredRevisionId": required_revision_id}
        return self.request(
            f"presentations/{self.quote(presentation_id)}:batchUpdate",
            method="POST",
            payload=body,
        )

    def get_page(self, presentation_id: str, page_object_id: str) -> Dict[str, Any]:
        return self.request(
            "presentations/"
            f"{self.quote(presentation_id)}/pages/{self.quote(page_object_id)}"
        )

    def get_thumbnail(
        self,
        presentation_id: str,
        page_object_id: str,
        *,
        thumbnail_size: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if thumbnail_size:
            params["thumbnailProperties.thumbnailSize"] = thumbnail_size
        if mime_type:
            params["thumbnailProperties.mimeType"] = mime_type
        return self.request(
            "presentations/"
            f"{self.quote(presentation_id)}/pages/{self.quote(page_object_id)}/thumbnail",
            params=params or None,
        )


_default_client: Optional[GoogleSlidesClient] = None


def get_client() -> GoogleSlidesClient:
    """Return the default Slides client backed by nexus-tools-google-common."""

    global _default_client
    if _default_client is None:
        from nexus_tools_google_common.client import get_client as get_google_client

        _default_client = GoogleSlidesClient(get_google_client())
    return _default_client


def set_client_for_tests(client: Optional[GoogleSlidesClient]) -> None:
    """Install a package-local client override for tests."""

    global _default_client
    _default_client = client
