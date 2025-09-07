"""Config flow for the webhook conversation integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
)

from .const import (
    CONF_AUTH_TYPE,
    CONF_ENABLE_STREAMING,
    CONF_NAME,
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
    MANUFACTURER,
    RECOMMENDED_AI_TASK_OPTIONS,
    RECOMMENDED_CONVERSATION_OPTIONS,
    AuthType,
)

_LOGGER = logging.getLogger(__name__)


def _get_subentry_schema(
    subentry_type: str, options: dict[str, Any] | None = None, is_new: bool = True
) -> vol.Schema:
    """Return the subentry configuration schema."""
    if options is None:
        options = {}

    schema_dict: dict[vol.Required | vol.Optional, Any] = {}

    if is_new:
        if subentry_type == "conversation":
            default_name = DEFAULT_CONVERSATION_NAME
        else:
            default_name = DEFAULT_AI_TASK_NAME

        schema_dict[vol.Required(CONF_NAME, default=default_name)] = str

    schema_dict.update(
        {
            vol.Required(
                CONF_WEBHOOK_URL,
                description={"suggested_value": options.get(CONF_WEBHOOK_URL)},
                default=None,
            ): str,
            vol.Optional(
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

    return vol.Schema(schema_dict)


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

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return self.async_create_entry(title=MANUFACTURER, data={}, subentries=[])

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {
            "conversation": WebhookSubentryFlowHandler,
            "ai_task": WebhookSubentryFlowHandler,
        }


class WebhookSubentryFlowHandler(ConfigSubentryFlow):
    """Flow for managing webhook subentries."""

    def __init__(self) -> None:
        """Initialize the subentry flow handler."""
        self._user_input: dict[str, Any] = {}

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle initial step for new subentry."""
        return await self.async_step_set_options(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of existing subentry."""
        return await self.async_step_set_options(user_input)

    async def async_step_set_options(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Set subentry options."""
        errors: dict[str, str] = {}

        if user_input is None:
            if self._is_new:
                if self._subentry_type == "conversation":
                    options = RECOMMENDED_CONVERSATION_OPTIONS.copy()
                else:
                    options = RECOMMENDED_AI_TASK_OPTIONS.copy()
            else:
                options = self._get_reconfigure_subentry().data.copy()

            return self.async_show_form(
                step_id="set_options",
                data_schema=_get_subentry_schema(
                    self._subentry_type, options, self._is_new
                ),
            )

        _LOGGER.debug(
            "Processing webhook %s subentry configuration with user input: %s",
            self._subentry_type,
            user_input,
        )

        webhook_url: str = user_input[CONF_WEBHOOK_URL]
        if not webhook_url.startswith("http://") and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.error("Invalid webhook URL: %s", webhook_url)
            errors["base"] = "invalid_webhook_url"

        if errors:
            return self.async_show_form(
                step_id="set_options",
                data_schema=_get_subentry_schema(
                    self._subentry_type, user_input, self._is_new
                ),
                errors=errors,
            )

        self._user_input = user_input

        auth_type = user_input.get(CONF_AUTH_TYPE, DEFAULT_AUTH_TYPE)
        if auth_type == AuthType.BASIC:
            return await self.async_step_auth()

        if self._is_new:
            return self.async_create_entry(
                title=user_input.pop(CONF_NAME),
                data=user_input,
            )

        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            data=user_input,
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle authentication configuration step."""
        current_auth_data = {}
        if not self._is_new:
            existing_data = self._get_reconfigure_subentry().data
            if existing_data.get(CONF_AUTH_TYPE) == AuthType.BASIC:
                current_auth_data = {
                    CONF_USERNAME: existing_data.get(CONF_USERNAME, ""),
                    CONF_PASSWORD: existing_data.get(CONF_PASSWORD, ""),
                }

        if user_input is None:
            return self.async_show_form(
                step_id="auth", data_schema=_get_auth_schema(current_auth_data)
            )

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

        if self._is_new:
            return self.async_create_entry(
                title=config_data.pop(CONF_NAME),
                data=config_data,
            )

        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            data=config_data,
        )
