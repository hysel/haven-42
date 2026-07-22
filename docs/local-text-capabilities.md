# Local Text Capabilities

One provider-neutral adapter supports repository-free chat, writing, and summarization. `ollama.local-text` uses Ollama's chat API and is live-validated. `llamacpp.local-text` uses the OpenAI-compatible chat-completions API and is live-validated for the exact Linux NVIDIA/CUDA profile admitted by `config/inference-engine-registry.json`. Its direct pinned-server run passed discovery, profile admission, invocation, exact output, sanitization, and cleanup. Windows AMD/HIP retains engine-only evidence until its adapter is run directly, and every other profile fails closed.

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

For an already-running llama.cpp server on the validated Windows AMD/HIP profile:

```powershell
.\scripts\invoke-local-text-capability.ps1 `
  -CapabilityId general.chat -Prompt "Explain dependency injection simply." `
  -Model "your-loaded-model" -SessionPath "C:\local-ai-sessions\chat-session" `
  -ProviderId llamacpp.local-text -EngineId llama.cpp -BackendId hip `
  -HardwareProfile windows-x64-amd-rx7800xt-16gb -RuntimeBaseUrl "http://127.0.0.1:8080" -AsJson
```

The admitted Linux form uses `--provider-id llamacpp.local-text --engine-id llama.cpp --backend-id cuda --hardware-profile linux-x64-nvidia-rtx5000-16gb --runtime-base-url http://127.0.0.1:8080`. Dry-run remains the default. Haven 42 does not install, start, download, or silently fall back to CPU for either runtime.

## Safety Contract

- Dry-run is the default and performs no network call.
- `Execute` is required before contacting any runtime.
- `Apply` requires `Execute` and is required before writing an artifact.
- The session must exist outside the pack repository and match the requested capability.
- The exact artifact path is returned before execution and cannot escape `artifacts/`.
- Existing artifacts are never overwritten.
- The prompt and endpoint are not stored in `session.json` or artifact metadata.
- Provider output is stored only in the explicitly approved local artifact.
- Repository content is not read by these general-purpose capabilities.
- The adapter does not install runtimes, start servers, or pull models. The requested model must already be installed or loaded.
- OpenAI-compatible execution requires an exact admitted engine, backend, and hardware profile; parked or unknown combinations fail before network use.

`-ResponseFixturePath` and `--response-fixture-path` exist only for deterministic adapter contract tests. Fixture success is not live-provider evidence.

## Promotion Boundary

Live validation must record only sanitized provider ID, model ID, operating system, capability, nonempty-output result, artifact validation, and failure signals. Never record the endpoint, prompt contents, local session path, or raw response. Writing and summarization quality should be evaluated separately from basic transport and artifact correctness.
