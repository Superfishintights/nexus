"""Gmail settings tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import coerce_json, gmail_request, quote_path_segment, user_path


def _settings(user_id: str, suffix: str, *, method: str = "GET", payload: Any = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"settings/{suffix.strip('/')}"), method=method, payload=payload)


@register_tool(namespace="google_gmail", description="List Gmail send-as aliases.", examples=["load_tool('google_gmail.list_send_as')()"], aliases=[], tool_class="read")
def list_send_as(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "sendAs")


@register_tool(namespace="google_gmail", description="Get a Gmail send-as alias.", examples=["load_tool('google_gmail.get_send_as')('me@example.com')"], aliases=[], tool_class="read")
def get_send_as(send_as_email: str, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, f"sendAs/{quote_path_segment(send_as_email)}")


@register_tool(namespace="google_gmail", description="Patch a Gmail send-as alias.", examples=["load_tool('google_gmail.patch_send_as')('me@example.com', {'signature':'<p>Hi</p>'})"], aliases=[], tool_class="write")
def patch_send_as(send_as_email: str, payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, f"sendAs/{quote_path_segment(send_as_email)}", method="PATCH", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="List Gmail filters.", examples=["load_tool('google_gmail.list_filters')()"], aliases=[], tool_class="read")
def list_filters(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "filters")


@register_tool(namespace="google_gmail", description="Get a Gmail filter.", examples=["load_tool('google_gmail.get_filter')('filter_id')"], aliases=[], tool_class="read")
def get_filter(filter_id: str, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, f"filters/{quote_path_segment(filter_id)}")


@register_tool(namespace="google_gmail", description="Create a Gmail filter.", examples=["load_tool('google_gmail.create_filter')({'criteria': {'from': 'a@example.com'}, 'action': {'addLabelIds': ['STARRED']}})"], tool_class="write", aliases=[])
def create_filter(payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "filters", method="POST", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Delete a Gmail filter.", examples=["load_tool('google_gmail.delete_filter')('filter_id')"], aliases=[], tool_class="destructive")
def delete_filter(filter_id: str, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, f"filters/{quote_path_segment(filter_id)}", method="DELETE")


@register_tool(namespace="google_gmail", description="List Gmail forwarding addresses.", examples=["load_tool('google_gmail.list_forwarding_addresses')()"], aliases=[], tool_class="read")
def list_forwarding_addresses(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "forwardingAddresses")


@register_tool(namespace="google_gmail", description="Get Gmail vacation responder settings.", examples=["load_tool('google_gmail.get_vacation')()"], aliases=[], tool_class="read")
def get_vacation(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "vacation")


@register_tool(namespace="google_gmail", description="Update Gmail vacation responder settings.", examples=["load_tool('google_gmail.update_vacation')({'enableAutoReply': True})"], aliases=[], tool_class="write")
def update_vacation(payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "vacation", method="PUT", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Get Gmail language settings.", examples=["load_tool('google_gmail.get_language')()"], aliases=[], tool_class="read")
def get_language(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "language")


@register_tool(namespace="google_gmail", description="Update Gmail language settings.", examples=["load_tool('google_gmail.update_language')({'displayLanguage': 'en-GB'})"], aliases=[], tool_class="write")
def update_language(payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "language", method="PUT", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Get Gmail IMAP settings.", examples=["load_tool('google_gmail.get_imap')()"], aliases=[], tool_class="read")
def get_imap(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "imap")


@register_tool(namespace="google_gmail", description="Update Gmail IMAP settings.", examples=["load_tool('google_gmail.update_imap')({'enabled': True})"], aliases=[], tool_class="write")
def update_imap(payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "imap", method="PUT", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Get Gmail POP settings.", examples=["load_tool('google_gmail.get_pop')()"], aliases=[], tool_class="read")
def get_pop(user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "pop")


@register_tool(namespace="google_gmail", description="Update Gmail POP settings.", examples=["load_tool('google_gmail.update_pop')({'accessWindow': 'allMail'})"], aliases=[], tool_class="write")
def update_pop(payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return _settings(user_id, "pop", method="PUT", payload=coerce_json(payload) or {})
