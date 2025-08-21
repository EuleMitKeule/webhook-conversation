"""Typed models for the webhook conversation integration payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

MessageRole = Literal["assistant", "system", "tool_result", "user"]


class WebhookConversationMessage(TypedDict):
    """A single message item."""

    role: MessageRole
    content: str


class WebhookConversationBinaryObject(TypedDict):
    """A single binary object."""

    name: str
    path: Path
    mime_type: str
    data: str


class WebhookConversationPayload(TypedDict):
    """Base payload shared by webhook calls."""

    conversation_id: str
    messages: list[WebhookConversationMessage]
    query: NotRequired[str | None]
    system_prompt: NotRequired[str | None]
    task_name: NotRequired[str | None]
    structure: NotRequired[dict[str, Any] | None]
    user_id: NotRequired[str | None]
    exposed_entities: NotRequired[str]
    binary_objects: NotRequired[list[WebhookConversationBinaryObject]]
    stream: NotRequired[bool]
