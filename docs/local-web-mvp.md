# Local Web MVP

Haven 42 has a runnable local product experience for Windows, Linux, and macOS. It opens a local browser page, reports sanitized host readiness, connects to an explicitly selected Ollama endpoint, discovers installed models, and provides repository-free chat, writing, and summarization.

This is a local application, not a hosted website. It does not require Node.js, Rust, Tauri, a cloud account, executable signing, or a public deployment.

## First-Run Wizard

Each launch begins with a memory-only wizard that first offers:

- **Guided setup:** explicitly scan a registered, bounded, read-only set of local facts, review a zero-effect setup plan, then connect Ollama;
- **Connect existing setup:** skip the local scan and enter a user-managed loopback or private-network Ollama IP address;
- **Explore Haven 42:** open the interface without scanning or connecting a provider.

The Guided path reports operating system, architecture, logical processors, system memory, available storage, sanitized accelerator facts, and registered software presence/version. It does not query the Ollama daemon or discover installed models because readiness scanning is network-free; model discovery begins only after the user explicitly connects a policy-approved provider endpoint. The scan does not return hostname, username, hardware serials, device IDs, private paths, environment variables, credentials, process command lines, or network addresses. Probes use fixed engine-owned executable/argument pairs without a shell, network access, writes, installation, elevation, service changes, or driver changes.

The resulting plan is bound to the exact current in-memory snapshot. Browser code cannot submit hardware evidence, component IDs outside the strict registry, commands, URLs, paths, arguments, environment, or approval decisions. Every plan action says that installation is disabled. The separate installation broker is simulation-only and is not exposed by the web runtime.

The wizard is intentionally not marked complete on disk because the endpoint, readiness snapshot, and setup state are not persisted. A fresh launch therefore cannot silently reconnect to a previously entered server or reuse stale hardware facts.

The engine, not browser JavaScript, owns the recommendation catalog. An installed model name with matching passed capability evidence is `recommended` and can be selected automatically. This first slice does not claim immutable-digest binding; that remains an explicit promotion task. A model evidenced for another text capability is `compatible`, an unknown installed model is `unverified`, and an evidence-backed candidate that is not installed is `missing`. Compatible and unverified models remain explicit advanced choices and gain no filesystem, repository, tool, network, or download authority.

If the recommended model is missing, the wizard names it but disables completion. Haven 42 does not issue an Ollama pull. The user installs a disclosed model separately and checks the connection again.

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

The launcher opens `http://127.0.0.1:4242`. Use `-NoOpen` on Windows or `--no-open` on Linux and macOS to start without opening the default browser. Use `-Port` or `--port` to select another loopback port. Every launcher probes candidate commands and accepts only a working Python 3 interpreter; a stale Windows `py` command or store alias is skipped rather than failing later with a misleading server error.

## Accessibility And Capability Status

The wizard is a labeled modal with an announced description and current-step state. Keyboard focus enters the wizard after secure-session bootstrap, moves to the active step, and remains trapped among visible controls until setup finishes. A skip link, visible focus styles, semantic status/alert regions, responsive layout, sufficient status contrast, and reduced-motion behavior support keyboard and assistive-technology use.

The capability view is read-only and engine-derived. Chat, Writing, and Summarization change from `configuration-required` to `available` only after a successful provider check. Software stays `not-admitted-in-web`; Images stays `provider-profile-required`. Clicking either unavailable navigation item explains its state and never invokes an operation.

The System view can repeat the explicit read-only readiness scan. It also reports sanitized provider health, catalog evidence matching, the current lack of immutable artifact-digest binding, and a disabled/no-network update state. These labels disclose evidence boundaries; they do not promote a provider, model, or capability.

## Chat-First Layout

The conversation workspace is the primary desktop interaction. The left navigation stays pinned below the local header, the headline is deliberately compact, and provider plus sanitized system configuration remain in a bounded sticky column on the right. On narrower windows the page collapses to one column with chat first and setup available through the Models or System navigation controls.

This layout change does not broaden browser authority: configuration, messages, and responses remain in memory, and the browser still has no shell, filesystem, repository, model-download, or arbitrary-network surface.

## Connect Ollama

For Ollama on the same computer, keep the default loopback endpoint. For an Ollama server on your trusted home or work network, enter its literal private IP endpoint, such as `http://<trusted-lan-ip>:11434`, and select **Connect**. Haven 42 classifies loopback versus private-LAN scope on the server; users do not need to select a connection scope.

After discovery, Haven 42 remembers a separate in-memory automatic or advanced manual model choice for Chat, Writing, and Summarization. Changing a capability restores its last selection, and **Use automatic** returns an override to the engine recommendation. No selection is persisted after Haven 42 closes.

Hostnames, credentials in URLs, paths, query strings, redirects, link-local addresses, public addresses under the trusted-LAN scope, and unsafe address classes are rejected. Connection settings remain in memory and are lost when Haven 42 closes.

## Chat, Writing, Summarization, And Model Cleanup

Use the task selector above the input area or the left navigation:

- **Chat** uses `general.chat` and keeps up to 20 bounded messages in browser memory for follow-up questions.
- **Write** uses `content.write` and sends one bounded writing request. It returns a Markdown-document result in the page.
- **Summarize** uses `content.summarize` and sends one bounded source input. Its system instruction permits only source-grounded summarization and requires uncertainty to be preserved.

Changing modes or selecting **New task** clears the visible in-memory task. These capabilities use the registered `ollama.local-text` provider. They do not read a repository, write files, download models, or persist the endpoint, input, conversation, or response.

The balanced default sends a bounded five-minute `keep_alive`, avoiding a costly reload between nearby prompts. Advanced connection settings offer immediate cleanup, 15 minutes, or 30 minutes. Haven 42 keeps at most one model active for its browser session: choosing a different model unloads and verifies the previous one before invoking the next. **New task**, provider changes, request failures, the idle timer, and application shutdown also trigger explicit unload and process-list verification.

## Security Boundary

The MVP:

- binds only to IPv4 loopback (`127.0.0.1`);
- rejects unexpected `Host`, `Origin`, and cross-site request metadata;
- requires an unpredictable in-memory token on every state-changing request;
- accepts JSON only and bounds request, message, conversation, timeout, and response sizes;
- serves only committed local HTML, CSS, and JavaScript;
- sends a restrictive Content Security Policy and denies framing, MIME sniffing, referrer leakage, caching, remote assets, and telemetry;
- uses the shared provider-security module for endpoint classification, no-redirect requests, and bounded JSON;
- returns sanitized error codes instead of provider responses or local exception details.

The renderer never receives a shell, executable, arbitrary process, filesystem, model-download, installation, elevation, or repository-access surface. Readiness scanning is a CSRF-protected POST because even read-only subprocess work consumes local resources.

Text responses include a schema-v1 typed artifact and ordered accepted/result events. Browser JavaScript validates the capability, artifact type, source capability, terminal status, and event sequence before rendering content. The UI reports typed progress/result/error state and explicitly says that no file was written. Workflow warning/retry/recovery envelopes remain future integration work.

The machine-readable boundaries are `config/local-web-runtime-policy.json`, `config/system-readiness-contract.json`, `config/setup-plan-contract.json`, and `config/installation-broker-contract.json`. The strict component inventory is `config/install-component-registry.json`, and the evidence-gated text recommendation input is `config/text-capability-model-recommendations.json`. Offline security coverage lives in `scripts/test-system-readiness.py` and `scripts/test-haven42-web.py`; the dependency-free real-browser wizard/chat flow is `scripts/test-haven42-web-browser.mjs`.

## Current Runtime Boundary

The admitted application includes explicit read-only system scanning, zero-effect setup planning, system status, read-only capability/health/evidence views, Ollama connection, installed-model selection, chat, writing, and summarization. Software installation, drivers, services, model downloads, software workflows, images, model management, persistence, multi-user access, remote browser access, automatic updates, and native packaging remain unavailable until their separate runtime and security gates pass.

Tauri remains an optional later packaging path. It is not required to run or validate this local-web slice.

## Validation Evidence

The sanitized Windows application-host and trusted-LAN Ollama validation cell is recorded in `examples/local-web-mvp-validation.md`. It covers page rendering, secure session bootstrap, discovery, model selection, all three bounded text modes, response-content exclusion, application unload, and an independently empty Ollama process list.
