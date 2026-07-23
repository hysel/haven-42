# Continue CLI Model Testing

## Purpose

Use these scripts when you want CLI-first evidence that a local model can work with the Continue command-line surface before you spend time testing the editor extension.

This is a focused model-screening harness. It does not replace the full runtime validation runner, and it does not prove that VS Code or VSCodium Apply behavior works. Editor Apply still needs separate manual validation because the editor approval flow can behave differently from the CLI.

## What This Tests

- Continue CLI can run against a generated disposable sample repository.
- A model can return useful read-only repository inspection output.
- Optional write smoke testing changes only `README.md` in a generated sample repository.
- The report is sanitized and omits raw prompts, raw model output, local paths, and private endpoints.

## Prerequisites

- Node.js with `npx` available, or another Continue CLI command you pass explicitly.
- A Continue config file that points at the model server you want to test.
- A generated disposable sample repository. The scripts create the default sample if it is missing and initialize a standalone Git baseline for external diff verification.

## Read-Only Screening

Windows:

```powershell
.\scripts\test-continue-cli-models.ps1 `
  -Models "qwen3.5:9b","qwen3-coder:30b" `
  -ConfigPath ".continue\config.yaml"
```

Linux:

```bash
./scripts/test-continue-cli-models.linux.sh \
  --models "qwen3.5:9b,qwen3-coder:30b" \
  --config-path .continue/config.yaml
```

macOS:

```bash
./scripts/test-continue-cli-models.macos.sh \
  --models "qwen3.5:9b,qwen3-coder:30b" \
  --config-path .continue/config.yaml
```

For a no-network, no-CLI dry run of the harness itself:

```powershell
.\scripts\test-continue-cli-models.ps1 -Models "qwen3.5:9b" -DryRun
```

## Write Smoke Test

Run write smoke tests only against generated disposable samples. The script blocks write smoke tests against non-generated targets unless you explicitly override that guard.

```powershell
.\scripts\test-continue-cli-models.ps1 `
  -Models "qwen3.5:9b" `
  -IncludeWriteSmoke
```

The expected write smoke result is exactly one changed file, `README.md`, with this final line:

```text
Continue CLI approved-write smoke test passed.
```

After checking the result, the script restores the generated sample `README.md` so repeated runs stay clean.

## Command-Template Flexibility

The default command is `npx` with this command-template:

```text
-y @continuedev/cli@1.5.47 --config "{ConfigPath}" --readonly -p "{Prompt}"
```

Use `-ContinueCommand` and `-ContinueArgumentsTemplate` when your Continue CLI command differs. Use `-ModelArgumentTemplate` only when your CLI supports a model flag.

Available placeholders:

- `{Prompt}`: the generated read or write test prompt.
- `{Model}`: the current model under test.
- `{PromptFile}`: path to the temporary prompt file.
- `{TargetRepo}`: generated sample repository path.
- `{ConfigPath}`: Continue config path.

Example for a CLI that accepts a model flag:

```powershell
.\scripts\test-continue-cli-models.ps1 `
  -Models "qwen3.5:9b" `
  -ModelArgumentTemplate '--model "{Model}"'
```


## Model Unload Safety

For online or remote Ollama testing, unload each model after its CLI run so large models do not stay resident and overload the server.

Windows PowerShell:

```powershell
-UnloadAfterEach -OllamaBaseUrl "http://127.0.0.1:11434"
```

Linux/macOS:

```bash
--unload-after-each --ollama-base-url http://127.0.0.1:11434
```

The unload call uses Ollama's local API with `keep_alive` set to `0`. Runtime reports record whether unload was requested, but they still omit private endpoints.

## Evidence Flow

Recommended sequence:

1. Run Ollama API-level model tests with `docs/local-agent-model-testing.md`.
2. Run Continue CLI read-only screening with this guide.
3. Run optional Continue CLI write smoke testing on generated samples.
4. Run editor-specific read and write validation before marking a setup approved-write ready.

## Reading Results

Reports are written to `runtime-validation-output/continue-cli-model-tests-*.json` and intentionally stay local-only. Do not commit runtime validation output.

Common failure signals:

- `READ_VALIDATION_FAILED`: the CLI ran but did not produce enough repository evidence.
- `UNEXPECTED_WRITE_DURING_READ`: the read-only prompt changed files.
- `WRITE_VALIDATION_FAILED`: write smoke testing did not produce exactly the expected README-only change.
- `TARGET_REPO_NOT_CLEAN`: the disposable sample had existing changes before the test.
- `SCRIPT_EXCEPTION`: the harness itself hit an unexpected error.
