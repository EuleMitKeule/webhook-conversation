"""Webhook conversation integration for Home Assistant."""

import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    CONF_AI_TASK_WEBHOOK_URL,
    CONF_AUTH_TYPE,
    CONF_ENABLE_STREAMING,
    CONF_OUTPUT_FIELD,
    CONF_PASSWORD,
    CONF_PROMPT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_WEBHOOK_URL,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_AUTH_TYPE,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_PROMPT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

PLATFORMS = [Platform.AI_TASK, Platform.CONVERSATION]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    _LOGGER.debug(
        "Setting up webhook conversation integration from config entry: %s",
        config_entry,
    )
    _LOGGER.debug("Config entry data: %s", config_entry.data)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle config entry unload."""
    _LOGGER.debug(
        "Unloading webhook conversation config entry %s", config_entry.entry_id
    )

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug(
        "Updating webhook conversation config entry %s", config_entry.entry_id
    )

    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating webhook conversation from version %s to 2", config_entry.version
    )
    if config_entry.version == 2:
        return True

    if config_entry.version > 2:
        return False

    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    options = {
        CONF_WEBHOOK_URL: config_entry.options.get(CONF_WEBHOOK_URL),
        CONF_OUTPUT_FIELD: config_entry.options.get(
            CONF_OUTPUT_FIELD, DEFAULT_OUTPUT_FIELD
        ),
        CONF_PROMPT: config_entry.options.get(CONF_PROMPT, DEFAULT_PROMPT),
        CONF_TIMEOUT: config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        CONF_ENABLE_STREAMING: config_entry.options.get(
            CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING
        ),
        CONF_AUTH_TYPE: config_entry.options.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE),
        CONF_USERNAME: config_entry.options.get(CONF_USERNAME),
        CONF_PASSWORD: config_entry.options.get(CONF_PASSWORD),
    }

    conversation_data = options.copy()
    conversation_subentry = ConfigSubentry(
        data=MappingProxyType(conversation_data),
        subentry_type="conversation",
        title=DEFAULT_CONVERSATION_NAME,
        unique_id=None,
    )
    hass.config_entries.async_add_subentry(config_entry, conversation_subentry)

    if conversation_entity_id := entity_registry.async_get_entity_id(
        "conversation", DOMAIN, f"{config_entry.entry_id}-conversation"
    ):
        entity_registry.async_remove(conversation_entity_id)

    if ai_task_url := config_entry.options.get(CONF_AI_TASK_WEBHOOK_URL):
        ai_task_data = options.copy()
        ai_task_data[CONF_WEBHOOK_URL] = ai_task_url

        ai_task_subentry = ConfigSubentry(
            data=MappingProxyType(ai_task_data),
            subentry_type="ai_task",
            title=DEFAULT_AI_TASK_NAME,
            unique_id=None,
        )
        hass.config_entries.async_add_subentry(config_entry, ai_task_subentry)

        if ai_task_entity_id := entity_registry.async_get_entity_id(
            "ai_task", DOMAIN, f"{config_entry.entry_id}-ai_task"
        ):
            entity_registry.async_remove(ai_task_entity_id)

    if device := device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.entry_id)}
    ):
        device_registry.async_remove_device(device.id)

    hass.config_entries.async_update_entry(
        config_entry,
        data={},
        options={},
        version=2,
    )

    _LOGGER.debug("Migration to version 2 successful")
    return True
