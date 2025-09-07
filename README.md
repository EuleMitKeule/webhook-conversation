# Webhook Conversation

[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=My)](https://my.home-assistant.io/redirect/hacs_repository/?owner=EuleMitKeule&repository=webhook-conversation&category=integration)

![GitHub License](https://img.shields.io/github/license/eulemitkeule/webhook-conversation)
![GitHub Sponsors](https://img.shields.io/github/sponsors/eulemitkeule?logo=GitHub-Sponsors)

> [!NOTE]
> This integration requires Home Assistant `>=2025.8`.

_Integration to connect Home Assistant conversation agents and AI features to external systems through webhooks._

**This integration allows you to use n8n workflows or other custom webhook-based systems as conversation agents in Home Assistant, enabling powerful automation and AI-driven interactions with your smart home.**

## Features

- 🤖 Use n8n workflows as conversation agents in Home Assistant
- 🧩 AI Tasks via a dedicated webhook, supporting text or structured outputs
- 💬 Text-to-Speech (TTS) support with custom webhook-based voice synthesis
- 🎤 Speech-to-Text (STT) support with custom webhook-based voice recognition
- 📎 Support for file attachments in AI Tasks (images, documents, etc.)
- 📡 Send conversation context and exposed entities to webhooks
- 🏠 Seamless integration with Home Assistant's voice assistant system
- 🔧 Configurable webhook URLs and output fields
- ⏱️ Configurable timeout for handling long-running workflows (1-300 seconds)
- 🚀 Response streaming for real-time conversation responses

## Quick Start

🚀 **New to n8n workflows?** Check out our [example workflow](examples/simple_n8n_workflow.json) for a complete working setup with OpenAI integration and attachment support!

## Installation

### HACS (Recommended)

> [!NOTE]
> **Quick Install**: Click the "My Home Assistant" badge at the top of this README for one-click installation via HACS.

1. Make sure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → ⋮ → Custom repositories
   - Add `https://github.com/eulemitkeule/webhook-conversation` with type `Integration`
3. Search for "Webhook Conversation" in HACS and install it
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/eulemitkeule/webhook-conversation/releases)
2. Extract the `custom_components/webhook_conversation` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Home Assistant Setup

The setup process consists of two steps:

#### Step 1: Create the Integration Entry

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** and search for "Webhook Conversation"
3. Add the integration (no configuration options are required at this stage)

#### Step 2: Add Conversation Agents and AI Tasks

After the integration is added, you'll see the "Webhook Conversation" integration on your integrations page. From there:

1. **Add Conversation Agent**: Click the **"Add Entry"** button on the integration page and select **"Conversation Agent"** to create a new webhook-based conversation agent. Configure it with:
   - **Webhook URL**: The URL of your webhook endpoint (remember to activate the workflow in n8n and to use the production webhook URL)
   - **Output Field**: The field name in the webhook response containing the reply (default: "output")
   - **Timeout**: The timeout in seconds for waiting for a response (default: 30 seconds, range: 1-300 seconds)
   - **Enable Response Streaming**: Enable real-time streaming of responses as they are generated (default: disabled)
   - **System Prompt**: A custom system prompt to provide additional context or instructions to your AI model

2. **Add AI Task**: Click the **"Add Entry"** button on the integration page and select **"AI Task"** to create a webhook-based AI task handler. Configure it with:
   - **Webhook URL**: The URL of your webhook endpoint (remember to activate the workflow in n8n and to use the production webhook URL)
   - **Output Field**: The field name in the webhook response containing the reply (default: "output")
   - **Timeout**: The timeout in seconds for waiting for a response (default: 30 seconds, range: 1-300 seconds)
   - **Enable Response Streaming**: Enable real-time streaming of responses as they are generated (default: disabled)
   - **System Prompt**: A custom system prompt to provide additional context or instructions to your AI model

3. **Add TTS (Text-to-Speech)**: Click the **"Add Entry"** button on the integration page and select **"TTS"** to create a webhook-based text-to-speech service. Configure it with:
   - **Webhook URL**: The URL of your webhook endpoint that will handle TTS requests
   - **Timeout**: The timeout in seconds for waiting for audio response (default: 30 seconds, range: 1-300 seconds)
   - **Supported Languages**: List of supported language codes (e.g., "en-US", "de-DE", "fr-FR")
   - **Voices**: Optional list of available voice names for speech synthesis
   - **Authentication**: Optional HTTP basic authentication for securing your webhook endpoint

4. **Add STT (Speech-to-Text)**: Click the **"Add Entry"** button on the integration page and select **"STT"** to create a webhook-based speech-to-text service. Configure it with:
   - **Webhook URL**: The URL of your webhook endpoint that will handle STT requests
   - **Timeout**: The timeout in seconds for waiting for transcription response (default: 30 seconds, range: 1-300 seconds)
   - **Supported Languages**: List of supported language codes (e.g., "en-US", "de-DE", "fr-FR")
   - **Output Field**: The field name in the webhook response containing the transcribed text (default: "output")
   - **Authentication**: Optional HTTP basic authentication for securing your webhook endpoint

> [!NOTE]
> You can add multiple conversation agents, AI task handlers, TTS services, and STT services by repeating steps 2-4. Each can be configured with different webhook URLs and settings to support various use cases.

### n8n Workflow Setup

Create an n8n workflow with the following structure:

1. **Webhook Trigger**: Set up a webhook trigger to receive POST requests from Home Assistant
2. **Process the payload**: Your workflow should include a node to process the incoming payload from Home Assistant. This can be done using the "Set" node to extract relevant information from the incoming JSON.
3. **Your AI/Processing Logic**: Process the conversation and entity data
4. **Return Response**: Return a JSON response with your configured output field

Note: For AI Tasks, the output value should adhere to the JSON schema provided in the `structure` field.

#### Example Workflow

For a quick start, you can use the provided example workflow that demonstrates a complete integration with OpenAI's GPT model and attachment and streaming support:

📁 **[Simple n8n Workflow](examples/simple_n8n_workflow.json)**

This example workflow includes:

- **Webhook Trigger**: Receives POST requests from Home Assistant
- **Extract Attachments**: JavaScript code node that processes binary attachments from AI Tasks
- **OpenAI Integration**: GPT model integration with dynamic response format (text or JSON)
- **AI Agent**: LangChain agent that handles the conversation and processes attachments
- **Response Handler**: Responses are returned to Home Assistant in chunks

**To use this example:**

1. Download the [workflow file](examples/simple_n8n_workflow.json)
2. Import it into your n8n instance (Settings → Import from file)
3. Configure your OpenAI credentials in the OpenAI node
4. Update the model name to match your available OpenAI model
5. Activate the workflow
6. Copy the webhook URL and use it in your Home Assistant n8n conversation integration

#### Input schema

##### For **conversations**

```json
{
  "conversation_id": "abc123",
  "user_id": "user id from ha",
  "language": "de-DE",
  "agent_id": "conversation.webhook_agent",
  "device_id": "satellite_device_id",
  "device_info": {
    "name": "Kitchen Voice Satellite",
    "manufacturer": "Raspberry Pi",
    "model": "Pi 4B"
  },
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
  "system_prompt": "optional additional system instructions",
  "stream": false
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
  "system_prompt": "optional additional system instructions",
  "structure": "json schema for output",
  "binary_objects": [
    {
      "name": "filename.jpg",
      "path": "/path/to/file",
      "mime_type": "image/jpeg",
      "data": "base64_encoded_file_content"
    }
  ],
  "stream": false
}
```

##### For **STT (Speech-to-Text)**

```json
{
  "audio": {
    "name": "audio.wav",
    "path": "/path/to/audio.wav",
    "mime_type": "audio/wav",
    "data": "base64_encoded_audio_content"
  },
  "language": "en-US"
}
```

> [!NOTE]
> For **conversations**: The `device_id` and `device_info` fields are only set when the conversation was initiated via a voice satellite. The `language` field contains the language code (e.g., "de-DE") configured for the conversation. The `agent_id` field contains the entity ID of the conversation agent.
>
> For **AI tasks**: The `binary_objects` field is only included when attachments are present in the AI task. The `structure` field is only included when a JSON schema is provided by the action call. The `task_name` field is only included for AI tasks when provided by the action call. Each attachment is converted to base64 format and includes metadata such as filename, file path, and MIME type.
>
> For **TTS**: The `voice` field is only included when a specific voice is requested and the TTS service has been configured with available voices. The webhook should return audio data with an appropriate Content-Type header (e.g., "audio/wav" or "audio/mp3").
>
> For **STT**: The audio data is automatically converted to the appropriate format and encoded as base64. The webhook should return a JSON response with the transcribed text in the configured output field (default: "output").

## Authentication

The webhook conversation integration supports **basic HTTP authentication** for secure communication with your webhook endpoints. This ensures that only authorized requests can access your n8n workflows or other webhook services.

### Configuration

To enable basic HTTP authentication:

1. In the integration configuration, provide:
   - **Username**: Your HTTP authentication username
   - **Password**: Your HTTP authentication password
2. The integration will automatically include the proper authentication headers in all requests to your webhook URLs

### n8n Authentication Setup

For n8n workflows, you can secure your webhook endpoints by:

1. **In your n8n workflow**:
   - Open the Webhook Trigger node
   - Go to the "Settings" tab
   - Under "Authentication", select "Basic Auth"
   - Set your desired username and password via the credential property

2. **In Home Assistant**:
   - Use the same username and password in your webhook conversation integration configuration
   - The integration will automatically authenticate with your secured n8n webhook

> [!IMPORTANT]
> Basic HTTP authentication credentials are transmitted with every request. Always use HTTPS to ensure credentials are encrypted in transit.

## Usage

### Voice Assistant Pipeline Setup

To use the n8n conversation agent with voice assistants, you need to create a voice assistant pipeline:

1. Go to **Settings** → **Voice assistants**
2. Click **Add Assistant**
3. Configure your pipeline:
   - **Name**: Give your pipeline a descriptive name (e.g., "Webhook Assistant")
   - **Language**: Select your preferred language
   - **Speech-to-text**: Choose your preferred STT engine (e.g., Whisper, Google Cloud, or your webhook STT service)
   - **Conversation agent**: Select your webhook conversation agent from the dropdown
   - **Text-to-speech**: Choose your preferred TTS engine (e.g., Google Translate, Piper, or your webhook TTS service)
   - **Wake word**: Optionally configure a wake word engine
4. Click **Create** to save your pipeline
5. Set this pipeline as the default for voice assistants or assign it to specific devices

## Response Streaming

The webhook conversation integration supports **optional response streaming** for real-time conversation responses. When enabled, responses are streamed as they are generated, providing a more natural and responsive conversation experience.

### How Response Streaming Works

When response streaming is enabled:

1. **Real-time Updates**: Responses appear in real-time as they are generated by your webhook endpoint
2. **Improved User Experience**: Users see responses being typed out naturally, similar to ChatGPT-style interfaces
3. **Better Performance**: No need to wait for the complete response before displaying it to the user

### Webhook Response Format for Streaming

When streaming is enabled, your webhook endpoint should return responses in a streaming format instead of a single JSON response. The expected format is:

```json
{"type": "item", "content": "First part of the response"}
{"type": "item", "content": " continues here"}
{"type": "item", "content": " and more content"}
{"type": "end"}
```

#### Example n8n Streaming Setup

To implement streaming in your n8n workflow:

1. **Configure Webhook Node**: Set the response mode to "Streaming"
2. **Configure Agent Node**: Enable streaming in the agent node settings

## Attachment Support

The webhook conversation integration supports file attachments in AI Tasks, allowing you to send images, documents, and other files to your n8n workflows for processing.

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

## Speech-to-Text (STT) Support

The webhook conversation integration includes support for custom Speech-to-Text services through webhooks, allowing you to use external STT engines like OpenAI's Whisper API, Google Cloud Speech-to-Text, or custom speech recognition solutions.

### How STT Works

When configured, the STT webhook integration:

1. **Receives audio data**: Home Assistant captures voice input from microphones or voice satellites
2. **Processes via webhook**: Your webhook endpoint receives the audio data and converts it to text
3. **Returns transcribed text**: The webhook returns the transcribed text in JSON format
4. **Integrates with conversation**: The transcribed text is passed to your conversation agent for processing

### STT Configuration

When adding an STT subentry, you can configure:

- **Webhook URL**: The endpoint that will handle speech-to-text transcription requests
- **Supported Languages**: List of language codes your STT service supports (e.g., "en-US", "de-DE", "fr-FR")
- **Output Field**: The field name in the webhook response containing the transcribed text (default: "output")
- **Timeout**: How long to wait for transcription (default: 30 seconds)
- **Authentication**: HTTP basic authentication for securing your webhook

### STT Request Format

Your webhook will receive POST requests with this JSON payload:

```json
{
  "audio": {
    "name": "audio.wav",
    "path": "/path/to/audio.wav",
    "mime_type": "audio/wav",
    "data": "base64_encoded_audio_content"
  },
  "language": "en-US"
}
```

### STT Response Format

Your webhook should return a JSON response with the transcribed text:

```json
{
  "output": "Hello, this is the transcribed text from the audio"
}
```

### Usage in Voice Assistants

Once configured, your STT webhook service will appear in Home Assistant's STT service list and can be used:

1. **Voice Assistant Pipelines**: Select your webhook STT service in voice assistant pipeline configuration
2. **Voice Satellites**: Use with Wyoming satellite devices or other voice input devices
3. **Mobile Apps**: Compatible with Home Assistant mobile app voice input

> [!TIP]
> The integration automatically converts raw audio streams to properly formatted WAV files with headers before encoding to base64. This ensures compatibility with most external STT services that expect standard audio file formats.

## Text-to-Speech (TTS) Support

The webhook conversation integration includes support for custom Text-to-Speech services through webhooks, allowing you to use external TTS engines like OpenAI's TTS API, ElevenLabs, or custom voice synthesis solutions.

### How TTS Works

When configured, the TTS webhook integration:

1. **Receives TTS requests**: Home Assistant sends text that needs to be synthesized to speech
2. **Processes via webhook**: Your webhook endpoint processes the text and generates audio
3. **Returns audio data**: The webhook returns audio data in WAV or MP3 format
4. **Plays in Home Assistant**: The audio is played through Home Assistant's audio system

### TTS Configuration

When adding a TTS subentry, you can configure:

- **Webhook URL**: The endpoint that will handle TTS synthesis requests
- **Supported Languages**: List of language codes your TTS service supports (e.g., "en-US", "de-DE", "fr-FR")
- **Voices**: Optional list of available voice names for different speaking styles
- **Timeout**: How long to wait for audio generation (default: 30 seconds)
- **Authentication**: HTTP basic authentication for securing your webhook

### TTS Request Format

Your webhook will receive POST requests with this JSON payload:

```json
{
  "text": "Hello, this is the text to be synthesized",
  "language": "en-US",
  "voice": "optional_voice_name"
}
```

### TTS Response Format

Your webhook should return audio data with the appropriate Content-Type header:

- **Content-Type**: Must be `audio/wav` or `audio/mp3`
- **Body**: Raw audio data in the specified format

### Usage in Voice Assistants

Once configured, your TTS webhook service will appear in Home Assistant's TTS service list and can be used:

1. **Voice Assistant Pipelines**: Select your webhook TTS service in voice assistant pipeline configuration
2. **TTS Service Calls**: Use the `tts.speak` service with your webhook TTS entity
3. **Media Players**: The generated audio can be played on any media player device

### Supported Audio Formats

The TTS webhook integration supports:
- **WAV**: Uncompressed audio format (`audio/wav`)
- **MP3**: Compressed audio format (`audio/mp3`)

> [!TIP]
> For best performance, consider using MP3 format to reduce bandwidth usage, especially for longer text synthesis. Make sure your webhook endpoint sets the correct Content-Type header to match the audio format being returned.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- 🐛 [Report issues](https://github.com/eulemitkeule/webhook-conversation/issues)
- 💬 [GitHub Discussions](https://github.com/eulemitkeule/webhook-conversation/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
