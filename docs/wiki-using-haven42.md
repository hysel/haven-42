# Using Haven 42

_For Haven 42 users. Development-stage limits are noted below._

## Conversation

Chat, writing, and summarization all use the same conversation. Leave **Choose
for me · Recommended** selected and describe the job normally. Pick Chat,
Write, or Summarize yourself only when you want to force a task type.

- Press **Enter** to send and **Shift+Enter** for a new line.
- Use **Up** and **Down** at the appropriate text boundary to recall prompts.
- Choose **New task** to clear the current memory-only conversation.
- Use the chat controls to change response text size and prompt-recall depth.
- Open **Response details · Advanced** for token counts and response speed.

Responses can contain headings, lists, code, quotations, and emoji. Haven 42
formats them without turning model-written code into an active webpage.

## Attach context

Use **Browse files** in the composer, drag supported files into the picker, or
paste a PNG screenshot from the clipboard. Haven 42 currently accepts a
bounded set of UTF-8 text, CSV, JSON, source-code, and PNG files.

Attachments stay in memory and go to the AI only when you send the message.
Haven 42 lets the AI read them but never runs attached code, scans folders, or
unpacks ZIP files.

If a file type or size isn't supported, the interface tells you why. PDF,
Office, OpenDocument, archives, executable content, and automatic local-file
scanning remain research or roadmap work rather than supported uploads.

## Models

The Models page lists what's already on your server. **Search public catalog**
looks up other model names online, but choosing a result doesn't download it.
Haven 42 first shows the exact model and destination; choose **Approve and
install** to start the Ollama download. Once Ollama lists that exact model,
Haven 42 makes it available in the selector. It doesn't silently download or
select one.

Server owners still have a manual-command fallback, but beginners shouldn't
need it. Large downloads currently show started/completed status rather than
byte-by-byte progress.

Automatic recommendations come only from Haven 42's safety and compatibility
records. You can still try another installed model. See [[Choose a
Model|Local-Model-Selection]].

## Research the web

Open **Research the web** in Chat, choose one of three paths, and enter the
search words. Haven 42 shows the exact words and destination; nothing leaves
the computer until you choose **Approve once**.

- **Wikipedia** returns bounded titles inside Haven 42. Reading one result
  requires a second approval and displays only inert page text.
- **Wider web with a cited answer** sends the approved words to Brave Search,
  reads at most five returned public HTTPS pages under strict limits, and asks
  the selected local model for a citation-bound answer. This path needs a Brave
  Search API key for that request. The key stays in memory, is never saved or
  sent to the model, and is cleared after use, cancellation, failure, or expiry.
- **Private browser search** opens the exact approved search on Brave Search in
  your normal browser. Haven 42 doesn't read those results, send them to the
  model, or follow links for you.

Retrieved pages can't run code, load remote media, create links, download
files, or start another search. The local model can't invoke or approve a
research path, choose a URL, receive the search key, or request a follow-up.
Only the cited-answer path sends bounded untrusted page text to the selected
local model.

Research state stays in memory. **New task** clears its approvals, results,
page text, and citations. See [[Privacy|Privacy-Policy]] for the network and
retention boundary.

If a research request is rejected, use **Open troubleshooting logs** beside the
message instead of hunting through System.

## AI server and computer settings

The AI server panel tells you where Ollama is running and warns if a
private-network connection isn't encrypted. Once connected, unchanged settings
can't reconnect or reset the task. Edit the endpoint or an advanced setting and
**Apply changes** becomes available with an explanation of the conversation
effect.

System settings include immediate, 5-minute, 15-minute, and 30-minute idle
model-cleanup choices. Current settings remain in memory only.

## Images

The supported image workflow uses a separately managed loopback Linux
ComfyUI/SDXL provider. Before generation, Haven 42 explains what the provider
retains, then returns the PNG to browser memory. Set it up with [[Set Up Local
Images|Local-Image-Provider-Onboarding]]. Other image, audio, and video paths
aren't available through this workflow.

## Technical details

**Technical details** is optional. It summarizes tested features and computer
setups; opening it doesn't run tests or contact an AI server. Detailed
engineering records are available through the [[Engineering and
Validation Index|Engineering-Index]].

For retention and network behavior, read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]].

**Next:** [[Troubleshooting]]
