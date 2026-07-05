# Local Agent Model Testing

## Purpose

Use these scripts to automate the repetitive part of local model validation before
testing Continue Agent mode in the editor.

These scripts test selected local model names. They do not discover newer
models online. If an online discovery helper is added later, it should only
suggest candidates; the model still has to pass this local preflight and the
editor Apply validation described below.

The scripts can:

- pull candidate Ollama models
- load a model before testing
- unload a model after testing
- check Ollama API tool-call behavior
- check exact-content output behavior
- write a sanitized JSON report

The scripts cannot click Continue's Apply button or prove that the editor
extension applied a patch. Automated preflight does not replace Continue UI Apply validation; that still requires a manual check in the editor and an external shell verification.

## Pull Candidate Models

Windows:

```powershell
.\scripts\pull-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -Models "qwen3.5:9b"
```

Linux:

```bash
./scripts/pull-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --models "qwen3.5:9b"
```

macOS:

```bash
./scripts/pull-local-agent-models.macos.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --models "qwen3.5:9b"
```

Use your own Ollama base URL when the server runs on another machine. Do not
commit private IP addresses or local-only endpoints.

## Test Candidate Models

Windows:

```powershell
.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "qwen3.5:9b" `
  -UnloadAfterEach
```

Linux:

```bash
./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b" \
  --unload-after-each
```

macOS:

```bash
./scripts/test-local-agent-models.macos.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b" \
  --unload-after-each
```

Add `-PullMissing` on Windows, or `--pull-missing` on Linux/macOS, when you want
the test runner to pull missing models before testing.

After the simple-hardware model passes, high-resource machines may explicitly
test optional profile upgrades such as `devstral-small-2:24b` for PLAN ONLY or
`qwen3-coder:30b` for DEEP REVIEW. Do not add those upgrades to shared config
until they pass local validation.

## Install A Validated Model Into Local Config

After a model passes validation, install it into one local-only profile. This
pulls the selected model unless `-NoPull` or `--no-pull` is used, and writes
only `.continue/config.local.yaml` in the target repository.

Windows:

```powershell
.\scripts\install-validated-model.ps1 `
  -TargetRepo "C:\path\to\your-project" `
  -Model "devstral-small-2:24b" `
  -Profile plan-only
```

Linux:

```bash
./scripts/install-validated-model.linux.sh \
  --target-repo "/path/to/your-project" \
  --model "devstral-small-2:24b" \
  --profile plan-only
```

macOS:

```bash
./scripts/install-validated-model.macos.sh \
  --target-repo "/path/to/your-project" \
  --model "devstral-small-2:24b" \
  --profile plan-only
```

Supported profiles are `write-safe`, `plan-only`, and `deep-review`. Use
`write-safe` only after approved-write validation passes in the intended editor.
Use `plan-only` or `deep-review` for heavier local models that should stay
chat-only.

## What The Test Means

The model is marked as an API-level candidate only when:

- Ollama can load the model.
- The model can return a structured `read_file` tool call for `README.md`.
- The model can return the exact requested file content without reasoning tags,
  markdown fences, raw tool-call text, or extra lines.

This is not the same as approved-write readiness in Continue. A model that passes
these API checks must still pass the editor Apply smoke test in
`docs/model-tool-use-validation.md`.

## Failure Signals

Common failure signals:

- `MODEL_NOT_INSTALLED`
- `MODEL_LOAD_FAILED`
- `MODEL_DOES_NOT_SUPPORT_TOOLS`
- `RAW_TOOL_CALL_OUTPUT`
- `TOOL_CALL_FAILED`
- `THINK_TAG_LEAK`
- `INCORRECT_EXACT_CONTENT`

If a model fails here, do not spend time testing approved writes in Continue
until you intentionally change model, prompt, or provider settings.

## Output

Reports are written to `runtime-validation-output/` by default. The report
redacts the Ollama URL and target repository path.

Do not commit reports that include private model names, private repositories,
local paths, endpoints, usernames, or raw private-code transcripts.
