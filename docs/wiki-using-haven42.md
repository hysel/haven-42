# Using Haven 42

_For Haven 42 users. Development-stage limits are noted below._

## Conversation

Chat, writing, and summarization share one continuous conversation. Haven 42
may suggest an installed model that better matches a request, but it never
switches models without asking.

- Press **Enter** to send and **Shift+Enter** for a new line.
- Use **Up** and **Down** at the appropriate text boundary to recall prompts.
- Choose **New task** to clear the current memory-only conversation.
- Use the chat controls to change response text size and prompt-recall depth.
- Expand run details for provider-reported token counts and timing.

Assistant responses support a safe subset of Markdown formatting and Unicode
emoji. Model-provided HTML, links, images, scripts, and event handlers are not
rendered as active content.

## Attach context

Use **Browse files** in the chat composer, drag admitted files into the picker,
or paste a PNG screenshot from the clipboard. Haven 42 currently accepts a
bounded set of UTF-8 text, CSV, JSON, source-code, and PNG files.

Selected attachments stay in memory, show a path-free preview, and are sent
only when you submit the task. They are treated as untrusted reference data and
are never executed. Haven 42 does not scan folders, watch files, extract
archives, or create a persistent document library.

The interface explains unsupported types and current size/count limits. PDF,
Office, OpenDocument, archives, executable content, and automatic local-file
scanning remain research or roadmap work rather than admitted upload features.

## Models

The Models view separates installed models from public catalog candidates.
Filtering installed models is offline. **Search public catalog** is an explicit
online action and never downloads a model.

An automatic choice requires matching name, immutable digest, and capability
evidence. Other installed models remain selectable as advanced, visibly
unverified choices. See [[Choose a Model|Local-Model-Selection]].

## Provider and system settings

The provider panel shows connection scope and warns about private-network HTTP.
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

## Software and evidence

Software shows read-only, plan-only workflows. The browser cannot pass workflow
arguments, start a child process, read a repository, or write a file.

Evidence displays bundled, sanitized project records. Opening it does not run a
test or contact a provider. Detailed engineering records are available through
the [[Evidence Dashboard|Evidence-Dashboard]].

For retention and network behavior, read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]].
