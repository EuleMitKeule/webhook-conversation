"Constants for the webhook conversation integration."

from homeassistant.helpers import llm

DOMAIN = "webhook_conversation"

CONF_NAME = "name"
CONF_WEBHOOK_URL = "webhook_url"
CONF_OUTPUT_FIELD = "output_field"
CONF_AI_TASK_WEBHOOK_URL = "ai_task_webhook_url"
CONF_TIMEOUT = "timeout"
CONF_ENABLE_STREAMING = "enable_streaming"
CONF_PROMPT = "prompt"

DEFAULT_NAME = "webhook"
DEFAULT_WEBHOOK_URL = ""
DEFAULT_OUTPUT_FIELD = "output"
DEFAULT_TIMEOUT = 30
DEFAULT_ENABLE_STREAMING = False
DEFAULT_PROMPT = llm.DEFAULT_INSTRUCTIONS_PROMPT
