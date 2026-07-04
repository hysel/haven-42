# Local Agent Model Testing

## Purpose

Use these scripts to automate the repetitive part of local model validation before
testing Continue Agent mode in the editor.

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
  -Models "qwen3.5:9b","devstral-small-2:24b","qwen3-coder:30b"
```

Linux:

```bash
./scripts/pull-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --models "qwen3.5:9b,devstral-small-2:24b,qwen3-coder:30b"
```

macOS:

```bash
./scripts/pull-local-agent-models.macos.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --models "qwen3.5:9b,devstral-small-2:24b,qwen3-coder:30b"
```

Use your own Ollama base URL when the server runs on another machine. Do not
commit private IP addresses or local-only endpoints.

## Test Candidate Models

Windows:

```powershell
.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "qwen3.5:9b","devstral-small-2:24b","qwen3-coder:30b" `
  -UnloadAfterEach
```

Linux:

```bash
./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b,devstral-small-2:24b,qwen3-coder:30b" \
  --unload-after-each
```

macOS:

```bash
./scripts/test-local-agent-models.macos.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b,devstral-small-2:24b,qwen3-coder:30b" \
  --unload-after-each
```

Add `-PullMissing` on Windows, or `--pull-missing` on Linux/macOS, when you want
the test runner to pull missing models before testing.

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
