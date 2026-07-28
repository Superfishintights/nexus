"""Registered Google Drive v3 Nexus tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import DriveClient, coerce_body, coerce_list, compact_dict, get_client, quote_segment
from .resources import (
    ChangesResource,
    CommentsResource,
    DrivesResource,
    FilesResource,
    PermissionsResource,
    RepliesResource,
    RevisionsResource,
    SimpleResource,
    ensure_body,
)


def _files() -> FilesResource:
    return FilesResource(get_client())


def _permissions() -> PermissionsResource:
    return PermissionsResource(get_client())


def _comments() -> CommentsResource:
    return CommentsResource(get_client())


def _replies() -> RepliesResource:
    return RepliesResource(get_client())


def _revisions() -> RevisionsResource:
    return RevisionsResource(get_client())


def _changes() -> ChangesResource:
    return ChangesResource(get_client())


def _drives() -> DrivesResource:
    return DrivesResource(get_client())


def _simple() -> SimpleResource:
    return SimpleResource(get_client())


@register_tool(
    namespace="google_drive", tool_class="read",
    description="Search or list Drive files using Drive v3 query syntax and pagination.",
    examples=['load_tool("google_drive.search_files")(q="name contains \'report\'", page_size=10)'],
)
def search_files(
    *,
    q: Optional[str] = None,
    page_size: int = 100,
    page_token: Optional[str] = None,
    fields: Optional[str] = None,
    order_by: Optional[str] = None,
    spaces: Optional[str] = None,
    corpora: Optional[str] = None,
    drive_id: Optional[str] = None,
    include_items_from_all_drives: bool = True,
    supports_all_drives: bool = True,
    include_labels: Optional[str] = None,
    include_permissions_for_view: Optional[str] = None,
) -> Dict[str, Any]:
    return _files().list(
        q=q,
        pageSize=page_size,
        pageToken=page_token,
        fields=fields,
        orderBy=order_by,
        spaces=spaces,
        corpora=corpora,
        driveId=drive_id,
        includeItemsFromAllDrives=include_items_from_all_drives,
        supportsAllDrives=supports_all_drives,
        includeLabels=include_labels,
        includePermissionsForView=include_permissions_for_view,
    )


@register_tool(
    namespace="google_drive", tool_class="read",
    aliases=["list_drive_files"],
    description="List Drive files; alias-friendly wrapper around Drive file search.",
    examples=['load_tool("google_drive.list_files")(page_size=25)'],
)
def list_files(**kwargs: Any) -> Dict[str, Any]:
    return search_files(**kwargs)


@register_tool(
    namespace="google_drive", tool_class="read",
    description="Get Drive file metadata by file ID.",
    examples=['load_tool("google_drive.get_file")("1abc")'],
)
def get_file(
    file_id: str,
    *,
    fields: Optional[str] = None,
    include_labels: Optional[str] = None,
    include_permissions_for_view: Optional[str] = None,
    acknowledge_abuse: Optional[bool] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    return _files().get(
        file_id,
        fields=fields,
        includeLabels=include_labels,
        includePermissionsForView=include_permissions_for_view,
        acknowledgeAbuse=acknowledge_abuse,
        supportsAllDrives=supports_all_drives,
    )


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Create a Drive folder.",
    examples=['load_tool("google_drive.create_folder")("Projects", parent_id="root")'],
)
def create_folder(name: str, *, parent_id: Optional[str] = None, drive_id: Optional[str] = None) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    return _files().create(metadata=metadata, supportsAllDrives=True, driveId=drive_id)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Create Drive file metadata without uploading media.",
    examples=['load_tool("google_drive.create_file_metadata")(name="Notes", mime_type="text/plain")'],
)
def create_file_metadata(
    *,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    parents: Optional[Any] = None,
    body: Optional[Any] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    metadata = ensure_body(body, name=name, mimeType=mime_type)
    parent_values = coerce_list(parents)
    if parent_values is not None:
        metadata["parents"] = parent_values
    return _files().create(metadata=metadata, supportsAllDrives=supports_all_drives)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Update Drive file metadata such as name, description, starred, trashed, or appProperties.",
    examples=['load_tool("google_drive.update_file_metadata")("1abc", name="Updated name")'],
)
def update_file_metadata(
    file_id: str,
    *,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    parents: Optional[Any] = None,
    add_parents: Optional[str] = None,
    remove_parents: Optional[str] = None,
    body: Optional[Any] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    metadata = ensure_body(body, name=name, mimeType=mime_type)
    parent_values = coerce_list(parents)
    if parent_values is not None:
        metadata["parents"] = parent_values
    return _files().update(
        file_id,
        metadata=metadata,
        addParents=add_parents,
        removeParents=remove_parents,
        supportsAllDrives=supports_all_drives,
    )


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Move a Drive file by adding and/or removing parent folder IDs.",
    examples=['load_tool("google_drive.move_file")("1abc", add_parents="folder2", remove_parents="folder1")'],
)
def move_file(file_id: str, *, add_parents: Optional[str] = None, remove_parents: Optional[str] = None) -> Dict[str, Any]:
    if not add_parents and not remove_parents:
        raise ValueError("At least one of add_parents or remove_parents is required")
    return _files().update(file_id, metadata={}, addParents=add_parents, removeParents=remove_parents, supportsAllDrives=True)


@register_tool(
    namespace="google_drive", tool_class="destructive",
    description="Mark a Drive file as trashed.",
    examples=['load_tool("google_drive.trash_file")("1abc")'],
)
def trash_file(file_id: str) -> Dict[str, Any]:
    return _files().update(file_id, metadata={"trashed": True}, supportsAllDrives=True)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Restore a Drive file from trash.",
    examples=['load_tool("google_drive.untrash_file")("1abc")'],
)
def untrash_file(file_id: str) -> Dict[str, Any]:
    return _files().update(file_id, metadata={"trashed": False}, supportsAllDrives=True)


@register_tool(
    namespace="google_drive", tool_class="destructive",
    description="Permanently delete a Drive file.",
    examples=['load_tool("google_drive.delete_file")("1abc")'],
)
def delete_file(file_id: str, *, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _files().delete(file_id, supportsAllDrives=supports_all_drives)


@register_tool(
    namespace="google_drive", tool_class="destructive",
    description="Empty the signed-in user's Drive trash, optionally scoped to a shared drive.",
    examples=['load_tool("google_drive.empty_trash")()'],
)
def empty_trash(*, drive_id: Optional[str] = None) -> Dict[str, Any]:
    return _files().empty_trash(driveId=drive_id)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Copy a Drive file and optionally set new metadata.",
    examples=['load_tool("google_drive.copy_file")("1abc", name="Copy")'],
)
def copy_file(file_id: str, *, name: Optional[str] = None, parents: Optional[Any] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    metadata = ensure_body(body, name=name)
    parent_values = coerce_list(parents)
    if parent_values is not None:
        metadata["parents"] = parent_values
    return _files().copy(file_id, metadata=metadata, supportsAllDrives=True)


@register_tool(
    namespace="google_drive", tool_class="read",
    description="Generate Drive file IDs for later create/upload calls.",
    examples=['load_tool("google_drive.generate_file_ids")(count=3)'],
)
def generate_file_ids(*, count: int = 1, space: Optional[str] = None, id_type: Optional[str] = None) -> Dict[str, Any]:
    return _files().generate_ids(count=count, space=space, type=id_type)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Upload file content to Drive with multipart upload.",
    examples=['load_tool("google_drive.upload_file")(local_path="/tmp/report.pdf", parent_id="root")'],
)
def upload_file(
    *,
    content: Optional[str] = None,
    content_base64: Optional[str] = None,
    local_path: Optional[str] = None,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    parents: Optional[Any] = None,
    body: Optional[Any] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    client: DriveClient = get_client()
    metadata = ensure_body(body, name=client.infer_name(local_path=local_path, name=name))
    parent_values = coerce_list(parents)
    if parent_id and parent_values is None:
        parent_values = [parent_id]
    if parent_values is not None:
        metadata["parents"] = parent_values
    data = client.read_content(content=content, content_base64=content_base64, local_path=local_path)
    chosen_mime = client.infer_mime_type(local_path=local_path, mime_type=mime_type)
    return FilesResource(client).upload(metadata=metadata, content=data, mime_type=chosen_mime, supportsAllDrives=supports_all_drives)


@register_tool(
    namespace="google_drive", tool_class="write",
    description="Replace or patch Drive file content with multipart upload.",
    examples=['load_tool("google_drive.update_file_content")("1abc", content="updated text", mime_type="text/plain")'],
)
def update_file_content(
    file_id: str,
    *,
    content: Optional[str] = None,
    content_base64: Optional[str] = None,
    local_path: Optional[str] = None,
    name: Optional[str] = None,
    mime_type: Optional[str] = None,
    body: Optional[Any] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    client: DriveClient = get_client()
    metadata = ensure_body(body, name=client.infer_name(local_path=local_path, name=name))
    data = client.read_content(content=content, content_base64=content_base64, local_path=local_path)
    chosen_mime = client.infer_mime_type(local_path=local_path, mime_type=mime_type)
    return FilesResource(client).upload(
        metadata=metadata,
        content=data,
        mime_type=chosen_mime,
        file_id=file_id,
        supportsAllDrives=supports_all_drives,
    )


@register_tool(
    namespace="google_drive", tool_class="read",
    description="Download Drive file bytes as returned by the shared Google client.",
    examples=['load_tool("google_drive.download_file")("1abc")'],
)
def download_file(file_id: str, *, acknowledge_abuse: Optional[bool] = None, revision_id: Optional[str] = None) -> Any:
    return _files().download(file_id, acknowledgeAbuse=acknowledge_abuse, revisionId=revision_id)


@register_tool(
    namespace="google_drive", tool_class="read",
    description="Export a Google Workspace file to a requested MIME type.",
    examples=['load_tool("google_drive.export_file")("1abc", mime_type="application/pdf")'],
)
def export_file(file_id: str, mime_type: str) -> Any:
    return _files().export(file_id, mime_type)


@register_tool(namespace="google_drive", tool_class="read", description="List permissions for a Drive file.", examples=['load_tool("google_drive.list_permissions")("1abc")'])
def list_permissions(file_id: str, *, page_size: int = 100, page_token: Optional[str] = None, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _permissions().list(file_id, pageSize=page_size, pageToken=page_token, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="read", description="Get one Drive permission.", examples=['load_tool("google_drive.get_permission")("1abc", "perm")'])
def get_permission(file_id: str, permission_id: str, *, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _permissions().get(file_id, permission_id, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="admin", description="Create a Drive sharing permission.", examples=['load_tool("google_drive.create_permission")("1abc", role="reader", email_address="a@example.com")'])
def create_permission(
    file_id: str,
    *,
    role: str,
    permission_type: str = "user",
    email_address: Optional[str] = None,
    domain: Optional[str] = None,
    body: Optional[Any] = None,
    send_notification_email: Optional[bool] = None,
    email_message: Optional[str] = None,
    transfer_ownership: Optional[bool] = None,
    supports_all_drives: bool = True,
) -> Dict[str, Any]:
    permission = ensure_body(body, role=role, type=permission_type, emailAddress=email_address, domain=domain)
    return _permissions().create(
        file_id,
        permission=permission,
        sendNotificationEmail=send_notification_email,
        emailMessage=email_message,
        transferOwnership=transfer_ownership,
        supportsAllDrives=supports_all_drives,
    )


@register_tool(namespace="google_drive", tool_class="admin", aliases=["share_file"], description="Share a Drive file with a user, group, domain, or anyone.", examples=['load_tool("google_drive.share_file")("1abc", role="reader", email_address="a@example.com")'])
def share_file(file_id: str, **kwargs: Any) -> Dict[str, Any]:
    return create_permission(file_id, **kwargs)


@register_tool(namespace="google_drive", tool_class="admin", description="Update a Drive permission.", examples=['load_tool("google_drive.update_permission")("1abc", "perm", role="writer")'])
def update_permission(file_id: str, permission_id: str, *, role: Optional[str] = None, body: Optional[Any] = None, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _permissions().update(file_id, permission_id, permission=ensure_body(body, role=role), supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="admin", description="Delete a Drive permission.", examples=['load_tool("google_drive.delete_permission")("1abc", "perm")'])
def delete_permission(file_id: str, permission_id: str, *, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _permissions().delete(file_id, permission_id, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="read", description="List comments on a Drive file.", examples=['load_tool("google_drive.list_comments")("1abc")'])
def list_comments(file_id: str, *, include_deleted: bool = False, page_size: int = 100, page_token: Optional[str] = None, start_modified_time: Optional[str] = None) -> Dict[str, Any]:
    return _comments().list(file_id, includeDeleted=include_deleted, pageSize=page_size, pageToken=page_token, startModifiedTime=start_modified_time)


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive file comment.", examples=['load_tool("google_drive.get_comment")("1abc", "comment")'])
def get_comment(file_id: str, comment_id: str, *, include_deleted: bool = False) -> Dict[str, Any]:
    return _comments().get(file_id, comment_id, includeDeleted=include_deleted)


@register_tool(namespace="google_drive", tool_class="write", description="Create a Drive file comment.", examples=['load_tool("google_drive.create_comment")("1abc", content="Looks good")'])
def create_comment(file_id: str, *, content: Optional[str] = None, anchor: Optional[str] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _comments().create(file_id, comment=ensure_body(body, content=content, anchor=anchor))


@register_tool(namespace="google_drive", tool_class="write", description="Update a Drive file comment.", examples=['load_tool("google_drive.update_comment")("1abc", "comment", content="Updated")'])
def update_comment(file_id: str, comment_id: str, *, content: Optional[str] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _comments().update(file_id, comment_id, comment=ensure_body(body, content=content))


@register_tool(namespace="google_drive", tool_class="destructive", description="Delete a Drive file comment.", examples=['load_tool("google_drive.delete_comment")("1abc", "comment")'])
def delete_comment(file_id: str, comment_id: str) -> Dict[str, Any]:
    return _comments().delete(file_id, comment_id)


@register_tool(namespace="google_drive", tool_class="read", description="List replies on a Drive file comment.", examples=['load_tool("google_drive.list_replies")("1abc", "comment")'])
def list_replies(file_id: str, comment_id: str, *, include_deleted: bool = False, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    return _replies().list(file_id, comment_id, includeDeleted=include_deleted, pageSize=page_size, pageToken=page_token)


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive comment reply.", examples=['load_tool("google_drive.get_reply")("1abc", "comment", "reply")'])
def get_reply(file_id: str, comment_id: str, reply_id: str, *, include_deleted: bool = False) -> Dict[str, Any]:
    return _replies().get(file_id, comment_id, reply_id, includeDeleted=include_deleted)


@register_tool(namespace="google_drive", tool_class="write", description="Create a reply on a Drive file comment.", examples=['load_tool("google_drive.create_reply")("1abc", "comment", content="Done")'])
def create_reply(file_id: str, comment_id: str, *, content: Optional[str] = None, action: Optional[str] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _replies().create(file_id, comment_id, reply=ensure_body(body, content=content, action=action))


@register_tool(namespace="google_drive", tool_class="write", description="Update a Drive comment reply.", examples=['load_tool("google_drive.update_reply")("1abc", "comment", "reply", content="Updated")'])
def update_reply(file_id: str, comment_id: str, reply_id: str, *, content: Optional[str] = None, action: Optional[str] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _replies().update(file_id, comment_id, reply_id, reply=ensure_body(body, content=content, action=action))


@register_tool(namespace="google_drive", tool_class="destructive", description="Delete a Drive comment reply.", examples=['load_tool("google_drive.delete_reply")("1abc", "comment", "reply")'])
def delete_reply(file_id: str, comment_id: str, reply_id: str) -> Dict[str, Any]:
    return _replies().delete(file_id, comment_id, reply_id)


@register_tool(namespace="google_drive", tool_class="read", description="List Drive file revisions.", examples=['load_tool("google_drive.list_revisions")("1abc")'])
def list_revisions(file_id: str, *, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    return _revisions().list(file_id, pageSize=page_size, pageToken=page_token)


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive file revision.", examples=['load_tool("google_drive.get_revision")("1abc", "2")'])
def get_revision(file_id: str, revision_id: str, *, acknowledge_abuse: Optional[bool] = None) -> Dict[str, Any]:
    return _revisions().get(file_id, revision_id, acknowledgeAbuse=acknowledge_abuse)


@register_tool(namespace="google_drive", tool_class="write", description="Update Drive revision metadata.", examples=['load_tool("google_drive.update_revision")("1abc", "2", keep_forever=True)'])
def update_revision(file_id: str, revision_id: str, *, keep_forever: Optional[bool] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _revisions().update(file_id, revision_id, revision=ensure_body(body, keepForever=keep_forever))


@register_tool(namespace="google_drive", tool_class="destructive", description="Delete a Drive file revision.", examples=['load_tool("google_drive.delete_revision")("1abc", "2")'])
def delete_revision(file_id: str, revision_id: str) -> Dict[str, Any]:
    return _revisions().delete(file_id, revision_id)


@register_tool(namespace="google_drive", tool_class="read", description="Get the current Drive changes start page token.", examples=['load_tool("google_drive.get_start_page_token")()'])
def get_start_page_token(*, drive_id: Optional[str] = None, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _changes().start_page_token(driveId=drive_id, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="read", description="List Drive changes from a page token.", examples=['load_tool("google_drive.list_changes")("123")'])
def list_changes(page_token: str, *, page_size: int = 100, drive_id: Optional[str] = None, include_removed: bool = True, include_items_from_all_drives: bool = True, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _changes().list(page_token, pageSize=page_size, driveId=drive_id, includeRemoved=include_removed, includeItemsFromAllDrives=include_items_from_all_drives, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="write", description="Create a watch channel for Drive changes.", examples=['load_tool("google_drive.watch_changes")("123", channel={"id":"x","type":"web_hook","address":"https://example.com"})'])
def watch_changes(page_token: str, *, channel: Any, drive_id: Optional[str] = None, page_size: int = 100, supports_all_drives: bool = True) -> Dict[str, Any]:
    return _changes().watch(page_token, channel=coerce_body(channel), driveId=drive_id, pageSize=page_size, supportsAllDrives=supports_all_drives)


@register_tool(namespace="google_drive", tool_class="write", description="Stop a Drive watch notification channel.", examples=['load_tool("google_drive.stop_channel")(channel_id="id", resource_id="resource")'])
def stop_channel(*, channel_id: str, resource_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    return _simple().request("POST", "channels/stop", body=compact_dict({"id": channel_id, "resourceId": resource_id, "token": token}))


@register_tool(namespace="google_drive", tool_class="read", description="List shared drives.", examples=['load_tool("google_drive.list_drives")()'])
def list_drives(*, q: Optional[str] = None, page_size: int = 100, page_token: Optional[str] = None, use_domain_admin_access: Optional[bool] = None) -> Dict[str, Any]:
    return _drives().list(q=q, pageSize=page_size, pageToken=page_token, useDomainAdminAccess=use_domain_admin_access)


@register_tool(namespace="google_drive", tool_class="read", description="Get shared drive metadata.", examples=['load_tool("google_drive.get_drive")("drive_id")'])
def get_drive(drive_id: str, *, use_domain_admin_access: Optional[bool] = None) -> Dict[str, Any]:
    return _drives().get(drive_id, useDomainAdminAccess=use_domain_admin_access)


@register_tool(namespace="google_drive", tool_class="admin", description="Create a shared drive.", examples=['load_tool("google_drive.create_drive")("request-id", name="Team Drive")'])
def create_drive(request_id: str, *, name: Optional[str] = None, body: Optional[Any] = None) -> Dict[str, Any]:
    return _drives().create(request_id=request_id, drive=ensure_body(body, name=name))


@register_tool(namespace="google_drive", tool_class="admin", description="Update shared drive metadata.", examples=['load_tool("google_drive.update_drive")("drive_id", name="New name")'])
def update_drive(drive_id: str, *, name: Optional[str] = None, body: Optional[Any] = None, use_domain_admin_access: Optional[bool] = None) -> Dict[str, Any]:
    return _drives().update(drive_id, drive=ensure_body(body, name=name), useDomainAdminAccess=use_domain_admin_access)


@register_tool(namespace="google_drive", tool_class="write", description="Hide a shared drive from the default list.", examples=['load_tool("google_drive.hide_drive")("drive_id")'])
def hide_drive(drive_id: str) -> Dict[str, Any]:
    return _drives().hide(drive_id)


@register_tool(namespace="google_drive", tool_class="write", description="Unhide a shared drive.", examples=['load_tool("google_drive.unhide_drive")("drive_id")'])
def unhide_drive(drive_id: str) -> Dict[str, Any]:
    return _drives().unhide(drive_id)


@register_tool(namespace="google_drive", tool_class="destructive", description="Delete a shared drive.", examples=['load_tool("google_drive.delete_drive")("drive_id")'])
def delete_drive(drive_id: str, *, allow_item_deletion: Optional[bool] = None, use_domain_admin_access: Optional[bool] = None) -> Dict[str, Any]:
    return _drives().delete(drive_id, allowItemDeletion=allow_item_deletion, useDomainAdminAccess=use_domain_admin_access)


@register_tool(namespace="google_drive", tool_class="read", description="List labels applied to a Drive file.", examples=['load_tool("google_drive.list_file_labels")("1abc")'])
def list_file_labels(file_id: str, *, max_results: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    return _files().list_labels(file_id, maxResults=max_results, pageToken=page_token)


@register_tool(namespace="google_drive", tool_class="write", description="Modify labels on a Drive file.", examples=['load_tool("google_drive.modify_file_labels")("1abc", body={"labelModifications":[]})'])
def modify_file_labels(file_id: str, *, body: Any) -> Dict[str, Any]:
    return _files().modify_labels(file_id, body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="read", description="Get Drive account/user/storage metadata.", examples=['load_tool("google_drive.get_about")(fields="user,storageQuota")'])
def get_about(*, fields: Optional[str] = None) -> Dict[str, Any]:
    return _simple().request("GET", "about", params={"fields": fields})


@register_tool(namespace="google_drive", tool_class="read", description="List Drive apps available to open files.", examples=['load_tool("google_drive.list_apps")()'])
def list_apps(*, app_filter_extensions: Optional[str] = None, app_filter_mime_types: Optional[str] = None, language_code: Optional[str] = None) -> Dict[str, Any]:
    return _simple().request("GET", "apps", params={"appFilterExtensions": app_filter_extensions, "appFilterMimeTypes": app_filter_mime_types, "languageCode": language_code})


@register_tool(namespace="google_drive", tool_class="read", description="Get Drive app metadata.", examples=['load_tool("google_drive.get_app")("app_id")'])
def get_app(app_id: str) -> Dict[str, Any]:
    return _simple().request("GET", f"apps/{quote_segment(app_id)}")


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive long-running operation.", examples=['load_tool("google_drive.get_operation")("operations/name")'])
def get_operation(name: str) -> Dict[str, Any]:
    return _simple().request("GET", name.strip("/") if name.startswith("operations/") else f"operations/{quote_segment(name)}")


@register_tool(namespace="google_drive", tool_class="read", description="List access proposals for a Drive file.", examples=['load_tool("google_drive.list_access_proposals")("1abc")'])
def list_access_proposals(file_id: str, *, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    return _simple().request("GET", f"files/{quote_segment(file_id)}/accessproposals", params={"pageSize": page_size, "pageToken": page_token})


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive file access proposal.", examples=['load_tool("google_drive.get_access_proposal")("1abc", "proposal")'])
def get_access_proposal(file_id: str, proposal_id: str) -> Dict[str, Any]:
    return _simple().request("GET", f"files/{quote_segment(file_id)}/accessproposals/{quote_segment(proposal_id)}")


@register_tool(namespace="google_drive", tool_class="admin", description="Resolve a Drive file access proposal.", examples=['load_tool("google_drive.resolve_access_proposal")("1abc", "proposal", body={})'])
def resolve_access_proposal(file_id: str, proposal_id: str, *, body: Any) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/accessproposals/{quote_segment(proposal_id)}:resolve", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="read", description="List Drive file approvals.", examples=['load_tool("google_drive.list_approvals")("1abc")'])
def list_approvals(file_id: str, *, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    return _simple().request("GET", f"files/{quote_segment(file_id)}/approvals", params={"pageSize": page_size, "pageToken": page_token})


@register_tool(namespace="google_drive", tool_class="read", description="Get a Drive approval.", examples=['load_tool("google_drive.get_approval")("1abc", "approval")'])
def get_approval(file_id: str, approval_id: str) -> Dict[str, Any]:
    return _simple().request("GET", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}")


@register_tool(namespace="google_drive", tool_class="write", description="Start the Drive approval process for a file.", examples=['load_tool("google_drive.start_approval")("1abc", body={})'])
def start_approval(file_id: str, *, body: Optional[Any] = None) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals:start", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="write", description="Approve a Drive approval request.", examples=['load_tool("google_drive.approve_approval")("1abc", "approval", body={})'])
def approve_approval(file_id: str, approval_id: str, *, body: Optional[Any] = None) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}:approve", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="write", description="Decline a Drive approval request.", examples=['load_tool("google_drive.decline_approval")("1abc", "approval", body={})'])
def decline_approval(file_id: str, approval_id: str, *, body: Optional[Any] = None) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}:decline", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="write", description="Comment on a Drive approval request.", examples=['load_tool("google_drive.comment_approval")("1abc", "approval", body={"comment":"OK"})'])
def comment_approval(file_id: str, approval_id: str, *, body: Any) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}:comment", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="write", description="Reassign a Drive approval request.", examples=['load_tool("google_drive.reassign_approval")("1abc", "approval", body={})'])
def reassign_approval(file_id: str, approval_id: str, *, body: Any) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}:reassign", body=coerce_body(body))


@register_tool(namespace="google_drive", tool_class="write", description="Cancel a Drive approval request.", examples=['load_tool("google_drive.cancel_approval")("1abc", "approval", body={})'])
def cancel_approval(file_id: str, approval_id: str, *, body: Optional[Any] = None) -> Dict[str, Any]:
    return _simple().request("POST", f"files/{quote_segment(file_id)}/approvals/{quote_segment(approval_id)}:cancel", body=coerce_body(body))
