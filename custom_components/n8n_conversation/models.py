"""Typed models for the n8n conversation integration payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

MessageRole = Literal["assistant", "system", "tool_result", "user"]


class N8nMessage(TypedDict):
    """A single message item sent to n8n."""

    role: MessageRole
    content: str


class N8nBinaryObject(TypedDict):
    """A single binary object sent to n8n."""

    name: str
    path: Path
    mime_type: str
    data: str


class N8nPayload(TypedDict):
    """Base payload shared by n8n webhook calls."""

    conversation_id: str
    messages: list[N8nMessage]
    query: NotRequired[str | None]
    extra_system_prompt: NotRequired[str | None]
    task_name: NotRequired[str | None]
    structure: NotRequired[dict[str, Any] | None]
    user_id: NotRequired[str | None]
    exposed_entities: NotRequired[str]
    binary_objects: NotRequired[list[N8nBinaryObject]]
