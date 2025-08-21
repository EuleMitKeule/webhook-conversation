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
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
)

from .const import (
    CONF_AI_TASK_WEBHOOK_URL,
    CONF_AUTH_TYPE,
    CONF_ENABLE_STREAMING,
    CONF_NAME,
    CONF_OUTPUT_FIELD,
    CONF_PASSWORD,
    CONF_PROMPT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_WEBHOOK_URL,
    DEFAULT_AUTH_TYPE,
    DEFAULT_ENABLE_STREAMING,
    DEFAULT_NAME,
    DEFAULT_OUTPUT_FIELD,
    DEFAULT_PROMPT,
    DEFAULT_TIMEOUT,
    DEFAULT_WEBHOOK_URL,
    DOMAIN,
    AuthType,
)

_LOGGER = logging.getLogger(__name__)


def _get_base_schema(options: dict[str, Any] | None = None) -> vol.Schema:
    """Return the base schema for the configuration form."""
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
                CONF_PROMPT,
                description={
                    "suggested_value": options.get(CONF_PROMPT, DEFAULT_PROMPT)
                },
                default=DEFAULT_PROMPT,
            ): TemplateSelector(),
            vol.Optional(
                CONF_TIMEOUT,
                description={
                    "suggested_value": options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                },
                default=DEFAULT_TIMEOUT,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
            vol.Optional(
                CONF_ENABLE_STREAMING,
                description={
                    "suggested_value": options.get(
                        CONF_ENABLE_STREAMING, DEFAULT_ENABLE_STREAMING
                    )
                },
                default=DEFAULT_ENABLE_STREAMING,
            ): bool,
            vol.Required(
                CONF_AUTH_TYPE,
                description={
                    "suggested_value": options.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
                },
                default=DEFAULT_AUTH_TYPE,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[auth_type.value for auth_type in AuthType],
                    translation_key="auth_type",
                )
            ),
        }
    )


def _get_auth_schema(options: dict[str, Any] | None = None) -> vol.Schema:
    """Return the authentication schema."""
    if options is None:
        options = {}

    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                description={"suggested_value": options.get(CONF_USERNAME, "")},
            ): str,
            vol.Required(
                CONF_PASSWORD,
                description={"suggested_value": options.get(CONF_PASSWORD, "")},
            ): str,
        }
    )


class WebhookConversationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for webhook conversation integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_get_base_schema())

        _LOGGER.debug(
            "Processing webhook conversation configuration with user input: %s",
            user_input,
        )

        errors = {}
        webhook_url: str = user_input[CONF_WEBHOOK_URL]
        if not webhook_url.startswith("http://") and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.error("Invalid webhook URL: %s", webhook_url)
            errors["base"] = "invalid_webhook_url"

        ai_task_url: str = user_input.get(CONF_AI_TASK_WEBHOOK_URL, "")
        if ai_task_url and not ai_task_url.startswith(("http://", "https://")):
            _LOGGER.error("Invalid AI Task webhook URL: %s", ai_task_url)
            errors["base"] = "invalid_webhook_url"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=_get_base_schema(user_input),
                errors=errors,
            )

        self._user_input = user_input

        auth_type = user_input.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
        if auth_type == AuthType.BASIC:
            return await self.async_step_auth()

        await self.async_set_unique_id(user_input[CONF_NAME])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_NAME], data={}, options=user_input
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle authentication configuration step."""
        if user_input is None:
            return self.async_show_form(step_id="auth", data_schema=_get_auth_schema())

        _LOGGER.debug("Processing authentication configuration")

        username = user_input.get(CONF_USERNAME, "").strip()
        password = user_input.get(CONF_PASSWORD, "").strip()

        if not username or not password:
            return self.async_show_form(
                step_id="auth",
                data_schema=_get_auth_schema(user_input),
                errors={"base": "invalid_auth"},
            )

        config_data = {**self._user_input, **user_input}

        await self.async_set_unique_id(config_data[CONF_NAME])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=config_data[CONF_NAME], data={}, options=config_data
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
        self._user_input: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=_get_base_schema(self.options),
            )

        _LOGGER.debug(
            "Updating webhook conversation configuration with user input: %s",
            user_input,
        )

        errors = {}
        webhook_url: str = user_input[CONF_WEBHOOK_URL]
        if not webhook_url.startswith("http://") and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.error("Invalid webhook URL: %s", webhook_url)
            errors["base"] = "invalid_webhook_url"

        ai_task_url: str = user_input.get(CONF_AI_TASK_WEBHOOK_URL, "")
        if ai_task_url and not ai_task_url.startswith(("http://", "https://")):
            _LOGGER.error("Invalid AI Task webhook URL: %s", ai_task_url)
            errors["base"] = "invalid_webhook_url"

        if errors:
            return self.async_show_form(
                step_id="init",
                data_schema=_get_base_schema(user_input),
                errors=errors,
            )

        self._user_input = user_input

        auth_type = user_input.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
        if auth_type == AuthType.BASIC:
            return await self.async_step_auth()

        return self.async_create_entry(data=user_input)

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle authentication configuration step."""
        current_auth_data = {}
        if self.options.get(CONF_AUTH_TYPE) == AuthType.BASIC:
            current_auth_data = {
                CONF_USERNAME: self.options.get(CONF_USERNAME, ""),
                CONF_PASSWORD: self.options.get(CONF_PASSWORD, ""),
            }

        if user_input is None:
            return self.async_show_form(
                step_id="auth", data_schema=_get_auth_schema(current_auth_data)
            )

        _LOGGER.debug("Processing authentication configuration update")

        username = user_input.get(CONF_USERNAME, "").strip()
        password = user_input.get(CONF_PASSWORD, "").strip()

        if not username or not password:
            return self.async_show_form(
                step_id="auth",
                data_schema=_get_auth_schema(user_input),
                errors={"base": "invalid_auth"},
            )

        config_data = {**self._user_input, **user_input}

        return self.async_create_entry(data=config_data)
