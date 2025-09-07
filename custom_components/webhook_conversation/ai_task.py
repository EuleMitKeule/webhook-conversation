"""AI Task platform for webhook conversation integration."""

from __future__ import annotations

import base64
import logging

import anyio
from voluptuous_openapi import convert

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import WebhookConversationLLMBaseEntity
from .models import WebhookConversationBinaryObject

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entity for webhook conversation."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "ai_task":
            continue

        async_add_entities(
            [WebhookAITaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class WebhookAITaskEntity(WebhookConversationLLMBaseEntity, ai_task.AITaskEntity):
    """Webhook AI Task entity."""

    _attr_supported_features = (
        ai_task.AITaskEntityFeature.GENERATE_DATA
        | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
    )

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task."""
        payload = self._build_payload(chat_log)
        payload["query"] = task.instructions
        payload["task_name"] = task.name

        binary_objects: list[WebhookConversationBinaryObject] = []
        if task.attachments:
            for attachment in task.attachments:
                async with await anyio.open_file(attachment.path, "rb") as f:
                    attachment_bytes = await f.read()
                    attachment_base64 = base64.b64encode(attachment_bytes).decode()
                    binary_objects.append(
                        WebhookConversationBinaryObject(
                            name=attachment.media_content_id,
                            path=attachment.path,
                            mime_type=attachment.mime_type,
                            data=attachment_base64,
                        )
                    )
            payload["binary_objects"] = binary_objects

        if task.structure and task.structure.schema:
            payload["structure"] = convert(
                task.structure.schema, custom_serializer=llm.selector_serializer
            )

        if self._streaming_enabled:
            reply_parts = [
                content_chunk
                async for content_chunk in self._send_payload_streaming(payload)
            ]
            reply = "".join(reply_parts)
        else:
            reply = await self._send_payload(payload)

        if not task.structure:
            text = reply if isinstance(reply, str) else str(reply)
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=reply,
        )
