"""Vaultwarden item create and update tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


def _require_purpose(purpose: str) -> str:
    if not purpose or not purpose.strip():
        raise ValueError("purpose is required")
    return purpose


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create a login item in the user's authorized personal Vaultwarden vault via the Bitwarden CLI.",
    examples=[
        'load_tool("vaultwarden.create_login")(name="Example", username="me", password="secret", purpose="store new login")',
    ],
    tool_class="write",
)
def create_login(
    *,
    name: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    uris: Optional[List[Dict[str, Any]]] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: bool = False,
    fields: Optional[List[Dict[str, Any]]] = None,
    organization_id: Optional[str] = None,
    collection_ids: Optional[List[str]] = None,
    totp: Optional[str] = None,
    purpose: str = "create login",
) -> Dict[str, Any]:
    client = get_client()
    payload = client.build_login_payload(
        name=name,
        username=username,
        password=password,
        uris=uris,
        url=url,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        organization_id=organization_id,
        collection_ids=collection_ids,
        totp=totp,
    )
    return client.create_item(payload, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create a secure note in the user's authorized personal Vaultwarden vault via the Bitwarden CLI.",
    examples=[
        'load_tool("vaultwarden.create_secure_note")(name="Recovery codes", notes="stored offline", purpose="store recovery note")',
    ],
    tool_class="write",
)
def create_secure_note(
    *,
    name: str,
    notes: str,
    folder_id: Optional[str] = None,
    favorite: bool = False,
    fields: Optional[List[Dict[str, Any]]] = None,
    organization_id: Optional[str] = None,
    collection_ids: Optional[List[str]] = None,
    purpose: str = "create secure note",
) -> Dict[str, Any]:
    client = get_client()
    payload = client.build_secure_note_payload(
        name=name,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        organization_id=organization_id,
        collection_ids=collection_ids,
    )
    return client.create_item(payload, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create a payment card in the user's authorized personal Vaultwarden vault via the Bitwarden CLI.",
    examples=[
        'load_tool("vaultwarden.create_card")(name="Work card", cardholder_name="A User", purpose="store card")',
    ],
    tool_class="write",
)
def create_card(
    *,
    name: str,
    cardholder_name: Optional[str] = None,
    brand: Optional[str] = None,
    number: Optional[str] = None,
    exp_month: Optional[str] = None,
    exp_year: Optional[str] = None,
    code: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: bool = False,
    fields: Optional[List[Dict[str, Any]]] = None,
    organization_id: Optional[str] = None,
    collection_ids: Optional[List[str]] = None,
    purpose: str = "create card",
) -> Dict[str, Any]:
    client = get_client()
    payload = client.build_card_payload(
        name=name,
        cardholder_name=cardholder_name,
        brand=brand,
        number=number,
        exp_month=exp_month,
        exp_year=exp_year,
        code=code,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        organization_id=organization_id,
        collection_ids=collection_ids,
    )
    return client.create_item(payload, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create an identity item in the user's authorized personal Vaultwarden vault via the Bitwarden CLI.",
    examples=[
        'load_tool("vaultwarden.create_identity")(name="Personal identity", identity={"firstName": "A"}, purpose="store identity")',
    ],
    tool_class="write",
)
def create_identity(
    *,
    name: str,
    identity: Dict[str, Any],
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: bool = False,
    fields: Optional[List[Dict[str, Any]]] = None,
    organization_id: Optional[str] = None,
    collection_ids: Optional[List[str]] = None,
    purpose: str = "create identity",
) -> Dict[str, Any]:
    client = get_client()
    payload = client.build_identity_payload(
        name=name,
        identity=identity,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        organization_id=organization_id,
        collection_ids=collection_ids,
    )
    return client.create_item(payload, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create an item in the user's authorized personal Vaultwarden vault from a validated Bitwarden CLI payload.",
    examples=[
        'load_tool("vaultwarden.create_item")({"type": 2, "name": "Note", "notes": "text", "secureNote": {"type": 0}}, purpose="create custom payload")',
    ],
    tool_class="write",
)
def create_item(payload: Dict[str, Any], *, purpose: str = "create item") -> Dict[str, Any]:
    return get_client().create_item(payload, purpose=_require_purpose(purpose))


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Update an existing login in the user's authorized personal Vaultwarden vault by exact item id.",
    examples=[
        'load_tool("vaultwarden.update_login")("00000000-0000-0000-0000-000000000000", username="new", purpose="rotate login")',
    ],
    tool_class="write",
)
def update_login(
    item_id: str,
    *,
    purpose: str,
    name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    uris: Optional[List[Dict[str, Any]]] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: Optional[bool] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    collection_ids: Optional[List[str]] = None,
    totp: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().update_login(
        item_id,
        purpose=_require_purpose(purpose),
        name=name,
        username=username,
        password=password,
        uris=uris,
        url=url,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        collection_ids=collection_ids,
        totp=totp,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Update an existing secure note in the user's authorized personal Vaultwarden vault by exact item id.",
    examples=[
        'load_tool("vaultwarden.update_secure_note")("00000000-0000-0000-0000-000000000000", notes="updated", purpose="revise note")',
    ],
    tool_class="write",
)
def update_secure_note(
    item_id: str,
    *,
    purpose: str,
    name: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: Optional[bool] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    collection_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return get_client().update_secure_note(
        item_id,
        purpose=_require_purpose(purpose),
        name=name,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        collection_ids=collection_ids,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Update an existing payment card in the user's authorized personal Vaultwarden vault by exact item id.",
    examples=[
        'load_tool("vaultwarden.update_card")("00000000-0000-0000-0000-000000000000", exp_year="2030", purpose="update card expiry")',
    ],
    tool_class="write",
)
def update_card(
    item_id: str,
    *,
    purpose: str,
    name: Optional[str] = None,
    cardholder_name: Optional[str] = None,
    brand: Optional[str] = None,
    number: Optional[str] = None,
    exp_month: Optional[str] = None,
    exp_year: Optional[str] = None,
    code: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: Optional[bool] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    collection_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return get_client().update_card(
        item_id,
        purpose=_require_purpose(purpose),
        name=name,
        cardholder_name=cardholder_name,
        brand=brand,
        number=number,
        exp_month=exp_month,
        exp_year=exp_year,
        code=code,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        collection_ids=collection_ids,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Update an existing identity item in the user's authorized personal Vaultwarden vault by exact item id.",
    examples=[
        'load_tool("vaultwarden.update_identity")("00000000-0000-0000-0000-000000000000", identity_updates={"email": "me@example.com"}, purpose="update identity")',
    ],
    tool_class="write",
)
def update_identity(
    item_id: str,
    *,
    purpose: str,
    identity_updates: Dict[str, Any],
    name: Optional[str] = None,
    notes: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorite: Optional[bool] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    collection_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return get_client().update_identity(
        item_id,
        purpose=_require_purpose(purpose),
        identity_updates=identity_updates,
        name=name,
        notes=notes,
        folder_id=folder_id,
        favorite=favorite,
        fields=fields,
        collection_ids=collection_ids,
    )


@register_tool(
    namespace="vaultwarden",
    aliases=[],
    description="Create or update one custom field on an item in the user's authorized personal Vaultwarden vault.",
    examples=[
        'load_tool("vaultwarden.update_custom_field")("00000000-0000-0000-0000-000000000000", name="env", value="prod", purpose="tag item")',
    ],
    tool_class="write",
)
def update_custom_field(
    item_id: str,
    *,
    name: str,
    value: Optional[str] = None,
    field_type: str = "text",
    purpose: str,
    create_if_missing: bool = True,
) -> Dict[str, Any]:
    return get_client().update_custom_field(
        item_id,
        name=name,
        value=value,
        field_type=field_type,
        purpose=_require_purpose(purpose),
        create_if_missing=create_if_missing,
    )
