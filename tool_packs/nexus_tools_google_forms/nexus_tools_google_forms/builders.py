"""High-value Google Forms request and item builders."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool


def _drop_none(value: Dict[str, Any]) -> Dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _location(index: Optional[int]) -> Dict[str, Any]:
    return {} if index is None else {"location": {"index": index}}


def _question_item(question: Dict[str, Any], *, title: str, description: Optional[str] = None, item_id: Optional[str] = None) -> Dict[str, Any]:
    return _drop_none(
        {
            "itemId": item_id,
            "title": title,
            "description": description,
            "questionItem": {"question": question},
        }
    )


@register_tool(
    namespace="google_forms",
    description="Build a createItem request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_create_item_request")({"title": "Name", "questionItem": {"question": {"textQuestion": {}}}}, index=0)'],
    aliases=[],
    tool_class="utility",
)
def build_create_item_request(item: Dict[str, Any], *, index: Optional[int] = None) -> Dict[str, Any]:
    return {"createItem": {"item": item, **_location(index)}}


@register_tool(
    namespace="google_forms",
    description="Build an updateItem request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_update_item_request")({"itemId": "abc", "title": "Updated"}, update_mask="title")'],
    aliases=[],
    tool_class="utility",
)
def build_update_item_request(item: Dict[str, Any], *, update_mask: str, index: Optional[int] = None) -> Dict[str, Any]:
    request: Dict[str, Any] = {"item": item, "updateMask": update_mask}
    request.update(_location(index))
    return {"updateItem": request}


@register_tool(
    namespace="google_forms",
    description="Build a deleteItem request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_delete_item_request")("item-id")'],
    aliases=[],
    tool_class="utility",
)
def build_delete_item_request(item_id: str) -> Dict[str, Any]:
    return {"deleteItem": {"itemId": item_id}}


@register_tool(
    namespace="google_forms",
    description="Build a moveItem request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_move_item_request")("item-id", new_index=2)'],
    aliases=[],
    tool_class="utility",
)
def build_move_item_request(item_id: str, *, new_index: int) -> Dict[str, Any]:
    return {"moveItem": {"originalLocation": {"itemId": item_id}, "newLocation": {"index": new_index}}}


@register_tool(
    namespace="google_forms",
    description="Build an updateFormInfo request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_update_form_info_request")(title="Survey", description="Short survey")'],
    aliases=[],
    tool_class="utility",
)
def build_update_form_info_request(
    *,
    title: Optional[str] = None,
    document_title: Optional[str] = None,
    description: Optional[str] = None,
    update_mask: Optional[str] = None,
) -> Dict[str, Any]:
    info = _drop_none({"title": title, "documentTitle": document_title, "description": description})
    if not info:
        raise ValueError("At least one info field is required")
    mask = update_mask or ",".join(info.keys())
    return {"updateFormInfo": {"info": info, "updateMask": mask}}


@register_tool(
    namespace="google_forms",
    description="Build an updateSettings request for Google Forms batchUpdate.",
    examples=['load_tool("google_forms.build_update_settings_request")(is_quiz=True)'],
    aliases=[],
    tool_class="utility",
)
def build_update_settings_request(
    *,
    is_quiz: Optional[bool] = None,
    settings: Optional[Dict[str, Any]] = None,
    update_mask: Optional[str] = None,
) -> Dict[str, Any]:
    body = dict(settings or {})
    if is_quiz is not None:
        body.setdefault("quizSettings", {})["isQuiz"] = is_quiz
    if not body:
        raise ValueError("settings or is_quiz is required")
    return {"updateSettings": {"settings": body, "updateMask": update_mask or ",".join(body.keys())}}


@register_tool(
    namespace="google_forms",
    description="Build a text question item for Google Forms.",
    examples=['load_tool("google_forms.build_text_question_item")("Your name", paragraph=False, required=True)'],
    aliases=[],
    tool_class="utility",
)
def build_text_question_item(
    title: str,
    *,
    paragraph: bool = False,
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    question = _drop_none({"questionId": question_id, "required": required, "textQuestion": {"paragraph": paragraph}})
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a choice question item for radio, checkbox, or drop-down questions.",
    examples=['load_tool("google_forms.build_choice_question_item")("Pick one", ["A", "B"], choice_type="RADIO")'],
    aliases=[],
    tool_class="utility",
)
def build_choice_question_item(
    title: str,
    options: list[str | Dict[str, Any]],
    *,
    choice_type: str = "RADIO",
    shuffle: Optional[bool] = None,
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    normalized = [option if isinstance(option, dict) else {"value": option} for option in options]
    question = _drop_none(
        {
            "questionId": question_id,
            "required": required,
            "choiceQuestion": _drop_none({"type": choice_type, "options": normalized, "shuffle": shuffle}),
        }
    )
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a scale question item for Google Forms.",
    examples=['load_tool("google_forms.build_scale_question_item")("Rate it", low=1, high=5)'],
    aliases=[],
    tool_class="utility",
)
def build_scale_question_item(
    title: str,
    *,
    low: int,
    high: int,
    low_label: Optional[str] = None,
    high_label: Optional[str] = None,
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    question = _drop_none(
        {
            "questionId": question_id,
            "required": required,
            "scaleQuestion": _drop_none({"low": low, "high": high, "lowLabel": low_label, "highLabel": high_label}),
        }
    )
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a date question item for Google Forms.",
    examples=['load_tool("google_forms.build_date_question_item")("Preferred date", include_year=True)'],
    aliases=[],
    tool_class="utility",
)
def build_date_question_item(
    title: str,
    *,
    include_time: bool = False,
    include_year: bool = True,
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    question = _drop_none(
        {
            "questionId": question_id,
            "required": required,
            "dateQuestion": {"includeTime": include_time, "includeYear": include_year},
        }
    )
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a time question item for Google Forms.",
    examples=['load_tool("google_forms.build_time_question_item")("Preferred time", duration=False)'],
    aliases=[],
    tool_class="utility",
)
def build_time_question_item(
    title: str,
    *,
    duration: bool = False,
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    question = _drop_none({"questionId": question_id, "required": required, "timeQuestion": {"duration": duration}})
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a rating question item for Google Forms.",
    examples=['load_tool("google_forms.build_rating_question_item")("Rate us", rating_scale_level=5, icon_type="STAR")'],
    aliases=[],
    tool_class="utility",
)
def build_rating_question_item(
    title: str,
    *,
    rating_scale_level: int,
    icon_type: str = "STAR",
    required: bool = False,
    description: Optional[str] = None,
    question_id: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    question = _drop_none(
        {
            "questionId": question_id,
            "required": required,
            "ratingQuestion": {"ratingScaleLevel": rating_scale_level, "iconType": icon_type},
        }
    )
    return _question_item(question, title=title, description=description, item_id=item_id)


@register_tool(
    namespace="google_forms",
    description="Build a text item for instructions or static copy in Google Forms.",
    examples=['load_tool("google_forms.build_text_item")("Instructions", description="Answer every question")'],
    aliases=[],
    tool_class="utility",
)
def build_text_item(title: str, *, description: Optional[str] = None, item_id: Optional[str] = None) -> Dict[str, Any]:
    return _drop_none({"itemId": item_id, "title": title, "description": description, "textItem": {}})


@register_tool(
    namespace="google_forms",
    description="Build a page break item for Google Forms.",
    examples=['load_tool("google_forms.build_page_break_item")("Next section")'],
    aliases=[],
    tool_class="utility",
)
def build_page_break_item(title: str, *, description: Optional[str] = None, item_id: Optional[str] = None) -> Dict[str, Any]:
    return _drop_none({"itemId": item_id, "title": title, "description": description, "pageBreakItem": {}})
