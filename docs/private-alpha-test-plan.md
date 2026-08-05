# Private alpha test plan

This runbook is for the invited, unsigned `0.4.0-alpha.1` Windows candidate.
It does not activate distribution. Guided setup effects require a separate
explicit tester choice in the application.

The engineering baseline and its limited hardware scope are recorded in
`docs/windows-alpha-native-validation.md`. Tester results remain independent
evidence and must not silently inherit that machine's outcome.

## Before testing

1. Confirm the artifact came through the owner-approved private channel.
2. Verify its filename, size, and SHA-256 against the candidate packet.
3. Confirm the target operating system and architecture are explicitly listed.
4. Read `docs/private-alpha-known-limitations.md`.
5. Use only disposable prompts and attachments with no credentials, customer
   data, private source, or regulated information.
6. Do not bypass operating-system security controls or certificate checks.

## Core smoke sequence

Record pass, fail, or not applicable without recording private content:

1. Extract the archive into a new user-owned directory without elevation.
2. Launch Haven 42 and confirm only an IPv4 loopback URL is shown or opened.
3. Complete first-run navigation with no provider configured.
4. Test either **Connect existing setup** or the guided local setup. Before the
   guided path, confirm the screen discloses downloads and current-user files
   and explicitly forbids driver, service, firewall, certificate, update, and
   elevation changes.
5. Confirm authenticated private-network HTTP is rejected and HTTPS
   certificate verification remains enabled.
6. Run disposable Chat, Write, and Summarize requests in the unified text
   workspace. Confirm automatic routing and each explicit task option,
   Enter/Shift+Enter behavior, readable formatting, per-response tokens/second,
   token totals, prompt recall, and New task behavior.
7. Attach one admitted synthetic text/source file and one synthetic PNG;
   confirm preview, removal, limits, warning, and memory-only cleanup.
8. Confirm Chat, Writing, and Summarization are exposed while Images and
   Software remain hidden. Confirm a crafted non-text API request is rejected.
   Review Models, System, Evidence, and About without enabling unavailable
   capabilities.
9. Confirm CPU, RAM, GPU/VRAM when available, per-run tokens, and session-token
   totals update without telemetry; **New task** resets session totals.
10. Change the model idle-unload policy and confirm the model unloads or is
   explicitly cleaned up before shutdown.
11. Close Haven 42, confirm both Haven and any Haven-owned Ollama process and
    loopback ports exit, then relaunch.
12. If guided setup was used, record whether retry/relaunch recognized the
    versioned portable runtime and model without redownloading it, skipped the
    connection step, and opened the text workspace with the managed loopback
    provider connected. Confirm the readiness view names Windows 10 or Windows
    11, its build and architecture, and available component/driver versions.
    Candidate cleanup instructions must identify the portable Alpha data directory.

Maintainers collecting a new hardware-tier cell must bind the expected result
instead of accepting whichever model happened to be selected:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts/run-windows-alpha-native-validation.ps1 `
  -Executable <path-to-haven42.exe> `
  -Mode Managed `
  -ExpectedModelId <catalog-model-id> `
  -ExpectedBackendMode <cpu|cuda|rocm|vulkan>
```

The harness fails before managed approval when either expectation differs and
reports the conservative required free-storage amount without retaining a
hostname, address, username, local path, prompt, or response.

For a machine intentionally below the target-volume storage threshold, use
`-Mode StorageDenied`. The harness requires no model or managed plan, an
explicit `storage-threshold` blocker, an idle setup broker, unchanged managed
state existence, clean shutdown, and no user-content persistence.

## Failure rules

Stop testing and report immediately if Haven listens beyond loopback, reveals
an API key, writes prompts or attachments unexpectedly, launches an arbitrary
process, bypasses TLS verification, cannot unload a model, cannot shut down,
or modifies system configuration. Do not attach sensitive logs or screenshots.

Security vulnerabilities must use GitHub private vulnerability reporting, not
a public issue. Other reports should use the exact owner-selected alpha
feedback channel and the sanitized template.
