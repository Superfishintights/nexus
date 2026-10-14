"""Google People API person, contact, directory, and photo tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import (
    clean_params,
    coerce_list,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    quote_resource_name,
    request_people,
    require_array,
    require_object,
)


DEFAULT_PERSON_FIELDS = "names,emailAddresses,phoneNumbers,organizations,metadata"


@register_tool(
    namespace="google_people",
    description="Get one Google People person or contact resource.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.get_person')('people/c123', person_fields='names,emailAddresses')"],
)
def get_person(
    resource_name: str,
    *,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
    request_sync_token: Optional[bool] = None,
) -> Dict[str, Any]:
    """Read a person by resource name such as `people/me` or `people/c123`."""
    return request_people(
        quote_resource_name(resource_name),
        params=clean_params(
            {
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
                "requestSyncToken": coerce_optional_bool(request_sync_token),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Batch get Google People person resources.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.batch_get_people')(['people/me', 'people/c123'])"],
)
def batch_get_people(
    resource_names: Any,
    *,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
    request_mask_include_field: Optional[str] = None,
) -> Dict[str, Any]:
    names = coerce_list(resource_names)
    if not names:
        raise ValueError("resource_names must contain at least one resource name")
    return request_people(
        "people:batchGet",
        params=clean_params(
            {
                "resourceNames": names,
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
                "requestMask.includeField": coerce_optional_str(request_mask_include_field),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="List contact connections for a person, normally people/me.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.list_connections')(resource_name='people/me', page_size=100)"],
)
def list_connections(
    *,
    resource_name: str = "people/me",
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100,
    sort_order: Optional[str] = None,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
    sync_token: Optional[str] = None,
    request_sync_token: Optional[bool] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}/connections",
        params=clean_params(
            {
                "pageToken": coerce_optional_str(page_token),
                "pageSize": coerce_optional_int(page_size),
                "sortOrder": coerce_optional_str(sort_order),
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
                "syncToken": coerce_optional_str(sync_token),
                "requestSyncToken": coerce_optional_bool(request_sync_token),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Search contacts by query in Google People API.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.search_contacts')('Ada', page_size=10)"],
)
def search_contacts(
    query: str,
    *,
    page_size: Optional[int] = 20,
    read_mask: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    """Search contacts. Google recommends a warmup empty-query request before use."""
    return request_people(
        "people:searchContacts",
        params=clean_params(
            {
                "query": coerce_optional_str(query, allow_empty=True),
                "pageSize": coerce_optional_int(page_size),
                "readMask": coerce_optional_str(read_mask),
                "sources": coerce_list(sources),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="List domain directory people visible to the Google account.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.list_directory_people')(read_mask='names,emailAddresses')"],
)
def list_directory_people(
    *,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100,
    read_mask: str = "names,emailAddresses,phoneNumbers,organizations",
    sources: Optional[Any] = None,
    merge_sources: Optional[Any] = None,
    sync_token: Optional[str] = None,
    request_sync_token: Optional[bool] = None,
) -> Dict[str, Any]:
    return request_people(
        "people:listDirectoryPeople",
        params=clean_params(
            {
                "pageToken": coerce_optional_str(page_token),
                "pageSize": coerce_optional_int(page_size),
                "readMask": coerce_optional_str(read_mask),
                "sources": coerce_list(sources),
                "mergeSources": coerce_list(merge_sources),
                "syncToken": coerce_optional_str(sync_token),
                "requestSyncToken": coerce_optional_bool(request_sync_token),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Search domain directory people visible to the Google account.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.search_directory_people')('Ada', read_mask='names,emailAddresses')"],
)
def search_directory_people(
    query: str,
    *,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 20,
    read_mask: str = "names,emailAddresses,phoneNumbers,organizations",
    sources: Optional[Any] = None,
    merge_sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        "people:searchDirectoryPeople",
        params=clean_params(
            {
                "query": coerce_optional_str(query, allow_empty=True),
                "pageToken": coerce_optional_str(page_token),
                "pageSize": coerce_optional_int(page_size),
                "readMask": coerce_optional_str(read_mask),
                "sources": coerce_list(sources),
                "mergeSources": coerce_list(merge_sources),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Create a Google contact.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.create_contact')({'names': [{'givenName': 'Ada'}]})"],
)
def create_contact(
    person: Any,
    *,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        "people:createContact",
        method="POST",
        params=clean_params(
            {
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
            }
        ),
        payload=require_object(person, "person"),
    )


@register_tool(
    namespace="google_people",
    description="Update one Google contact using update-person-fields mask.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.update_contact')('people/c123', {'etag': '...', 'names': [...]}, update_person_fields='names')"],
)
def update_contact(
    resource_name: str,
    person: Any,
    *,
    update_person_fields: str,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}:updateContact",
        method="PATCH",
        params=clean_params(
            {
                "updatePersonFields": coerce_optional_str(update_person_fields),
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
            }
        ),
        payload=require_object(person, "person"),
    )


@register_tool(
    namespace="google_people",
    description="Delete one Google contact.",
    aliases=[],
    tool_class="destructive",
    examples=["load_tool('google_people.delete_contact')('people/c123')"],
)
def delete_contact(resource_name: str) -> Dict[str, Any]:
    return request_people(f"{quote_resource_name(resource_name)}:deleteContact", method="DELETE")


@register_tool(
    namespace="google_people",
    description="Batch create Google contacts.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.batch_create_contacts')([{'contactPerson': {'names': [{'givenName': 'Ada'}]}}])"],
)
def batch_create_contacts(
    contacts: Any,
    *,
    read_mask: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        "people:batchCreateContacts",
        method="POST",
        params=clean_params({"readMask": coerce_optional_str(read_mask), "sources": coerce_list(sources)}),
        payload={"contacts": require_array(contacts, "contacts")},
    )


@register_tool(
    namespace="google_people",
    description="Batch update Google contacts keyed by resource name.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.batch_update_contacts')({'people/c123': {'etag': '...', 'names': [...] }}, update_mask='names')"],
)
def batch_update_contacts(
    contacts: Any,
    *,
    update_mask: str,
    read_mask: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        "people:batchUpdateContacts",
        method="POST",
        params=clean_params({"sources": coerce_list(sources)}),
        payload={
            "contacts": require_object(contacts, "contacts"),
            "updateMask": update_mask,
            "readMask": read_mask,
        },
    )


@register_tool(
    namespace="google_people",
    description="Batch delete Google contacts by resource name.",
    aliases=[],
    tool_class="destructive",
    examples=["load_tool('google_people.batch_delete_contacts')(['people/c123', 'people/c456'])"],
)
def batch_delete_contacts(resource_names: Any) -> Dict[str, Any]:
    names = coerce_list(resource_names)
    if not names:
        raise ValueError("resource_names must contain at least one resource name")
    return request_people(
        "people:batchDeleteContacts",
        method="POST",
        payload={"resourceNames": names},
    )


@register_tool(
    namespace="google_people",
    description="Update a Google contact photo from base64-encoded image bytes.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.update_contact_photo')('people/c123', photo_bytes='...')"],
)
def update_contact_photo(
    resource_name: str,
    photo_bytes: str,
    *,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}:updateContactPhoto",
        method="PATCH",
        params=clean_params(
            {
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
            }
        ),
        payload={"photoBytes": photo_bytes},
    )


@register_tool(
    namespace="google_people",
    description="Delete a Google contact photo.",
    aliases=[],
    tool_class="destructive",
    examples=["load_tool('google_people.delete_contact_photo')('people/c123')"],
)
def delete_contact_photo(
    resource_name: str,
    *,
    person_fields: str = DEFAULT_PERSON_FIELDS,
    sources: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}:deleteContactPhoto",
        method="DELETE",
        params=clean_params(
            {
                "personFields": coerce_optional_str(person_fields),
                "sources": coerce_list(sources),
            }
        ),
    )
