"""Ordinary Vikunja API v2 operations from the checked live specification."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description="List a task's attachments.", examples=['load_tool("vikunja.list_task_attachments")(1)'], tool_class='read', aliases=[])
def list_task_attachments(task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the attachment metadata for one task, paginated. Requires read access to the task. The file bytes are not included; fetch them from the download endpoint.'
    return get_client().page(f'tasks/{positive_id(task_id)}/attachments', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Delete a task attachment.', examples=['load_tool("vikunja.delete_task_attachment")(1, 1)'], tool_class='destructive', aliases=[])
def delete_task_attachment(task_id: int, attachment_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes one attachment and its underlying file. Requires write access to the task. The attachment must belong to the task in the path.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}/attachments/{positive_id(attachment_id)}', params=params)


@register_tool(namespace="vikunja", description="Upload bounded runtime-local files to a task using multipart form data.", examples=['load_tool("vikunja.upload_task_attachments")(1, ["notes.txt"])'], tool_class="write", aliases=[])
def upload_task_attachments(task_id: int, file_paths: list[str]) -> Any:
    """Upload 1 to 10 files inside VIKUNJA_ATTACHMENT_DIR. The API can return partial successes and an errors list. No automatic retry."""
    return get_client().upload_attachments(task_id, file_paths)


@register_tool(namespace="vikunja", description="Download a bounded attachment into a new private runtime-local file and return metadata.", examples=['load_tool("vikunja.download_task_attachment")(1, 2, "notes.txt")'], tool_class="read", aliases=[])
def download_task_attachment(task_id: int, attachment_id: int, output_name: str, preview_size: str | None = None) -> dict[str, Any]:
    """Never overwrite files or return binary data through Nexus. Optional preview_size is sm, md, lg or xl for images."""
    return get_client().download_attachment(task_id, attachment_id, output_name, preview_size=preview_size)
