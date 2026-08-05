# Using Haven 42

_For Haven 42 users. Development-stage limits are noted below._

## Conversation

Chat, writing, and summarization share one conversation. Keep **Choose for me ·
Recommended** selected and describe what you need in normal language. You can
choose Chat, Write, or Summarize yourself when you prefer.

- Press **Enter** to send and **Shift+Enter** for a new line.
- Use **Up** and **Down** at the appropriate text boundary to recall prompts.
- Choose **New task** to clear the current memory-only conversation.
- Use the chat controls to change response text size and prompt-recall depth.
- Open **Response details · Advanced** for token counts and response speed.

Responses can include headings, lists, code, quotations, and emoji. Haven 42
shows this formatting safely and does not turn model-written code into an
active webpage.

## Attach context

Use **Browse files** in the chat composer, drag admitted files into the picker,
or paste a PNG screenshot from the clipboard. Haven 42 currently accepts a
bounded set of UTF-8 text, CSV, JSON, source-code, and PNG files.

Selected attachments stay in memory and are sent only when you send the
message. Haven 42 lets the AI read them but never runs attached code. It does
not scan folders or unpack ZIP files.

The interface explains unsupported types and current size/count limits. PDF,
Office, OpenDocument, archives, executable content, and automatic local-file
scanning remain research or roadmap work rather than admitted upload features.

## Models

The Models page shows AI models already available on your server. **Search
public catalog** looks for other model names online but does not download them.

Haven 42 recommends only choices that match its safety and compatibility
records. Advanced users can still try another installed model. See [[Choose a
Model|Local-Model-Selection]].

## AI server and computer settings

The AI server panel shows where Ollama is running and warns when a
private-network connection is not encrypted.
Once connected, unchanged settings cannot reconnect or reset the task. Editing
the endpoint or an advanced setting enables **Apply changes** and discloses the
conversation effect.

System settings include immediate, 5-minute, 15-minute, and 30-minute idle
model-cleanup choices. Current settings remain in memory only.

## Images

The admitted image workflow uses a separately managed loopback Linux
ComfyUI/SDXL provider. Haven 42 discloses provider-side output retention before
generation and returns the PNG to browser memory. Set it up with [[Set Up Local
Images|Local-Image-Provider-Onboarding]]. Other image, audio, and video paths
remain gated.

## Technical details

**Technical details** is optional. It summarizes which features and computer
setups have been tested. Opening it does not run tests or contact an AI server.
Detailed engineering records are available through the [[Evidence
Dashboard|Evidence-Dashboard]].

For retention and network behavior, read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]].
