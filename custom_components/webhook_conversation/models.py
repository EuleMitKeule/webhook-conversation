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

    # common fields
    conversation_id: str
    messages: list[WebhookConversationMessage]
    query: str
    system_prompt: str
    stream: bool

    # conversation fields
    agent_id: NotRequired[str]
    device_id: NotRequired[str | None]
    device_info: NotRequired[dict[str, Any] | None]
    exposed_entities: NotRequired[str]
    language: NotRequired[str]
    user_id: NotRequired[str | None]

    # task fields
    binary_objects: NotRequired[list[WebhookConversationBinaryObject]]
    structure: NotRequired[dict[str, Any] | None]
    task_name: NotRequired[str | None]


class WebhookTTSRequestPayload(TypedDict):
    """TTS request payload."""

    text: str
    language: str
    voice: NotRequired[str]
