"""Conversation platform for webhook conversation integration."""

from collections.abc import AsyncIterator
import json
import logging
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_WEBHOOK_URL, DOMAIN
from .entity import WebhookConversationBaseEntity
from .models import WebhookConversationPayload

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the integration from a config entry."""
    async_add_entities(
        [WebhookConversationEntity(config_entry)],
    )


class WebhookConversationEntity(
    conversation.ConversationEntity,
    conversation.models.AbstractConversationAgent,
    WebhookConversationBaseEntity,
):
    """Webhook conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the agent."""
        WebhookConversationBaseEntity.__init__(self, config_entry)
        self._webhook_url = config_entry.options[CONF_WEBHOOK_URL]
        self._attr_unique_id = f"{config_entry.entry_id}-conversation"

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._config_entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self._config_entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process the user input and call the API."""
        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                user_llm_hass_api=None,
                user_llm_prompt=self._system_prompt,
                user_extra_system_prompt=user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_handle_chat_log(user_input, chat_log)

        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_handle_chat_log(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> None:
        """Send the chat log to the webhook and process the response."""
        payload = self._build_payload(chat_log)
        user_messages = [
            self._convert_content_to_param(user_message)
            for user_message in chat_log.content
            if isinstance(user_message, conversation.UserContent)
        ]

        if not user_messages:
            raise HomeAssistantError("No user message found in chat log")

        def set_default(obj: Any) -> Any:
            if isinstance(obj, set):
                return list(obj)
            return obj

        payload["user_id"] = user_input.context.user_id
        payload["query"] = user_messages[-1]["content"]
        payload["exposed_entities"] = json.dumps(
            self._get_exposed_entities(), default=set_default
        )

        if self._streaming_enabled:
            async for _ in chat_log.async_add_delta_content_stream(
                self.entity_id,
                self._transform_webhook_stream(payload),
            ):
                pass
        else:
            reply = await self._send_payload(payload)
            async for _ in chat_log.async_add_assistant_content(
                conversation.AssistantContent(
                    self.entity_id,
                    reply,
                )
            ):
                pass

    async def _transform_webhook_stream(
        self, payload: WebhookConversationPayload
    ) -> AsyncIterator[conversation.AssistantContentDeltaDict]:
        """Transform webhook streaming content into HA format."""
        yield {"role": "assistant"}

        async for content_delta in self._send_payload_streaming(payload):
            _LOGGER.debug("Webhook streaming response: %s", content_delta)
            yield {"content": content_delta}

    def _get_exposed_entities(self) -> list[dict[str, Any]]:
        states = [
            state
            for state in self.hass.states.async_all()
            if async_should_expose(self.hass, conversation.DOMAIN, state.entity_id)
        ]
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)
        area_registry = ar.async_get(self.hass)
        exposed_entities: list[dict[str, Any]] = []

        for state in states:
            entity_id = state.entity_id
            entity = entity_registry.async_get(entity_id)

            aliases: list[str] = []
            if entity and entity.aliases:
                aliases = list(entity.aliases)

            area_id = None
            area_name = None

            if entity and entity.area_id:
                area_id = entity.area_id
                area = area_registry.async_get_area(area_id)
                if area:
                    area_name = area.name
            elif entity and entity.device_id:
                device = device_registry.async_get(entity.device_id)
                if device and device.area_id:
                    area_id = device.area_id
                    area = area_registry.async_get_area(area_id)
                    if area:
                        area_name = area.name

            exposed_entities.append(
                {
                    "entity_id": entity_id,
                    "name": state.name,
                    "state": state.state,
                    "aliases": aliases,
                    "area_id": area_id,
                    "area_name": area_name,
                }
            )
        return exposed_entities
