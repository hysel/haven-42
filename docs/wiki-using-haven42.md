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
public catalog** looks for other model names online. Choosing a result does not
start a download: Haven 42 first shows the exact model and destination. Choose
**Approve and install** to ask the connected Ollama server to download it.
Haven 42 verifies that Ollama lists the exact model afterward, then makes it
available for you to choose. It never silently downloads or selects a model.

An advanced manual command remains available as a fallback for server owners,
but it is no longer the normal beginner path. Large downloads currently show
started/completed status rather than byte-by-byte progress.

Haven 42 recommends only choices that match its safety and compatibility
records. Advanced users can still try another installed model. See [[Choose a
Model|Local-Model-Selection]].

## Research the web

Chat includes a manual **Research the web** disclosure. Choose one of three
clearly separated paths, enter search words, and review the exact words and
destination before choosing **Approve once**. Nothing is sent before approval.

- **Wikipedia** returns bounded titles inside Haven 42. Reading one result
  requires a second approval and displays only inert page text.
- **Wider web with a cited answer** sends the approved words to Brave Search,
  reads at most five returned public HTTPS pages under strict limits, and asks
  the selected local model for a citation-bound answer. It requires a Brave
  Search API key for that request. The key stays in memory, is never saved, is
  cleared after use, cancellation, failure, or expiry, and is never sent to the
  model.
- **Private browser search** opens the exact approved search on Brave Search in your normal
  browser. Haven 42 does not read those results, send them to the model, or
  follow links for you.

Retrieved pages cannot run code, load remote media, create links, download
files, or start another search. The local model cannot invoke or approve any
research path, choose a URL, receive the search key, or request a follow-up.
Only the cited-answer path sends bounded untrusted page text to the selected
local model.

Research state stays in memory. **New task** clears its approvals, results,
page text, and citations. See [[Privacy|Privacy-Policy]] for the network and
retention boundary.

When a research request is rejected, use the visible **Open troubleshooting
logs** button beside the message. You do not need to hunt through System.

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
Detailed engineering records are available through the [[Engineering and
Validation Index|Engineering-Index]].

For retention and network behavior, read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]].

**Next:** [[Troubleshooting]]
