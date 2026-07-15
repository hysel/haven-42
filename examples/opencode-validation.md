# OpenCode Validation Evidence

This page records sanitized OpenCode CLI validation evidence. It excludes
private endpoints, local paths, usernames, prompts, raw output, and source
code.

## Evidence: 2026-07-15 Generated Python Sample

- Surface: OpenCode CLI 1.18.2
- Operating system: Windows
- Provider: Ollama
- Target: generated disposable Python sample
- Model unload after each run: passed

| Model | Read-only validation | Disposable write smoke | Decision |
| --- | --- | --- | --- |
| devstral-small-2:24b | passed | passed | Generated-sample scoped-edit validated for OpenCode only; real-project approval remains blocked. |
| qwen3.5:9b | passed | failed | The model read the sample but its exact-string edit failed. Keep it read-only only for this surface. |
| qwen3.5:35b | failed strict filename contract | passed | The expected isolated README-only write passed external Git and file verification, but the read contract did not pass. Keep it scoped to disposable write evidence. |

No result approves real-project writes. Devstral Small 2 24B has passed
generated-sample read-only, write-smoke, and constrained scoped-edit contracts
for OpenCode. Explicitly approved non-generated repository validation is still
required before any real-project promotion.
