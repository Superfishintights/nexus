"""Google People API contact group tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import clean_params, coerce_list, coerce_optional_bool, coerce_optional_int, coerce_optional_str, quote_resource_name, request_people, require_object


@register_tool(
    namespace="google_people",
    description="List Google contact groups.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.list_contact_groups')(page_size=50)"],
)
def list_contact_groups(
    *,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100,
    sync_token: Optional[str] = None,
    group_fields: Optional[str] = None,
) -> Dict[str, Any]:
    return request_people(
        "contactGroups",
        params=clean_params(
            {
                "pageToken": coerce_optional_str(page_token),
                "pageSize": coerce_optional_int(page_size),
                "syncToken": coerce_optional_str(sync_token),
                "groupFields": coerce_optional_str(group_fields),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Get one Google contact group.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.get_contact_group')('contactGroups/myContacts')"],
)
def get_contact_group(
    resource_name: str,
    *,
    max_members: Optional[int] = None,
    group_fields: Optional[str] = None,
) -> Dict[str, Any]:
    return request_people(
        quote_resource_name(resource_name),
        params=clean_params(
            {
                "maxMembers": coerce_optional_int(max_members),
                "groupFields": coerce_optional_str(group_fields),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Batch get Google contact groups by resource name.",
    aliases=[],
    tool_class="read",
    examples=["load_tool('google_people.batch_get_contact_groups')(['contactGroups/myContacts'])"],
)
def batch_get_contact_groups(
    resource_names: Any,
    *,
    max_members: Optional[int] = None,
    group_fields: Optional[str] = None,
) -> Dict[str, Any]:
    names = coerce_list(resource_names)
    if not names:
        raise ValueError("resource_names must contain at least one resource name")
    return request_people(
        "contactGroups:batchGet",
        params=clean_params(
            {
                "resourceNames": names,
                "maxMembers": coerce_optional_int(max_members),
                "groupFields": coerce_optional_str(group_fields),
            }
        ),
    )


@register_tool(
    namespace="google_people",
    description="Create a Google contact group.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.create_contact_group')('Friends')"],
)
def create_contact_group(
    name: str,
    *,
    contact_group: Optional[Any] = None,
    read_group_fields: Optional[str] = None,
) -> Dict[str, Any]:
    group = require_object(contact_group, "contact_group") if contact_group is not None else {"name": name}
    group.setdefault("name", name)
    return request_people(
        "contactGroups",
        method="POST",
        params=clean_params({"readGroupFields": coerce_optional_str(read_group_fields)}),
        payload={"contactGroup": group},
    )


@register_tool(
    namespace="google_people",
    description="Update a Google contact group.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.update_contact_group')('contactGroups/abc', {'name': 'New name'})"],
)
def update_contact_group(
    resource_name: str,
    contact_group: Any,
    *,
    update_group_fields: Optional[str] = None,
    read_group_fields: Optional[str] = None,
) -> Dict[str, Any]:
    return request_people(
        quote_resource_name(resource_name),
        method="PUT",
        params=clean_params(
            {
                "updateGroupFields": coerce_optional_str(update_group_fields),
                "readGroupFields": coerce_optional_str(read_group_fields),
            }
        ),
        payload={"contactGroup": require_object(contact_group, "contact_group")},
    )


@register_tool(
    namespace="google_people",
    description="Delete a Google contact group.",
    aliases=[],
    tool_class="destructive",
    examples=["load_tool('google_people.delete_contact_group')('contactGroups/abc')"],
)
def delete_contact_group(
    resource_name: str,
    *,
    delete_contacts: Optional[bool] = None,
) -> Dict[str, Any]:
    return request_people(
        quote_resource_name(resource_name),
        method="DELETE",
        params=clean_params({"deleteContacts": coerce_optional_bool(delete_contacts)}),
    )


@register_tool(
    namespace="google_people",
    description="Add or remove contacts from a Google contact group.",
    aliases=[],
    tool_class="write",
    examples=["load_tool('google_people.modify_contact_group_members')('contactGroups/abc', add_resource_names=['people/c123'])"],
)
def modify_contact_group_members(
    resource_name: str,
    *,
    add_resource_names: Optional[Any] = None,
    remove_resource_names: Optional[Any] = None,
) -> Dict[str, Any]:
    return request_people(
        f"{quote_resource_name(resource_name)}/members:modify",
        method="POST",
        payload={
            "resourceNamesToAdd": coerce_list(add_resource_names) or [],
            "resourceNamesToRemove": coerce_list(remove_resource_names) or [],
        },
    )
