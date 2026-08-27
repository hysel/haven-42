# Continue CLI Model Validation Evidence

> **Historical evidence only:** Continue is a legacy surface in Haven 42. These results preserve what was measured; they do not make Continue a current, supported, or recommended coding surface.

This file records sanitized Continue CLI model validation results. It intentionally omits private endpoints, local paths, usernames, raw transcripts, and repository-specific details.

## Summary

- Date: 2026-07-09
- Surface: Continue CLI
- Provider: Ollama-compatible local endpoint
- Target: generated disposable Python sample repository
- Operating system: Windows
- Test mode: read-only repository inspection plus approved-write smoke test
- Config source: generated runtime config derived from the pack template
- Private details removed: Yes

## Results

| Model | Read-only CLI validation | Approved-write smoke validation | Decision |
| --- | --- | --- | --- |
| `qwen3.5:9b` | Pass | Pass | Approved-write ready for one scoped disposable edit at a time. |
| `qwen3-coder:30b` | Pass | Pass | Approved-write ready for one scoped disposable edit at a time; may be slower on modest hardware. |
| `devstral-small-2:24b` | Pass | Pass | Approved-write ready for one scoped disposable edit at a time; keep editor-surface validation separate. |

## Validation Behavior

The harness verified that each model could:

- Inspect a generated repository and reference real files from the sample.
- Avoid modifying files during the read-only phase.
- Modify only `README.md` during the write-smoke phase.
- Add the exact expected final line.
- Restore the disposable sample after validation.

The harness also initializes a standalone Git baseline inside generated sample repositories so validation does not accidentally read the parent pack repository state.

## Decision

These models qualified as Continue CLI candidates for the historical tool-backed workflow that was tested. The result does not transfer to maintained coding surfaces, editor extensions, real-project edits, or future model builds.

## Remaining Risks

- Real project edits still require scoped prompts, external `git status`, and review before commit.
- Editor extensions may behave differently from the CLI and need separate read/write validation.
- Local hardware, context length, and model quantization can affect speed and reliability.
