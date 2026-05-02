"""Shared base entity utilities for the webhook conversation integration."""

from __future__ import annotations

import base64
from collections.abc import AsyncGenerator
import json
import logging
from typing import Any

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
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
    CONF_WEBHOOK_URL,
    DEFAULT_AUTH_TYPE,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
    AuthType,
)
from .models import WebhookConversationMessage, WebhookConversationPayload

_LOGGER = logging.getLogger(__name__)


class WebhookConversationBaseEntity(Entity):
    """Base entity for webhook conversation integration providing shared basics."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize base properties shared by all webhook conversation entities."""
        self._config_entry = config_entry
        self._subentry = subentry
        self._webhook_url = subentry.data[CONF_WEBHOOK_URL]
        self._auth_type = subentry.data.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer=MANUFACTURER,
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers based on configured auth type."""
        headers = {"Content-Type": "application/json"}

        if self._auth_type == AuthType.BASIC:
            username = self._subentry.data.get(CONF_USERNAME, "")
            password = self._subentry.data.get(CONF_PASSWORD, "")

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


class WebhookConversationLLMBaseEntity(WebhookConversationBaseEntity):
    """Base entity for LLM-based webhook conversation entities (conversation and AI task)."""

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize LLM-specific properties."""
        super().__init__(config_entry, subentry)
        self._system_prompt = subentry.data[CONF_PROMPT]
        self._streaming_enabled: bool = subentry.data.get(
            CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING
        )

    async def _send_payload(
        self,
        payload: WebhookConversationPayload,
        allow_tool_only: bool = False,
    ) -> dict[str, Any]:
        """Send the payload to the webhook."""
        _LOGGER.debug(
            "Webhook request: %s",
            payload,
        )

        timeout = self._subentry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
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

        output_field: str = self._subentry.data.get(
            CONF_OUTPUT_FIELD, DEFAULT_OUTPUT_FIELD
        )
        if not isinstance(result, dict) or (
            output_field not in result
            and not (allow_tool_only and "tool_calls" in result)
        ):
            raise HomeAssistantError(f"Invalid webhook response: {result}")

        _LOGGER.debug("Webhook response: %s", result)
        return result

    async def _send_payload_streaming(
        self, payload: WebhookConversationPayload
    ) -> AsyncGenerator[dict[str, Any]]:
        """Send the payload to the webhook and stream the response."""
        _LOGGER.debug("Webhook streaming request: %s", payload)

        timeout = self._subentry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
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
                            chunk_type = chunk_data.get("type")
                            if chunk_type == "error":
                                raise HomeAssistantError(
                                    f"n8n error: {chunk_data.get('message', chunk_data)}"
                                )
                            # We don't break on "end" because n8n can send multiple
                            # begin/end blocks when using tools or intermediate steps.
                            # We keep reading until the stream actually closes.
                            yield chunk_data
                        except json.JSONDecodeError:
                            _LOGGER.warning(
                                "Failed to parse streaming response chunk: %s", line_str
                            )
                            continue

    def _build_payload(
        self, chat_log: conversation.ChatLog, include_last: bool = False
    ) -> WebhookConversationPayload:
        """Create a base payload from the chat log for webhook calls."""
        system_message = chat_log.content[0]
        if not isinstance(system_message, conversation.SystemContent):
            raise TypeError("First message must be a system message")

        end_idx = len(chat_log.content) if include_last else -1
        messages = [
            self._convert_content_to_param(content)
            for content in chat_log.content[1:end_idx]
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
        if isinstance(content, conversation.ToolResultContent):
            return WebhookConversationMessage(
                {
                    "role": content.role,
                    "content": json.dumps(content.tool_result)
                    if content.tool_result is not None
                    else "",
                    "tool_call_id": content.tool_call_id,
                    "tool_name": content.tool_name,
                }
            )
        if isinstance(content, conversation.AssistantContent) and content.tool_calls:
            return WebhookConversationMessage(
                {
                    "role": content.role,
                    "content": content.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "name": tool_call.tool_name,
                            "arguments": tool_call.tool_args,
                        }
                        for tool_call in content.tool_calls
                    ],
                }
            )
        return WebhookConversationMessage(
            {
                "role": content.role,
                "content": content.content or "",
            }
        )
