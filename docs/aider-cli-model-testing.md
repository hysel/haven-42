# Aider CLI Model Testing

## Purpose

This is the Aider-specific wrapper around the shared CLI-surface harness in docs/agent-cli-surface-model-testing.md.

Use this workflow to test future local models through Aider CLI before asking Aider to touch a real project.

This is different from `scripts/test-local-agent-models.*`:

- `test-local-agent-models.*` checks raw Ollama API behavior.
- `test-aider-cli-models.*` checks whether Aider CLI can use a model through the Aider agent surface.
- Real-project Aider tests are still required before marking Aider approved-write behavior ready.

## Current Boundary

Aider CLI is useful for automated screening, but it does not prove realistic scoped-edit behavior in a real project.

Treat the result as surface-specific evidence:

```text
Aider CLI validation is CLI-specific and does not prove Continue, Cline, VS Code, or VSCodium behavior.
```

## Install Aider CLI

Aider is a Python-based CLI. The pack exposes the supported setup path through
one cross-platform adapter.

Windows PowerShell:

```powershell
.\scripts\setup-agent-surface.ps1 -Surface aider -Action Plan
.\scripts\setup-agent-surface.ps1 -Surface aider -Action Install -InstallMethod aider-install -DryRun
```

Linux or macOS:

```bash
./scripts/setup-agent-surface.linux.sh --surface aider --action Plan
./scripts/setup-agent-surface.linux.sh --surface aider --action Install --install-method aider-install --dry-run
```

Remove dry-run only after reviewing the network install plan. The adapter also
supports `pipx` and `uv`. A manual isolated install remains available:

```bash
pipx install aider-chat
```

Verify it:

Windows PowerShell:

```powershell
aider --version
```

## Generate Local-Only Ollama Config

The adapter writes `.aider.conf.local.yml` and requires launching Aider with
`--config .aider.conf.local.yml`. When Git metadata is available, it adds the
filename to the local repository's `.git/info/exclude`. Do not commit this file
while it contains a private endpoint.

Windows PowerShell:

```powershell
.\scripts\setup-agent-surface.ps1 `
  -Surface aider `
  -Action Configure `
  -TargetRepo C:/path/to/project `
  -Model qwen3.5:9b `
  -OllamaBaseUrl http://your-local-ollama-host:11434
```

Linux:

```bash
./scripts/setup-agent-surface.linux.sh \
  --surface aider \
  --action Configure \
  --target-repo /path/to/project \
  --model qwen3.5:9b \
  --ollama-base-url http://your-local-ollama-host:11434
```

Instead of a model, pass a hardware recommendation JSON plus the `WriteSafe`,
`PlanOnly`, or `DeepReview` lane. The config uses `ollama_chat/<model>`, sets
`OLLAMA_API_BASE`, and disables automatic and dirty commits. Run the adapter's
`Health` action after configuration.

Official references: [Aider installation](https://aider.chat/docs/install.html),
[Ollama setup](https://aider.chat/docs/llms/ollama.html), and
[YAML configuration](https://aider.chat/docs/config/aider_conf.html).

Linux or macOS:

```bash
aider --version
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

The default Aider CLI test target is:

```text
runtime-validation-output/sample-repositories/python-api
```

That folder is disposable and ignored by Git.

## Read-Only Model Screening

Windows PowerShell:

```powershell
.\scripts\test-aider-cli-models.ps1 `
  -Models "qwen3-coder:30b","qwen3.5:9b" `
  -TimeoutSeconds 600
```

Linux:

```bash
./scripts/test-aider-cli-models.linux.sh \
  --models "qwen3-coder:30b,qwen3.5:9b" \
  --timeout-seconds 600
```

macOS:

```bash
./scripts/test-aider-cli-models.macos.sh \
  --models "qwen3-coder:30b,qwen3.5:9b" \
  --timeout-seconds 600
```

The sanitized report is written under `runtime-validation-output/`.

## Write Smoke Test

Only run write smoke tests against generated disposable samples. The scripts initialize a standalone Git baseline so write validation is isolated from the pack repository.

Windows PowerShell:

```powershell
.\scripts\test-aider-cli-models.ps1 `
  -Models "qwen3-coder:30b" `
  -IncludeWriteSmoke `
  -TimeoutSeconds 600
```

Linux:

```bash
./scripts/test-aider-cli-models.linux.sh \
  --models "qwen3-coder:30b" \
  --include-write-smoke \
  --timeout-seconds 600
```

macOS:

```bash
./scripts/test-aider-cli-models.macos.sh \
  --models "qwen3-coder:30b" \
  --include-write-smoke \
  --timeout-seconds 600
```

The script verifies the write outside Aider with Git and direct file inspection, then restores the disposable README.

## CLI Argument Templates

Aider CLI flags may change over time. The scripts therefore support command-template placeholders instead of hardcoding every provider flag.

Default prompt invocation:

```text
--set-env OLLAMA_API_BASE={OllamaBaseUrl} --read README.md --read pyproject.toml --read app/main.py --read app/settings.py --read tests/test_main.py --message "{Prompt}" --yes-always --no-auto-commits --no-gitignore --map-tokens 0 --input-history-file "{TempDir}\aider-input-history.txt" --chat-history-file "{TempDir}\aider-chat-history.md" --no-check-update --analytics-disable --no-auto-lint --no-auto-test --line-endings lf
```

The default uses Aider read-only file context because Aider CLI is not a tool-calling repository inspector in the same sense as editor agents. The generated Python sample is the default target, so the default `--read` files are specific to that fixture.

Default write-smoke invocation:

```text
--set-env OLLAMA_API_BASE={OllamaBaseUrl} README.md --read pyproject.toml --read app/main.py --read app/settings.py --read tests/test_main.py --message "{Prompt}" --yes-always --no-auto-commits --no-gitignore --map-tokens 0 --input-history-file "{TempDir}\aider-input-history.txt" --chat-history-file "{TempDir}\aider-chat-history.md" --no-check-update --analytics-disable --no-auto-lint --no-auto-test --line-endings lf
```

The write-smoke template makes only `README.md` editable and keeps the supporting sample files read-only.

Useful placeholders:

| Placeholder | Meaning |
| --- | --- |
| `{Prompt}` | Compact one-line prompt text. |
| `{Model}` | Current model under test. |
| `{PromptFile}` | Temporary file containing the full prompt. |
| `{TargetRepo}` | Target repository path. |
| `{OllamaBaseUrl}` | Ollama base URL passed to the wrapper. |
| `{TempDir}` | Local temporary directory for history files. |

If your Aider CLI version supports a model flag, pass it explicitly.

Windows PowerShell example:

```powershell
.\scripts\test-aider-cli-models.ps1 `
  -Models "qwen3-coder:30b" `
  -ModelArgumentTemplate '--model "ollama_chat/{Model}"'
```

Linux or macOS example:

```bash
./scripts/test-aider-cli-models.linux.sh \
  --models "qwen3-coder:30b" \
  --model-argument-template '--model "ollama_chat/{Model}"'
```

The test harness passes the model explicitly. Normal day-to-day use should use
the generated local config with `aider --config .aider.conf.local.yml`.

## Dry Run

Use dry run to verify report writing and script plumbing without invoking Aider.

Windows PowerShell:

```powershell
.\scripts\test-aider-cli-models.ps1 -Models "qwen3-coder:30b" -DryRun
```

Linux or macOS:

```bash
./scripts/test-aider-cli-models.linux.sh --models "qwen3-coder:30b" --dry-run
```

Dry run is not evidence that a model works.

## Evidence Rules

Record only sanitized summaries in `examples/aider-validation.md` or a future dedicated Aider CLI evidence file.

Do not commit:

- raw Aider output
- local paths
- private endpoints
- usernames
- project names
- secrets or tokens

Promote evidence only after external verification passes.

## Recommended Flow

1. Run raw Ollama checks with `scripts/test-local-agent-models.*`.
2. Run Aider CLI read-only checks with `scripts/test-aider-cli-models.*`.
3. Run Aider CLI disposable write smoke checks for promising models.
4. Run a realistic Aider scoped-edit test in a disposable or explicitly approved repository.
5. Only then consider a model/surface pair for realistic scoped edits.
