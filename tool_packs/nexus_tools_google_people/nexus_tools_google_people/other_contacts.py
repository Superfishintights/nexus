"""Google People API other contacts tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import clean_params, coerce_list, coerce_optional_bool, coerce_optional_int, coerce_optional_str, quote_resource_name, request_people


@register_tool(
    namespace="google_people",
    description="List Google Other Contacts.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.list_other_contacts')(read_mask='names,emailAddresses')"],
)
def list_other_contacts(
    *,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100,
    read_mask: str = "names,emailAddresses,phoneNumbers,metadata",
    sources: Optional[Any] = None,
    sync_token: Optional[str] = None,
    request_sync_token: Optional[bool] = None,
) -> Dict[str, Any]:
    return request_people(
        "otherContacts",
        params=clean_params(
            {
                "pageToken": coerce_optional_str(page_token),
                "pageSize": coerce_optional_int(page_size),
                "readMask": coerce_optional_str(read_mask),
                "sources": coerce_list(sources),
                "syncToken": coerce_optional_str(sync_token),
                "requestSyncToken": coerce_optional_bool(request_sync_token),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Search Google Other Contacts by query.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.search_other_contacts')('Ada')"],
)
def search_other_contacts(
    query: str,
    *,
    page_size: Optional[int] = 20,
    read_mask: str = "names,emailAddresses,phoneNumbers,metadata",
) -> Dict[str, Any]:
    """Search other contacts. Google recommends a warmup empty-query request before use."""
    return request_people(
        "otherContacts:search",
        params=clean_params(
            {
                "query": coerce_optional_str(query, allow_empty=True),
                "pageSize": coerce_optional_int(page_size),
                "readMask": coerce_optional_str(read_mask),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Copy an Other Contact into the authenticated user's contacts.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.copy_other_contact_to_my_contacts')('otherContacts/c123')"],
)
def copy_other_contact_to_my_contacts(
    resource_name: str,
    *,
    copy_mask: str = "names,emailAddresses,phoneNumbers",
    read_mask: str = "names,emailAddresses,phoneNumbers,metadata",
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}:copyOtherContactToMyContactsGroup",
        method="POST",
        params=clean_params(
            {
                "sources": coerce_list(sources),
            }
        ),
        payload={"copyMask": copy_mask, "readMask": read_mask},
    )
