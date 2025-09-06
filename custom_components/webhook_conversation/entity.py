"""Shared base entity utilities for the webhook conversation integration."""

from __future__ import annotations

import base64
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
    CONF_AUTH_TYPE,
    CONF_ENABLE_STREAMING,
    CONF_OUTPUT_FIELD,
    CONF_PASSWORD,
    CONF_PROMPT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    DEFAULT_AUTH_TYPE,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_TIMEOUT,
    DOMAIN,
    AuthType,
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
        self._system_prompt = config_entry.options[CONF_PROMPT]
        self._streaming_enabled: bool = config_entry.options.get(
            CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING
        )
        self._auth_type = config_entry.options.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="webhook-conversation",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers based on configured auth type."""
        headers = {"Content-Type": "application/json"}

        if self._auth_type == AuthType.BASIC:
            username = self._config_entry.options.get(CONF_USERNAME, "")
            password = self._config_entry.options.get(CONF_PASSWORD, "")

            if username and password:
                credentials = base64.b64encode(
                    f"{username}:{password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
            else:
                _LOGGER.warning(
                    "Basic authentication configured but credentials missing"
                )

        return headers

    async def _send_payload(self, payload: WebhookConversationPayload) -> Any:
        """Send the payload to the webhook."""
        _LOGGER.debug(
            "Webhook request: %s",
            payload,
        )

        timeout = self._config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        session = async_get_clientsession(self.hass)
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        headers = self._get_auth_headers()

        async with session.post(
            self._webhook_url,
            json=payload,
            headers=headers,
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
        headers = self._get_auth_headers()

        async with session.post(
            self._webhook_url,
            json=payload,
            headers=headers,
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
        system_message = chat_log.content[0]
        if not isinstance(system_message, conversation.SystemContent):
            raise TypeError("First message must be a system message")

        messages = [
            self._convert_content_to_param(content)
            for content in chat_log.content[1:-1]
        ]

        return WebhookConversationPayload(
            {
                "messages": messages,
                "conversation_id": chat_log.conversation_id,
                "system_prompt": system_message.content,
                "stream": self._streaming_enabled,
                "query": "",
            }
        )

    def _convert_content_to_param(
        self, content: conversation.Content
    ) -> WebhookConversationMessage:
        """Convert native chat content into a simple dict."""
        return WebhookConversationMessage(
            {
                "role": content.role,
                "content": str(content.tool_result or "")
                if isinstance(content, conversation.ToolResultContent)
                else content.content or "",
            }
        )
