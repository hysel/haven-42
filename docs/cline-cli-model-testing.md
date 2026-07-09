# Cline CLI Model Testing

## Purpose

Use this workflow to test future local models through Cline CLI before asking the editor extension to touch a real project.

This is different from `scripts/test-local-agent-models.*`:

- `test-local-agent-models.*` checks raw Ollama API behavior.
- `test-cline-cli-models.*` checks whether Cline CLI can use a model through the Cline agent surface.
- VS Code or VSCodium Cline extension tests are still required before marking editor approved-write behavior ready.

## Current Boundary

Cline CLI is useful for automated screening, but it does not prove the editor extension Apply UI, checkpoint behavior, approval prompts, or workspace detection.

Treat the result as surface-specific evidence:

```text
Cline CLI != Cline VS Code extension != Cline VSCodium extension
```

## Install Cline CLI

Cline currently documents CLI installation with npm:

```bash
npm i -g cline
```

Verify it:

Windows PowerShell:

```powershell
cline --version
```

Linux or macOS:

```bash
cline --version
```

## Generate Disposable Samples

Run this from the pack repository.

Windows PowerShell:

```powershell
.\scripts\generate-sample-repositories.ps1 -Force
```

Linux:

```bash
./scripts/generate-sample-repositories.linux.sh --force
```

macOS:

```bash
./scripts/generate-sample-repositories.macos.sh --force
```

The default Cline CLI test target is:

```text
runtime-validation-output/sample-repositories/python-api
```

That folder is disposable and ignored by Git.

## Read-Only Model Screening

Windows PowerShell:

```powershell
.\scripts\test-cline-cli-models.ps1 `
  -Models "qwen3-coder:30b","qwen3.5:9b" `
  -TimeoutSeconds 600
```

Linux:

```bash
./scripts/test-cline-cli-models.linux.sh \
  --models "qwen3-coder:30b,qwen3.5:9b" \
  --timeout-seconds 600
```

macOS:

```bash
./scripts/test-cline-cli-models.macos.sh \
  --models "qwen3-coder:30b,qwen3.5:9b" \
  --timeout-seconds 600
```

The sanitized report is written under `runtime-validation-output/`.

## Write Smoke Test

Only run write smoke tests against generated disposable samples.

Windows PowerShell:

```powershell
.\scripts\test-cline-cli-models.ps1 `
  -Models "qwen3-coder:30b" `
  -IncludeWriteSmoke `
  -TimeoutSeconds 600
```

Linux:

```bash
./scripts/test-cline-cli-models.linux.sh \
  --models "qwen3-coder:30b" \
  --include-write-smoke \
  --timeout-seconds 600
```

macOS:

```bash
./scripts/test-cline-cli-models.macos.sh \
  --models "qwen3-coder:30b" \
  --include-write-smoke \
  --timeout-seconds 600
```

The script verifies the write outside Cline with Git and direct file inspection, then restores the disposable README.

## CLI Argument Templates

Cline CLI flags may change over time. The scripts therefore support command-template placeholders instead of hardcoding every provider flag.

Default prompt invocation:

```text
--json "{Prompt}"
```

Useful placeholders:

| Placeholder | Meaning |
| --- | --- |
| `{Prompt}` | Compact one-line prompt text. |
| `{Model}` | Current model under test. |
| `{PromptFile}` | Temporary file containing the full prompt. |
| `{TargetRepo}` | Target repository path. |

If your Cline CLI version supports a model flag, pass it explicitly.

Windows PowerShell example:

```powershell
.\scripts\test-cline-cli-models.ps1 `
  -Models "qwen3-coder:30b" `
  -ModelArgumentTemplate '--model "{Model}"'
```

Linux or macOS example:

```bash
./scripts/test-cline-cli-models.linux.sh \
  --models "qwen3-coder:30b" \
  --model-argument-template '--model "{Model}"'
```

If your Cline CLI uses configuration profiles instead of a model flag, switch profiles outside the script and run one model at a time.

## Dry Run

Use dry run to verify report writing and script plumbing without invoking Cline.

Windows PowerShell:

```powershell
.\scripts\test-cline-cli-models.ps1 -Models "qwen3-coder:30b" -DryRun
```

Linux or macOS:

```bash
./scripts/test-cline-cli-models.linux.sh --models "qwen3-coder:30b" --dry-run
```

Dry run is not evidence that a model works.

## Evidence Rules

Record only sanitized summaries in `examples/cline-readonly-validation.md` or a future dedicated Cline CLI evidence file.

Do not commit:

- raw Cline output
- local paths
- private endpoints
- usernames
- project names
- secrets or tokens

Promote evidence only after external verification passes.

## Recommended Flow

1. Run raw Ollama checks with `scripts/test-local-agent-models.*`.
2. Run Cline CLI read-only checks with `scripts/test-cline-cli-models.*`.
3. Run Cline CLI disposable write smoke checks for promising models.
4. Run Cline editor extension read and write smoke tests.
5. Only then consider a model/surface pair for realistic scoped edits.
