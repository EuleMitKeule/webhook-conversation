"""TTS platform for webhook conversation integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, cast

import aiohttp
from propcache.api import cached_property

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_SUPPORTED_LANGUAGES, CONF_TIMEOUT, CONF_VOICES, DEFAULT_TIMEOUT
from .entity import WebhookConversationBaseEntity
from .models import WebhookTTSRequestPayload

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entity for webhook conversation."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "tts":
            continue

        async_add_entities(
            [WebhookConversationTextToSpeechEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class WebhookConversationTextToSpeechEntity(
    WebhookConversationBaseEntity, TextToSpeechEntity
):
    """Webhook TTS entity."""

    _attr_has_entity_name = False
    _voices: list[Voice] | None = None

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize TTS entity."""
        super().__init__(config_entry, subentry)
        self._attr_name = self.device_info.get("name", subentry.title)

        supported_languages = subentry.data.get(CONF_SUPPORTED_LANGUAGES)
        self._attr_supported_languages = supported_languages
        self._attr_default_language = supported_languages[0]

        if voices := subentry.data.get(CONF_VOICES):
            self._attr_supported_options = [ATTR_VOICE]
            self._voices = [Voice(voice, voice) for voice in cast(list[str], voices)]

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return a list of supported voices for a language."""
        return self._voices

    @cached_property
    def default_options(self) -> Mapping[str, Any]:
        """Return a mapping with the default options."""
        return {
            ATTR_VOICE: self._voices[0],
        }

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS audio from webhook."""

        timeout = self._config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        session = async_get_clientsession(self.hass)
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        headers = self._get_auth_headers()

        payload: WebhookTTSRequestPayload = {
            "text": message,
            "language": language,
        }

        if voice := cast(str, options.get(ATTR_VOICE)):
            payload["voice"] = voice

        async with session.post(
            self._webhook_url,
            json=payload,
            headers=headers,
            timeout=client_timeout,
        ) as response:
            if response.status != 200:
                raise HomeAssistantError(
                    f"Error contacting TTS webhook: HTTP {response.status} - {response.reason}"
                )

            response_bytes = await response.read()
            content_type: str | None = response.headers.get("Content-Type")
            if not content_type or "/" not in content_type:
                raise HomeAssistantError(
                    f"Invalid Content-Type in TTS webhook response: {content_type}"
                )
            audio_format = content_type.split("/")[-1]
            if audio_format not in ["wav", "mp3"]:
                raise HomeAssistantError(
                    f"Unsupported audio format in TTS webhook response: {audio_format}"
                )

        return audio_format, response_bytes
