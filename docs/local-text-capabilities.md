# Local Text Capabilities

The live-validated `ollama.local-text` adapter supports repository-free chat, writing, and summarization through an explicit local Ollama model. It remains runtime configuration-dependent: one validated environment does not prove that every endpoint, model, operating system, or prompt will work. Sanitized evidence is recorded in `examples/local-text-capability-validation.md`.

Create a matching session first with `scripts/start-ai-session.*`. Then preview the provider plan without network or file writes:

```powershell
.\scripts\invoke-local-text-capability.ps1 `
  -CapabilityId general.chat `
  -Prompt "Explain dependency injection simply." `
  -Model "your-installed-model" `
  -SessionPath "C:\local-ai-sessions\chat-session" `
  -AsJson
```

Add `-Execute` to contact the runtime-only Ollama endpoint. Add `-Apply` only when the disclosed JSON artifact path is correct and should be written. Linux and macOS use `scripts/invoke-local-text-capability.linux.sh` or `.macos.sh` with `--capability-id`, `--prompt`, `--model`, `--session-path`, `--execute`, `--apply`, and `--json`.

## Safety Contract

- Dry-run is the default and performs no network call.
- `Execute` is required before contacting Ollama.
- `Apply` requires `Execute` and is required before writing an artifact.
- The session must exist outside the pack repository and match the requested capability.
- The exact artifact path is returned before execution and cannot escape `artifacts/`.
- Existing artifacts are never overwritten.
- The prompt and endpoint are not stored in `session.json` or artifact metadata.
- Provider output is stored only in the explicitly approved local artifact.
- Repository content is not read by these general-purpose capabilities.
- The adapter does not pull models. The requested model must already be installed.

`-ResponseFixturePath` and `--response-fixture-path` exist only for deterministic adapter contract tests. Fixture success is not live-provider evidence.

## Promotion Boundary

Live validation must record only sanitized provider ID, model ID, operating system, capability, nonempty-output result, artifact validation, and failure signals. Never record the endpoint, prompt contents, local session path, or raw response. Writing and summarization quality should be evaluated separately from basic transport and artifact correctness.
