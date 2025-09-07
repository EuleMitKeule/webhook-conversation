"""STT platform for webhook conversation integration."""

from __future__ import annotations

import base64
from collections.abc import AsyncIterable
import io
import logging
from pathlib import Path
import wave

import aiohttp

from homeassistant.components import stt
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_OUTPUT_FIELD,
    CONF_SUPPORTED_LANGUAGES,
    CONF_TIMEOUT,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_TIMEOUT,
)
from .entity import WebhookConversationBaseEntity
from .models import WebhookConversationBinaryObject, WebhookSTTRequestPayload

_LOGGER = logging.getLogger(__name__)


def _convert_to_wav(
    audio_data: bytes, sample_rate: int, bit_rate: int, channels: int = 1
) -> bytes:
    """Convert raw audio data to WAV format with proper headers.

    Args:
        audio_data: The raw audio data as bytes
        sample_rate: Sample rate in Hz (e.g., 16000)
        bit_rate: Bit depth (e.g., 16)
        channels: Number of audio channels (default: 1 for mono)

    Returns:
        Properly formatted WAV file as bytes
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(bit_rate // 8)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)

    return wav_buffer.getvalue()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STT entity for webhook conversation."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "stt":
            continue

        async_add_entities(
            [WebhookConversationSTTEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class WebhookConversationSTTEntity(
    WebhookConversationBaseEntity, stt.SpeechToTextEntity
):
    """Webhook STT entity."""

    _attr_has_entity_name = False
    _attr_name: str

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize STT entity."""
        super().__init__(config_entry, subentry)
        self._attr_name: str = (
            (self.device_info.get("name") or subentry.title)
            if self.device_info
            else subentry.title
        )

        supported_languages: list[str] = subentry.data[CONF_SUPPORTED_LANGUAGES]
        self._supported_languages = supported_languages

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return self._supported_languages

    @property
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return a list of supported formats."""
        return [stt.AudioFormats.WAV, stt.AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return a list of supported codecs."""
        return [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return a list of supported bit rates."""
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return a list of supported sample rates."""
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return a list of supported channels."""
        return [stt.AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Process an audio stream to STT service."""
        # Collect all audio data from the stream
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        # Convert to proper WAV format if needed
        if metadata.format == stt.AudioFormats.WAV:
            # Convert raw audio data to proper WAV format with headers
            wav_data = _convert_to_wav(
                audio_data,
                metadata.sample_rate.value,
                metadata.bit_rate.value,
                metadata.channel.value,
            )
            audio_base64 = base64.b64encode(wav_data).decode("utf-8")
        else:
            # For other formats, use as-is (assuming they're already properly formatted)
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

        # Create audio binary object
        audio_object: WebhookConversationBinaryObject = {
            "name": f"audio.{metadata.format.value}",
            "path": Path(f"audio.{metadata.format.value}"),
            "mime_type": f"audio/{metadata.format.value}",
            "data": audio_base64,
        }

        # Prepare the payload
        payload: WebhookSTTRequestPayload = {
            "audio": audio_object,
            "language": metadata.language,
        }

        timeout = self._subentry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        session = async_get_clientsession(self.hass)
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        headers = self._get_auth_headers()

        try:
            async with session.post(
                self._webhook_url,
                json=payload,
                headers=headers,
                timeout=client_timeout,
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Error contacting STT webhook: HTTP %s - %s",
                        response.status,
                        response.reason,
                    )
                    return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

                response_data = await response.json()
                output_field = self._subentry.data.get(
                    CONF_OUTPUT_FIELD, DEFAULT_OUTPUT_FIELD
                )

                if output_field in response_data:
                    text = response_data[output_field]
                    if text and isinstance(text, str):
                        return stt.SpeechResult(
                            text.strip(),
                            stt.SpeechResultState.SUCCESS,
                        )

                _LOGGER.error(
                    "STT webhook response missing or invalid output field '%s': %s",
                    output_field,
                    response_data,
                )
                return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        except aiohttp.ClientError as err:
            _LOGGER.error("Error during STT request: %s", err)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
        except (ValueError, KeyError) as err:
            _LOGGER.error("Error parsing STT response: %s", err)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
