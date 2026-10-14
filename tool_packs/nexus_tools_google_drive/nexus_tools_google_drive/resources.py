"""Explicit Drive v3 resource classes used by registered tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import DriveClient, coerce_body, compact_dict, quote_segment


class FilesResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "files", params=compact_dict(params))

    def get(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}", params=compact_dict(params))

    def create(self, *, metadata: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("POST", "files", params=compact_dict(params), body=metadata)

    def update(self, file_id: str, *, metadata: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("PATCH", f"files/{quote_segment(file_id)}", params=compact_dict(params), body=metadata)

    def copy(self, file_id: str, *, metadata: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("POST", f"files/{quote_segment(file_id)}/copy", params=compact_dict(params), body=metadata)

    def delete(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("DELETE", f"files/{quote_segment(file_id)}", params=compact_dict(params))

    def empty_trash(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("DELETE", "files/trash", params=compact_dict(params))

    def generate_ids(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "files/generateIds", params=compact_dict(params))

    def export(self, file_id: str, mime_type: str) -> Any:
        return self.client.request(
            "GET",
            f"files/{quote_segment(file_id)}/export",
            params={"mimeType": mime_type},
            binary=True,
        )

    def download(self, file_id: str, **params: Any) -> Any:
        return self.client.request(
            "GET",
            f"files/{quote_segment(file_id)}",
            params=compact_dict({**params, "alt": "media"}),
            binary=True,
        )

    def upload(
        self,
        *,
        metadata: Dict[str, Any],
        content: bytes,
        mime_type: str,
        file_id: Optional[str] = None,
        **params: Any,
    ) -> Dict[str, Any]:
        return self.client.upload_multipart(
            metadata=metadata,
            content=content,
            mime_type=mime_type,
            file_id=file_id,
            params=compact_dict(params),
        )

    def list_labels(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/listLabels", params=compact_dict(params))

    def modify_labels(self, file_id: str, *, body: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", f"files/{quote_segment(file_id)}/modifyLabels", body=body)


class PermissionsResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/permissions", params=compact_dict(params))

    def get(self, file_id: str, permission_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/permissions/{quote_segment(permission_id)}", params=compact_dict(params))

    def create(self, file_id: str, *, permission: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("POST", f"files/{quote_segment(file_id)}/permissions", params=compact_dict(params), body=permission)

    def update(self, file_id: str, permission_id: str, *, permission: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("PATCH", f"files/{quote_segment(file_id)}/permissions/{quote_segment(permission_id)}", params=compact_dict(params), body=permission)

    def delete(self, file_id: str, permission_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("DELETE", f"files/{quote_segment(file_id)}/permissions/{quote_segment(permission_id)}", params=compact_dict(params))


class CommentsResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/comments", params=compact_dict(params))

    def get(self, file_id: str, comment_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}", params=compact_dict(params))

    def create(self, file_id: str, *, comment: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", f"files/{quote_segment(file_id)}/comments", body=comment)

    def update(self, file_id: str, comment_id: str, *, comment: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("PATCH", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}", body=comment)

    def delete(self, file_id: str, comment_id: str) -> Dict[str, Any]:
        return self.client.request("DELETE", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}")


class RepliesResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, file_id: str, comment_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}/replies", params=compact_dict(params))

    def get(self, file_id: str, comment_id: str, reply_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}/replies/{quote_segment(reply_id)}", params=compact_dict(params))

    def create(self, file_id: str, comment_id: str, *, reply: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}/replies", body=reply)

    def update(self, file_id: str, comment_id: str, reply_id: str, *, reply: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("PATCH", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}/replies/{quote_segment(reply_id)}", body=reply)

    def delete(self, file_id: str, comment_id: str, reply_id: str) -> Dict[str, Any]:
        return self.client.request("DELETE", f"files/{quote_segment(file_id)}/comments/{quote_segment(comment_id)}/replies/{quote_segment(reply_id)}")


class RevisionsResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, file_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/revisions", params=compact_dict(params))

    def get(self, file_id: str, revision_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"files/{quote_segment(file_id)}/revisions/{quote_segment(revision_id)}", params=compact_dict(params))

    def update(self, file_id: str, revision_id: str, *, revision: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("PATCH", f"files/{quote_segment(file_id)}/revisions/{quote_segment(revision_id)}", body=revision)

    def delete(self, file_id: str, revision_id: str) -> Dict[str, Any]:
        return self.client.request("DELETE", f"files/{quote_segment(file_id)}/revisions/{quote_segment(revision_id)}")


class ChangesResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def start_page_token(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "changes/startPageToken", params=compact_dict(params))

    def list(self, page_token: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "changes", params=compact_dict({**params, "pageToken": page_token}))

    def watch(self, page_token: str, *, channel: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("POST", "changes/watch", params=compact_dict({**params, "pageToken": page_token}), body=channel)


class DrivesResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def list(self, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", "drives", params=compact_dict(params))

    def get(self, drive_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("GET", f"drives/{quote_segment(drive_id)}", params=compact_dict(params))

    def create(self, *, request_id: str, drive: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "drives", params={"requestId": request_id}, body=drive)

    def update(self, drive_id: str, *, drive: Dict[str, Any], **params: Any) -> Dict[str, Any]:
        return self.client.request("PATCH", f"drives/{quote_segment(drive_id)}", params=compact_dict(params), body=drive)

    def hide(self, drive_id: str) -> Dict[str, Any]:
        return self.client.request("POST", f"drives/{quote_segment(drive_id)}/hide")

    def unhide(self, drive_id: str) -> Dict[str, Any]:
        return self.client.request("POST", f"drives/{quote_segment(drive_id)}/unhide")

    def delete(self, drive_id: str, **params: Any) -> Dict[str, Any]:
        return self.client.request("DELETE", f"drives/{quote_segment(drive_id)}", params=compact_dict(params))


class SimpleResource:
    def __init__(self, client: DriveClient):
        self.client = client

    def request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, body: Optional[Any] = None) -> Dict[str, Any]:
        return self.client.request(method, path, params=compact_dict(params or {}), body=body)


def ensure_body(body: Optional[Any], **items: Any) -> Dict[str, Any]:
    payload = coerce_body(body)
    payload.update(compact_dict(items))
    return payload
