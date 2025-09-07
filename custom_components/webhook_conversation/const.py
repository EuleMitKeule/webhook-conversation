"Constants for the webhook conversation integration."

from enum import StrEnum

from homeassistant.helpers import llm

DOMAIN = "webhook_conversation"
MANUFACTURER = "Webhook Conversation"

# Main config entry constants
CONF_NAME = "name"
DEFAULT_TITLE = "Webhook Conversation"

# Subentry names
DEFAULT_CONVERSATION_NAME = "Webhook Conversation"
DEFAULT_AI_TASK_NAME = "Webhook AI Task"

# Subentry configuration constants
CONF_WEBHOOK_URL = "webhook_url"
CONF_OUTPUT_FIELD = "output_field"
CONF_TIMEOUT = "timeout"
CONF_ENABLE_STREAMING = "enable_streaming"
CONF_PROMPT = "prompt"
CONF_AUTH_TYPE = "auth_type"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Defaults for subentries
DEFAULT_OUTPUT_FIELD = "output"
DEFAULT_TIMEOUT = 30
DEFAULT_ENABLE_STREAMING = True
DEFAULT_PROMPT = llm.DEFAULT_INSTRUCTIONS_PROMPT


class AuthType(StrEnum):
    """Authentication types for webhook requests."""

    NONE = "none"
    BASIC = "basic_auth"


DEFAULT_AUTH_TYPE = AuthType.NONE

# Recommended options for subentries
RECOMMENDED_CONVERSATION_OPTIONS = {
    CONF_OUTPUT_FIELD: DEFAULT_OUTPUT_FIELD,
    CONF_PROMPT: DEFAULT_PROMPT,
    CONF_TIMEOUT: DEFAULT_TIMEOUT,
    CONF_ENABLE_STREAMING: DEFAULT_ENABLE_STREAMING,
    CONF_AUTH_TYPE: DEFAULT_AUTH_TYPE,
}

RECOMMENDED_AI_TASK_OPTIONS = {
    CONF_OUTPUT_FIELD: DEFAULT_OUTPUT_FIELD,
    CONF_PROMPT: DEFAULT_PROMPT,
    CONF_TIMEOUT: DEFAULT_TIMEOUT,
    CONF_ENABLE_STREAMING: DEFAULT_ENABLE_STREAMING,
    CONF_AUTH_TYPE: DEFAULT_AUTH_TYPE,
}

# Legacy constants for backward compatibility
CONF_AI_TASK_WEBHOOK_URL = "ai_task_webhook_url"
