# Local Web MVP

Haven 42 runs locally on Windows, Linux, and macOS. It opens a local browser page, reports sanitized host readiness, connects to an explicitly selected Ollama endpoint, discovers installed models, and provides repository-free chat, writing, summarization, and bounded user-selected text context.

This is a local application, not a hosted website. Source execution does not require Node.js, Rust, Tauri, a cloud account, executable signing, or a public deployment. Unsigned PyInstaller one-folder development packages also remove the global Python requirement; see `docs/portable-development-package.md`.

## First-Run Wizard

Each launch begins with a memory-only wizard that first offers:

- **Guided setup:** explicitly scan a registered, bounded, read-only set of local facts, review a zero-effect setup plan, then connect Ollama;
- **Connect existing setup:** skip the local scan and enter a user-managed loopback or private-network Ollama IP address;
- **Explore Haven 42:** open the interface without scanning or connecting a provider.

The Guided path reports operating system, architecture, logical processors, system memory, available storage, sanitized accelerator facts, and registered software presence/version. It does not query the Ollama daemon or discover installed models because readiness scanning is network-free; model discovery begins only after the user explicitly connects a policy-approved provider endpoint. The scan does not return hostname, username, hardware serials, device IDs, private paths, environment variables, credentials, process command lines, or network addresses. Probes use fixed engine-owned executable/argument pairs without a shell, network access, writes, installation, elevation, service changes, or driver changes.

The resulting plan is bound to the exact current in-memory snapshot. Browser code cannot submit hardware evidence, component IDs outside the strict registry, commands, URLs, paths, arguments, environment, or approval decisions. Every plan action says that installation is disabled. The separate installation broker is simulation-only and is not exposed by the web runtime.

The wizard is intentionally not marked complete on disk because the endpoint, readiness snapshot, and setup state are not persisted. A fresh launch therefore cannot silently reconnect to a previously entered server or reuse stale hardware facts.

The engine, not browser JavaScript, owns the recommendation catalog. An installed model is `recommended` and can be selected automatically only when its name, immutable Ollama digest, and passed capability evidence all match. A missing or different digest makes even a matching tag `unverified`. A model evidenced for another text capability is `compatible`, an unknown installed model is `unverified`, and an evidence-backed candidate that is not installed is `missing`. Compatible and unverified models remain explicit advanced choices and gain no filesystem, repository, tool, network, or download authority.

If the recommended model is missing, the wizard names it but disables completion. Haven 42 does not issue an Ollama pull. The user installs a disclosed model separately and checks the connection again.

## Find A Model

Expand **Find another model** in the Models panel. Typing filters the connected
provider's installed inventory locally and makes no network request. To search
the public Ollama catalog, enter a 1–64 character phrase and activate **Search
public catalog**. The button is the explicit online action. Only that phrase is
sent; endpoints, hardware facts, repository content, paths, and prompts are not.

Public results are research candidates, not recommendations. Haven 42 reports
their evidence as unverified, hardware fit as unknown, and license as requiring
review. Selecting an uninstalled result records a desired model in browser
memory and keeps its execution disabled. The displayed `ollama pull` command is
constructed from a strict model name and can be copied, but Haven 42 never runs
it or calls the Ollama pull API. Install through your separately managed Ollama
environment, check disk capacity and trust metadata there, then reconnect.

## Start Haven 42

Windows PowerShell:

```powershell
.\scripts\start-haven42-web.ps1
```

Linux:

```bash
./scripts/start-haven42-web.linux.sh
```

macOS:

```bash
./scripts/start-haven42-web.macos.sh
```

The launcher opens `http://127.0.0.1:4242`. Use `-NoOpen` on Windows or `--no-open` on Linux and macOS to start without opening the default browser. Use `-Port` or `--port` to select another loopback port. Automatic opening accepts only the engine-generated IPv4-loopback HTTP origin. Windows uses the registered URL association, macOS uses fixed `/usr/bin/open`, and Linux uses fixed allowlisted `/usr/bin/gio` or `/usr/bin/xdg-open` commands without a shell. Unix launch passes a minimal environment that excludes `BROWSER`. Linux uses only fixed system-owned application lookup roots for Flatpak, Ubuntu Snap, and base-system desktop registrations and never inherits caller-controlled `XDG_DATA_DIRS`. An immediate nonzero exit or process error advances to the next admitted Linux opener; only a zero exit or a still-running opener counts as success. If no admitted desktop opener is available, Haven 42 remains running and prints the URL for manual use. Every source launcher probes candidate commands and accepts only a working Python 3 interpreter; a stale Windows `py` command or store alias is skipped rather than failing later with a misleading server error.

## Accessibility And Capability Status

The wizard is a labeled modal with an announced description and current-step state. Keyboard focus enters the wizard after secure-session bootstrap and moves to the active step. Tab and Shift+Tab move among its visible controls; Escape dismisses the wizard and returns focus to a usable application control. Provider endpoint, timeout, cleanup, authentication, and other primary controls have a minimum 44-pixel target. A skip link, three-pixel high-contrast focus ring, navigation/main/complementary landmarks, one page-level heading, labeled form fields, text-backed status indicators, semantic status/alert/note regions, responsive layout, deterministic contrast checks, forced-color support, and reduced-motion behavior support keyboard and assistive-technology use. Live resource values remain visually current while their polite screen-reader summary is limited to one update per minute.

The separate local `/accessibility` route contains the application's self-assessed WCAG 2.1 Level AA target, implemented features, known testing gaps, technical scope, assessment approach, and accessibility issue-reporting link. The About view links to that statement. It explicitly does not claim third-party certification or completed manual testing across screen-reader and browser combinations.

The capability view is read-only and engine-derived. Chat, Writing, and Summarization change from `configuration-required` to `available` only after a successful provider check. Software stays `not-admitted-in-web`; Images stays `provider-profile-required`. Clicking either unavailable navigation item explains its state and never invokes an operation.

The System view can repeat the explicit read-only readiness scan. It also reports sanitized provider health and exact artifact-digest and catalog evidence matching. Its Software updates area makes no background request: only **Check official releases now** contacts Ollama's official GitHub release API. The request contains no chats, files, addresses, credentials, or hardware details, and the preference and result remain in session memory. A verified managed release still enters the existing guided setup review, download, checksum, extraction, local-health, and approval boundary; checking never downloads or activates it. A newer official release that is not in this build's admitted component registry is disclosed but cannot be installed by Haven 42.

The separate advanced **Evidence** navigation section loads only the bundled sanitized evidence catalog and agent-surface matrices, keeping validation metrics outside the everyday chat and setup flow. It reports committed record/model counts, the complete outcome distribution, per-surface supported/validated/blocked activity counts, and bounded install/configure/test status. A fixed explicit-click link opens the detailed Haven 42 Evidence Dashboard wiki in a separate no-referrer browsing context; the application never fetches it in the background and the renderer cannot change its address. The view does not run a test, contact a provider, inspect a user repository, start a process, write a file, or claim production readiness. A visible cleanup selector offers immediate, 5-minute, 15-minute, and 30-minute model residency. After connection, unchanged provider values show disabled `Connected` and the active System policy shows disabled `Applied`; even a programmatic unchanged submission makes no provider request and cannot reset the task. Editing the endpoint, timeout, or cleanup policy enables `Apply changes` and discloses that a successful changed connection starts a new task. While disconnected, selecting a cleanup policy only updates the in-memory choice for the next connection. These controls grant no installation or process authority.

## Provider-reported run details

Each successful text result may expose provider-reported input, output, and total
tokens; generation throughput; and load, prompt, generation, and total timing.
The renderer validates a strict nullable numeric schema and shows a compact
memory-only disclosure. These values are diagnostics, not billing data,
remaining-context calculations, or independently measured performance claims.

## Attach Text And Screenshot Context

The text workspace can attach up to five explicitly selected UTF-8 `.txt`,
`.md`, `.csv`, or `.json` files. Each file is limited to 64 KiB and the
combined selection to 128 KiB. CSV and JSON are syntax- and resource-checked
in both browser and engine; JSON is never evaluated and CSV formulas are never
executed. The browser shows normalized filenames, format-aware inert previews,
sizes, approximate token costs, removal, and clear-all controls. It never sends
a filesystem path, scans a directory, watches files, or creates a persistent
library.

A single keyboard-operable browser control accepts only `.txt`, `.md`, `.csv`,
`.json`, source-text `.cs`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`,
`.go`, `.rs`, `.sql`, `.tf`, and `.png`; a PNG screenshot can also be pasted
from the clipboard. Source files are normalized to inert `text/plain`, receive
no syntax-validation claim, and are never executed. Shell, PowerShell, batch,
binary, project, archive, and configuration formats remain blocked.
The selection is atomic, so one rejected file leaves the previous selection unchanged. A
screenshot copied to the Windows clipboard or through a real Ubuntu desktop
clipboard session can be pasted directly into the page; both native cells
entered through the admitted PNG path. Physical macOS clipboard behavior
remains unverified. The initial image boundary accepts PNG items only. Each task defaults to
two screenshots and offers an advanced one-through-four choice. The engine
retains an absolute four-image cap, 4 MiB per image, 8 MiB combined, 4096
pixels per dimension, 16.7 million pixels per image, and 33.5 million combined
decoded pixels. The browser shows a memory-only
thumbnail; the engine independently verifies base64, PNG signature and chunk
structure, CRCs, exact size, dimensions, and pixel budget before adding
canonical image data to the Ollama chat message. Broader image file upload and
JPEG, WebP, GIF, SVG, PDF, OCR, or image conversion are not admitted.

The loopback service independently validates the complete attachment shape,
extension/media-type match, UTF-8 content, exact byte count, duplicate names,
per-file budget, and total budget. Filenames and browser MIME values are
untrusted hints: byte preflight and server revalidation reject known
binary/container signatures, forbidden control bytes, and high-confidence
PowerShell, shell, or batch files renamed to an allowed extension. Correctly
named admitted-language shebangs and ambiguous prose remain inert data. This is
not a perfect language classifier or antivirus claim. The service labels
selected text as untrusted
reference material before adding it to the bounded provider request. File
content cannot select a tool, command, path, provider, model, approval, or
network destination. The same untrusted-data instruction covers image content,
including visible or encoded prompt injection. The runtime exposes no
attachment-driven tool, shell, process, filesystem-write, archive-expansion,
or model-output execution path. This is execution prevention, not an antivirus
claim; attached data may still contain hostile text, but Haven 42 never runs
it. A private-network Ollama connection shows a prominent warning that the
selected contents will leave the current machine. Deliberate Send after that
warning confirms the transfer without a separate checkbox. Public provider
destinations remain blocked.

Ollama's chat contract supports an optional base64 `images` list on a user
message for multimodal models. Haven 42 uses that fixed field, but no installed
model currently has admitted image-input evidence. The UI therefore warns that
screenshot understanding is unverified for the selected model and that the
request may fail; successful transport does not promote a model as vision
capable.

Selection and extracted text remain in browser/process memory. New task,
capability, model, or provider changes and process shutdown clear the selection.
No temporary file, browser storage, server-side upload, or log is created.
Directories, archives, PDF, Office files, source trees, OCR, active lexical
retrieval, embeddings, vision-model promotion, and persistent indexes remain
outside this admission. A restricted parser-worker contract and hostile
metadata suite now reject unsafe PDF/Office candidate shapes but admit no
parser dependency, worker, route, path, filesystem access, or temporary file.
The deterministic memory-only lexical core is
implemented and hostile-tested offline, including strict budgets, stable
ranking, source/chunk disclosure, removal, and failure cleanup. It has no
runtime route, UI control, provider payload, path access, parser, network
operation, embedding, temporary file, or persistent index.

Chat now includes three manual research choices. A person can review and approve
one exact English Wikipedia metadata search, inspect inactive source
destinations, and separately approve reading one selected page as inert text.
The engine owns that fixed destination, DNS revalidation, pinned TLS connection,
response limits, citation identity, and memory cleanup. A wider-web choice
accepts a session-only Brave Search API key, retrieves at most five public HTTPS
pages under the same SSRF and resource boundary, and asks the selected local
Ollama model for a strict citation-bound answer after one explicit review. A
separate browser fallback prepares an exact Brave Search destination and opens
it only after review; Haven 42 does not ingest those browser results. Models
cannot invoke or approve research, choose URLs, navigate, download, persist
results, receive the key, or trigger follow-up searches. See
`docs/controlled-web-research-foundation.md` for the exact boundary and open
package and assistive-technology gates.

Conversation history is inactive as well. Its default-deny contract,
non-executable logical SQLite-compatible schema, pure planners, and hostile
fixtures do not import SQLite, open or create a database, write a file, use
browser storage, expose a route or UI control, or persist a message. Private
session remains the write-free default. See
`docs/conversation-history-database.md` and
`docs/conversation-history-encryption-review.md`.

## Registered software plans

The Software view reads `config/workflows.json` through the engine. Only unique
`uiReady` workflows whose registry safety level is exactly `read-only` are
visible. The current admitted mode is plan-only: renderer arguments, arbitrary
commands, child processes, repository reads, writes, and workflow network calls
are all denied. The result is a typed planned `engineering-report` with ordered
accepted/warning/result events.

## Promoted image flow

The Images view admits only `comfyui.local-image` using the promoted Linux
ComfyUI/SDXL profile and exact `sd_xl_base_1.0.safetensors` checkpoint. The
endpoint must be an IPv4 loopback literal, normally an explicitly managed SSH
tunnel. Checkpoint discovery precedes admission; the renderer cannot choose a
model, custom node, external API node, filename, provider path, or workflow
graph.

Generation uses fixed bounded dimensions, steps, CFG, sampler, negative prompt,
and a built-in node graph. The server reuses the attachment PNG parser to verify
the complete chunk sequence, CRCs, terminal IEND, absence of trailing bytes, and
bounded dimensions before accepting provider output, then clears ComfyUI
API history, and returns the image in browser memory. No client file is written
until the user activates the browser download. ComfyUI retains its provider-side
output, and the UI discloses that material effect before execution.

## Chat-First Layout

The conversation workspace is the primary desktop interaction. The left navigation stays pinned below the local header, the headline is deliberately compact, and provider plus sanitized system configuration remain in a bounded sticky column on the right. On narrower windows the page collapses to one column with chat first and setup available through the Models or System navigation controls.

Chat, Software, Images, Models, and About are mutually exclusive primary
panels, preventing hidden content from overlapping or clipping the active view.
Chat is one continuous conversation rather than separate Chat, Writing, and
Summarization tabs. Models opens a dedicated workspace with a
Chat/Writing/Summarization evidence selector,
installed models visible by default, and candidate search beside selection.
Results label whether a model is already installed on the connected Ollama
server. Changing the target capability clears the query, online candidates, and
desired candidate before ranking installed options for the new capability.
About reports the version, admitted provider boundaries, memory-only privacy,
and unsigned development status without adding network or execution behavior.

This layout change does not broaden browser authority: configuration, messages, and responses remain in memory, and the browser still has no shell, filesystem, repository, model-download, or arbitrary-network surface.

The Chat header includes session-only **A−** and **A+** controls that step
through Small, Default, Large, and Extra large text. Accessible labels announce
their purpose, the current scale is shown between them, and the unavailable
direction is disabled at each bound. The composer footer keeps the bounded
20/50/100 prompt-recall choice beside the Up/Down hint where that behavior is
used. Both controls are browser-memory-only. They do not alter navigation,
provider payloads, stored data, model context, or any engine decision, and
return to their defaults when Haven 42 closes.

## Connect Ollama

For Ollama on the same computer, keep the default loopback endpoint. For an Ollama server on your trusted home or work network, enter its literal private IP endpoint, such as `http://<trusted-lan-ip>:11434`, and select **Connect**. Haven 42 classifies loopback versus private-LAN scope on the server; users do not need to select a connection scope.

After discovery, Haven 42 remembers separate in-memory automatic or advanced manual model guidance for Chat, Writing, and Summarization. The visible conversation model remains active across task intents. If an explicit write/draft/compose or summarize/condense request has a different configured installed model, a browser-memory-only prompt appears before submission. The user can switch or keep the current model; no request or automatic switch occurs while the prompt is open. **Use automatic** returns an override to the engine recommendation. No selection is persisted after Haven 42 closes.

Hostnames, credentials in URLs, paths, query strings, redirects, link-local addresses, public addresses under the trusted-LAN scope, and unsafe address classes are rejected. Advanced settings optionally admit a fixed Bearer or X-API-Key header. Keys are bounded, memory-only, cleared from the visible field after connection, omitted from every response, and require HTTPS outside same-machine loopback. Connection settings and authentication are lost when Haven 42 closes.

## Chat, Writing, Summarization, And Model Cleanup

Use the single Chat composer for all admitted text tasks:

- Ordinary questions use `general.chat`.
- Explicit write, draft, compose, or rewrite requests use the bounded `content.write` prompt and return a Markdown-document response inside the same conversation.
- Explicit summarize, summarise, condense, summary, or TL;DR requests use `content.summarize`; its system instruction permits only source-grounded summarization and requires uncertainty to be preserved.
- Chat, Writing, and Summarization do not infer gender, pronouns, titles, or
  relationships from a name or appearance alone. They preserve pronouns stated
  by the user or supplied source exactly. They never replace an explicit
  individual pronoun with singular they/them. When no pronoun is supplied, they
  use the person's name or a neutral noun such as `the person` or `the author`
  and do not assign or request a gender merely to word the response.
- The same compact response policy rejects unsupported sensitive-trait
  inference and stereotypes, distinguishes supplied information from
  assumptions, preserves source uncertainty, forbids invented browsing/file/
  execution claims, avoids repeating secrets, treats high-stakes guidance as
  uncertain rather than professional determination, and places effect and
  verification guidance before destructive or system-changing commands. These
  are model-behavior instructions, not security authorization; the server's
  deterministic route, filesystem, process, network, and approval controls
  remain the security boundary.

All three paths retain the same bounded conversation in browser memory. The
local intent hint is advisory routing among already admitted text capabilities;
it cannot grant tools, filesystem access, repository access, model downloads,
or network authority.

Press Enter to submit a text task. Use Shift+Enter for a new line. Input-method
composition is not submitted until composition has ended.

Chat, Models, System, Technical details, and About each provide an independent
three-to-six-step help tour. A tour opens automatically only on the first visit
to its own section, never navigates between sections, and can always be opened
again from that section's **Help** button. Every step provides Back, Next, Skip,
close, and Escape behavior; focus stays in the tour dialog and returns to the
section when the tour closes. Skip, close, and completion all mark that section
as seen instead of saving a resume position.

The only persistent tour state is the fixed-key
`haven42.section-tours.v1` browser preference with one positive integer tour
revision for each known
section. It contains no conversation, attachment, model, provider, system, or
identity data. Invalid or unavailable browser storage is ignored and cannot
block the application.

Up and Down recall older and newer submitted prompts when the caret is on the
first or last textarea line respectively, so ordinary multiline cursor movement
is preserved. Entering history retains the unfinished draft and moving past the
newest entry restores it. Consecutive duplicates are stored once. System offers
20 (default), 50, or 100 entries; the setting and prompt text remain in browser
memory, and the list clears on New task, a direct model/provider change, or shutdown.

Only selecting **New task**, applying a changed provider configuration, or closing Haven 42 clears the visible in-memory conversation. Changing from a question to writing or summarization does not. These capabilities use the registered `ollama.local-text` provider. They do not read a repository, write files, download models, or persist the endpoint, input, conversation, or response.

The balanced default sends a bounded five-minute `keep_alive`, avoiding a costly reload between nearby prompts. Advanced connection settings and the System panel offer immediate cleanup, 5 minutes, 15 minutes, or 30 minutes. Haven 42 keeps at most one model active for its browser session: choosing a different model unloads and verifies the previous one before invoking the next. **New task**, provider changes, request failures, the idle timer, and application shutdown also trigger explicit unload and process-list verification.

## Security Boundary

The MVP:

- binds only to IPv4 loopback (`127.0.0.1`);
- rejects unexpected `Host`, `Origin`, and cross-site request metadata;
- requires an unpredictable in-memory token on every state-changing request;
- accepts JSON only and bounds request, message, conversation, timeout, and response sizes;
- serves only committed local HTML, CSS, and JavaScript;
- sends a restrictive Content Security Policy and denies framing, MIME sniffing, referrer leakage, caching, remote assets, and telemetry;
- uses the shared provider-security module for endpoint classification, no-redirect requests, and bounded JSON;
- sends only the selected fixed Bearer or X-API-Key header, requires HTTPS for authenticated private-network traffic, and never persists or returns the key;
- limits public catalog discovery to an explicit bounded query, fixed Ollama HTTPS origin, no redirects, capped HTML, strict names, and candidate-only results;
- returns sanitized error codes instead of provider responses or local exception details.

The renderer never receives a shell, executable, arbitrary process, filesystem, model-download, installation, elevation, or repository-access surface. Readiness scanning is a CSRF-protected POST because even read-only subprocess work consumes local resources.

Text responses include a schema-v1 typed artifact and ordered accepted/progress/warning/result events. Browser JavaScript validates the capability, artifact type, source capability, terminal status, strict event shape, contiguous sequence, exactly one terminal event, and absence of post-terminal events before rendering content. Assistant chat and Markdown-document text render headings, paragraphs, ordered and unordered lists, bold, italics, inline and fenced code, quotes, rules, and Unicode emoji through a small dependency-free allowlist. The renderer uses `createElement` and `textContent`, never model-supplied HTML; raw tags remain visible inert text and cannot create links, images, scripts, or event handlers. An advanced manual model without exact evidence for the selected capability adds a visible warning without granting that model more authority.

Text failures return a typed error envelope and an explicit recovery declaration. Haven 42 never retries automatically. When safe browser-memory restoration is declared, the failed input is restored to the composer, removed from chat history, and can be edited or submitted as a new request. Nothing is persisted and no approval or request identity is reused. Broader dispatcher workflow rendering remains future integration work.

The machine-readable boundaries are `config/local-web-runtime-policy.json`, `config/system-readiness-contract.json`, `config/setup-plan-contract.json`, and `config/installation-broker-contract.json`. The strict component inventory is `config/install-component-registry.json`, and the evidence-gated text recommendation input is `config/text-capability-model-recommendations.json`. Offline security coverage lives in `scripts/test-system-readiness.py` and `scripts/test-haven42-web.py`; the dependency-free real-browser wizard/chat flow is `scripts/test-haven42-web-browser.mjs`.

## Current Runtime Boundary

The admitted application includes explicit read-only system scanning, zero-effect setup planning, system status, read-only capability/health/evidence views, Ollama connection, installed-model selection, candidate-only public catalog search, chat, writing, summarization, and unsigned one-folder development packaging. Software installation, drivers, services, model downloads, software workflows, images, model management, persistence, multi-user access, remote browser access, automatic updates, signed/notarized distribution, installers, and production release publication remain unavailable until their separate runtime and security gates pass.

Tauri/Rust remains unadmitted. The shared browser UI and minimum trusted
PyInstaller launcher/service are the active cross-platform development
packaging path.

## Validation Evidence

The sanitized Windows application-host and trusted-LAN Ollama validation cell is recorded in `examples/local-web-mvp-validation.md`. It covers page rendering, secure session bootstrap, discovery, model selection, all three bounded text modes, response-content exclusion, application unload, and an independently empty Ollama process list.
