# n8n Conversation

[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=My)](https://my.home-assistant.io/redirect/hacs_repository/?owner=EuleMitKeule&repository=n8n-conversation&category=integration)

![GitHub License](https://img.shields.io/github/license/eulemitkeule/n8n-conversation)
![GitHub Sponsors](https://img.shields.io/github/sponsors/eulemitkeule?logo=GitHub-Sponsors)

> [!NOTE]
> This integration requires Home Assistant `2025.8`.

_Integration to connect Home Assistant with n8n workflows through conversation agents._

**This integration allows you to use n8n workflows as conversation agents in Home Assistant, enabling powerful automation and AI-driven interactions with your smart home.**

## Features

- 🤖 Use n8n workflows as conversation agents in Home Assistant
- 🧩 AI Tasks via a dedicated webhook, supporting text or structured outputs
- 📎 Support for file attachments in AI Tasks (images, documents, etc.)
- 📡 Send conversation context and exposed entities to n8n webhooks
- 🏠 Seamless integration with Home Assistant's voice assistant system
- 🔧 Configurable webhook URLs and output fields
- ⏱️ Configurable timeout for handling long-running workflows (1-300 seconds)

## Installation

### HACS (Recommended)

> [!NOTE]
> **Quick Install**: Click the "My Home Assistant" badge at the top of this README for one-click installation via HACS.

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add `https://github.com/eulemitkeule/n8n-conversation` as an Integration
3. Search for "n8n Conversation" in HACS and install it
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/eulemitkeule/n8n-conversation/releases)
2. Extract the `custom_components/n8n_conversation` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Home Assistant Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** and search for "n8n Conversation"
3. Configure the integration with:
   - **Name**: A friendly name for your n8n agent
   - **Webhook URL**: The URL of your n8n webhook endpoint (remember to activate the workflow in n8n and to use the production webhook URL)
   - **AI Task Webhook URL (optional)**: A separate webhook endpoint for AI Tasks
   - **Output Field**: The field name in the n8n response containing the reply (default: "output")
   - **Timeout**: The timeout in seconds for waiting for a response from n8n (default: 30 seconds, range: 1-300 seconds)

### n8n Workflow Setup

Create an n8n workflow with the following structure:

1. **Webhook Trigger**: Set up a webhook trigger to receive POST requests from Home Assistant
2. **Process the payload**: Your workflow should include a node to process the incoming payload from Home Assistant. This can be done using the "Set" node to extract relevant information from the incoming JSON.
3. **Your AI/Processing Logic**: Process the conversation and entity data
4. **Return Response**: Return a JSON response with your configured output field

Note: For AI Tasks, the output value should adhere to the JSON schema provided in the `structure` field.

#### Input schema

##### For **conversations**

```json
{
  "conversation_id": "abc123",
  "user_id": "user id from ha",
  "messages": [
    {
      "role": "assistant|system|tool_result|user",
      "content": "message content"
    }
  ],
  "query": "latest user message",
  "exposed_entities": [
    {
      "entity_id": "light.living_room",
      "name": "Living Room Light",
      "state": "on",
      "aliases": ["main light"],
      "area_id": "living_room",
      "area_name": "Living Room"
    }
  ],
  "extra_system_prompt": "optional additional system instructions"
}
```

##### For **AI tasks**

```json
{
  "conversation_id": "abc123",
  "messages": [
    {
      "role": "assistant|system|tool_result|user",
      "content": "message content"
    }
  ],
  "query": "task instructions",
  "task_name": "task name",
  "extra_system_prompt": "optional additional system instructions",
  "structure": "json schema for output",
  "binary_objects": [
    {
      "name": "filename.jpg",
      "path": "/path/to/file",
      "mime_type": "image/jpeg",
      "data": "base64_encoded_file_content"
    }
  ]
}
```

> [!NOTE]
> The `binary_objects` field is only included when attachments are present in the AI task. The `structure` field is only included when a JSON schema is provided by the action call. The `task_name` field is only included for AI tasks when provided by the action call. Each attachment is converted to base64 format and includes metadata such as filename, file path, and MIME type.

## Usage

### Voice Assistant Pipeline Setup

To use the n8n conversation agent with voice assistants, you need to create a voice assistant pipeline:

1. Go to **Settings** → **Voice assistants**
2. Click **Add Assistant**
3. Configure your pipeline:
   - **Name**: Give your pipeline a descriptive name (e.g., "n8n Assistant")
   - **Language**: Select your preferred language
   - **Speech-to-text**: Choose your preferred STT engine (e.g., Whisper, Google Cloud)
   - **Conversation agent**: Select your n8n conversation agent from the dropdown
   - **Text-to-speech**: Choose your preferred TTS engine (e.g., Google Translate, Piper)
   - **Wake word**: Optionally configure a wake word engine
4. Click **Create** to save your pipeline
5. Set this pipeline as the default for voice assistants or assign it to specific devices

## Attachment Support

The n8n conversation integration supports file attachments in AI Tasks, allowing you to send images, documents, and other files to your n8n workflows for processing.

### How Attachments Work

When an AI Task includes attachments, they are automatically:

- Read from the file system
- Encoded as base64 strings
- Included in the `binary_objects` field of the webhook payload

### Attachment Data Structure

Each attachment in the `binary_objects` array contains:

- `name`: The filename or media content ID
- `path`: The full file path on the system
- `mime_type`: The MIME type of the file (e.g., "image/jpeg", "application/pdf")
- `data`: The base64-encoded file content

### Processing Attachments in n8n

In your n8n workflow, you can process attachments by:

1. **Accessing the binary_objects array**: Use `{{ $json.body.binary_objects }}` to access all attachments
2. **Processing individual files**: Loop through the array or access specific attachments by index
3. **Decoding base64 data**: Use the function node in the example workflow or your own custom code to decode the file content
4. **File type handling**: Use the `mime_type` field to determine how to process different file types

> [!TIP]
> Attachment support is only available for AI Tasks, not regular conversation messages. Make sure your n8n workflow can handle payloads both with and without the `binary_objects` field.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- 🐛 [Report issues](https://github.com/eulemitkeule/n8n-conversation/issues)
- 💬 [GitHub Discussions](https://github.com/eulemitkeule/n8n-conversation/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
