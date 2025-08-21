"""Shared base entity utilities for the webhook conversation integration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import json
import logging
from typing import Any

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_ENABLE_STREAMING,
    CONF_OUTPUT_FIELD,
    CONF_TIMEOUT,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .models import WebhookConversationMessage, WebhookConversationPayload

_LOGGER = logging.getLogger(__name__)


class WebhookConversationBaseEntity(Entity):
    """Base mixin for webhook conversation entities providing shared helpers."""

    _attr_has_entity_name = True
    _attr_name = None
    _webhook_url: str

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize base properties shared by webhook conversation entities."""
        self._config_entry = config_entry
        self._streaming_enabled: bool = config_entry.options.get(
            CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING
        )
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="webhook-conversation",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    async def _send_payload(self, payload: WebhookConversationPayload) -> Any:
        """Send the payload to the webhook."""
        _LOGGER.debug(
            "Webhook request: %s",
            payload,
        )

        timeout = self._config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        session = async_get_clientsession(self.hass)
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with session.post(
            self._webhook_url,
            json=payload,
            timeout=client_timeout,
        ) as response:
            if response.status != 200:
                raise HomeAssistantError(
                    f"Error contacting webhook: HTTP {response.status} - {response.reason}"
                )
            result = await response.json()

        output_field: str = self._config_entry.options.get(
            CONF_OUTPUT_FIELD, DEFAULT_OUTPUT_FIELD
        )
        if not isinstance(result, dict) or output_field not in result:
            raise HomeAssistantError(f"Invalid webhook response: {result}")

        _LOGGER.debug("Webhook response: %s", result)
        return result.get(output_field)

    async def _send_payload_streaming(
        self, payload: WebhookConversationPayload
    ) -> AsyncGenerator[str]:
        """Send the payload to the webhook and stream the response."""
        _LOGGER.debug("Webhook streaming request: %s", payload)

        timeout = self._config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        session = async_get_clientsession(self.hass)
        client_timeout = aiohttp.ClientTimeout(total=timeout)

        async with session.post(
            self._webhook_url,
            json=payload,
            timeout=client_timeout,
        ) as response:
            if response.status != 200:
                raise HomeAssistantError(
                    f"Error contacting webhook: HTTP {response.status} - {response.reason}"
                )

            async for line in response.content:
                if line:
                    line_str = line.decode("utf-8").strip()
                    if line_str:
                        try:
                            chunk_data = json.loads(line_str)
                            if (
                                chunk_data.get("type") == "item"
                                and "content" in chunk_data
                            ):
                                yield chunk_data["content"]
                            elif chunk_data.get("type") == "end":
                                break
                        except json.JSONDecodeError:
                            _LOGGER.warning(
                                "Failed to parse streaming response chunk: %s", line_str
                            )
                            continue

    def _build_payload(
        self, chat_log: conversation.ChatLog
    ) -> WebhookConversationPayload:
        """Create a base payload from the chat log for webhook calls."""
        messages = [
            self._convert_content_to_param(content) for content in chat_log.content
        ]
        return WebhookConversationPayload(
            {
                "messages": messages,
                "conversation_id": chat_log.conversation_id,
                "extra_system_prompt": chat_log.extra_system_prompt,
                "stream": self._streaming_enabled,
            }
        )

    def _convert_content_to_param(
        self, content: conversation.Content
    ) -> WebhookConversationMessage:
        """Convert native chat content into a simple dict."""
        return WebhookConversationMessage(
            {
                "role": content.role,
                "content": str(content.tool_result)
                if isinstance(content, conversation.ToolResultContent)
                else content.content,
            }
        )
