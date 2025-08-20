"""Config flow for the webhook conversation integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_AI_TASK_WEBHOOK_URL,
    CONF_NAME,
    CONF_OUTPUT_FIELD,
    CONF_TIMEOUT,
    CONF_WEBHOOK_URL,
    DEFAULT_NAME,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_TIMEOUT,
    DEFAULT_WEBHOOK_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_schema(options: dict[str, Any] | None = None) -> vol.Schema:
    """Return the schema for the configuration form."""
    if options is None:
        options = {}

    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                description={"suggested_value": options.get(CONF_NAME, DEFAULT_NAME)},
                default=DEFAULT_NAME,
            ): str,
            vol.Required(
                CONF_WEBHOOK_URL,
                description={
                    "suggested_value": options.get(
                        CONF_WEBHOOK_URL, DEFAULT_WEBHOOK_URL
                    )
                },
                default=DEFAULT_WEBHOOK_URL,
            ): str,
            vol.Optional(
                CONF_AI_TASK_WEBHOOK_URL,
                description={
                    "suggested_value": options.get(
                        CONF_AI_TASK_WEBHOOK_URL, DEFAULT_WEBHOOK_URL
                    )
                },
                default=DEFAULT_WEBHOOK_URL,
            ): str,
            vol.Required(
                CONF_OUTPUT_FIELD,
                description={
                    "suggested_value": options.get(
                        CONF_OUTPUT_FIELD, DEFAULT_OUTPUT_FIELD
                    )
                },
                default=DEFAULT_OUTPUT_FIELD,
            ): str,
            vol.Optional(
                CONF_TIMEOUT,
                description={
                    "suggested_value": options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                },
                default=DEFAULT_TIMEOUT,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
        }
    )


class WebhookConversationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for webhook conversation integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_get_schema())

        _LOGGER.debug(
            "Creating webhook conversation configuration with user input: %s",
            user_input,
        )

        webhook_url: str = user_input[CONF_WEBHOOK_URL]
        if not webhook_url.startswith("http://") and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.error("Invalid webhook URL: %s", webhook_url)
            return self.async_show_form(
                step_id="user",
                data_schema=_get_schema(user_input),
                errors={"base": "invalid_webhook_url"},
            )

        ai_task_url: str = user_input.get(CONF_AI_TASK_WEBHOOK_URL, "")
        if ai_task_url and not ai_task_url.startswith(("http://", "https://")):
            _LOGGER.error("Invalid AI Task webhook URL: %s", ai_task_url)
            return self.async_show_form(
                step_id="user",
                data_schema=_get_schema(user_input),
                errors={"base": "invalid_webhook_url"},
            )

        await self.async_set_unique_id(user_input[CONF_NAME])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_NAME], data={}, options=user_input
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(dict(config_entry.options))


class OptionsFlowHandler(OptionsFlow):
    """Handle Options flow for webhook conversation integration."""

    def __init__(self, options: dict[str, Any]) -> None:
        """Initialize the options flow handler."""
        self.options = options

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=_get_schema(self.options),
            )

        _LOGGER.debug(
            "Updating webhook conversation configuration with user input: %s",
            user_input,
        )

        webhook_url: str = user_input[CONF_WEBHOOK_URL]
        if not webhook_url.startswith("http://") and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.error("Invalid webhook URL: %s", webhook_url)
            return self.async_show_form(
                step_id="init",
                data_schema=_get_schema(user_input),
                errors={"base": "invalid_webhook_url"},
            )

        ai_task_url: str = user_input.get(CONF_AI_TASK_WEBHOOK_URL, "")
        if ai_task_url and not ai_task_url.startswith(("http://", "https://")):
            _LOGGER.error("Invalid AI Task webhook URL: %s", ai_task_url)
            return self.async_show_form(
                step_id="init",
                data_schema=_get_schema(user_input),
                errors={"base": "invalid_webhook_url"},
            )

        return self.async_create_entry(data=user_input)
