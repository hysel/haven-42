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
- optionally remove failed models when explicitly requested

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


## Current Candidate Evidence

The current simple-hardware default remains `qwen3.5:9b` for WRITE SAFE, PLAN ONLY, and DEEP REVIEW profiles.

Recent automated API-level screening and Continue CLI prompt validation found two additional candidates worth manual editor testing:

| Model | Automated Result | Next Step |
| --- | --- | --- |
| `Qwen3-Coder-Next:latest` | Passed API-level tool/exact-content screening and completed all generated Python sample CLI workflows; 10 of 12 workflow outputs passed verification. | Try manual Continue editor Apply validation before granting write-safe status. |
| `devstral-small-2:latest` | Passed API-level tool/exact-content screening and completed all generated Python sample CLI workflows; 10 of 12 workflow outputs passed verification. | Try manual Continue editor Apply validation before granting write-safe status. |

Both candidates failed verification only on filename-drift guardrails in non-code workflows. That is a prompt-quality follow-up, not proof that either model is write-safe.

Additional missing-model screening found:

| Model | Automated Result | Next Step |
| --- | --- | --- |
| `llama3.1:8b-instruct-q5_K_M` | Passed API-level structured tool-call and exact-content screening. | Treat as an API-level candidate only; run manual Continue editor Apply validation before write-safe use. |
| `sammcj/glm-4-32b-0414:q6_k` | Failed structured tool-call validation. | Do not use for tool-backed Agent workflows unless settings or model variant changes. |
| `deepseek-r1:14b` | Failed structured tool-call validation. | Do not use for tool-backed Agent workflows unless settings or model variant changes. |
| `qwen3-coder-localpilot:latest` | Not installed and not pullable by that exact name. | Remove from active candidate lists unless a valid local tag is created. |
| `architect:latest` | Not installed and not pullable by that exact name. | Remove from active candidate lists unless a valid local tag is created. |
| `coder:latest` | Not installed and not pullable by that exact name. | Remove from active candidate lists unless a valid local tag is created. |


## Progress Output And Pull Timeouts

The model test runner prints numbered progress messages so users can tell what is happening during long runs:

- `[1/8]` prepares the local test run.
- `[2/8]` validates the target repository path.
- `[3/8]` connects to Ollama and reads installed models.
- `[4/8]` reads VRAM from a local or remote model profile when one is supplied.
- `[5/8]` prints the candidate list, VRAM estimate, and API timeout.
- `[6/8]` tests each model, including optional pulls, model loading, tool-call checks, and exact-content checks.
- `[7/8]` unloads or removes models when requested.
- `[8/8]` writes the sanitized JSON report and final summary.

Large model downloads can take longer than the default API timeout. If a pull fails with `MODEL_NOT_INSTALLED` and the report shows a timeout, either increase the timeout or pull the model directly on the Ollama server first.

Windows example for a large model pull:

```powershell
.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "qwen3.5:35b" `
  -PullMissing `
  -UnloadAfterEach `
  -TimeoutSeconds 1800
```

Linux or macOS example:

```bash
./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:35b" \
  --pull-missing \
  --unload-after-each \
  --timeout-seconds 1800
```

Manual pull fallback on the Ollama server:

```bash
ollama pull qwen3.5:35b
```

After a manual pull succeeds, rerun the test. A model that previously reported `MODEL_NOT_INSTALLED` because of a timeout may become a valid API-level candidate.
## Gate Pulls By Available VRAM

Use the local model profile scripts first, then pass the generated JSON into the
model test runner. This ties candidate pulls to the GPU/CPU detection already
used by the setup flow and avoids manually copying VRAM values.

The runner uses `TotalDedicated` VRAM by default, which sums visible dedicated or
unknown GPU memory in `Gpus[].VramGb`. Use `MaxDedicated` when you want the more
conservative single-GPU limit. Passing `AvailableVramGb` still wins over the
profile value and is useful for controlled tests.

Windows:

```powershell
.\scripts\get-local-model-profile.windows.ps1 -AsJson |
  Set-Content .\runtime-validation-output\local-model-profile.json

.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "qwen3.5:9b","devstral:24b","qwen3.5:35b","qwen3.5:122b" `
  -ModelProfilePath .\runtime-validation-output\local-model-profile.json `
  -VramSelectionMode TotalDedicated `
  -PullMissing `
  -UnloadAfterEach `
  -RemoveFailedModels
```

Linux:

```bash
mkdir -p runtime-validation-output
./scripts/get-local-model-profile.linux.sh --json \
  > runtime-validation-output/local-model-profile.json

./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b,devstral:24b,qwen3.5:35b,qwen3.5:122b" \
  --model-profile-path runtime-validation-output/local-model-profile.json \
  --vram-selection-mode TotalDedicated \
  --pull-missing \
  --unload-after-each \
  --remove-failed-models
```

macOS:

```bash
mkdir -p runtime-validation-output
./scripts/get-local-model-profile.macos.sh --json \
  > runtime-validation-output/local-model-profile.json

./scripts/test-local-agent-models.macos.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "qwen3.5:9b,devstral:24b,qwen3.5:35b,qwen3.5:122b" \
  --model-profile-path runtime-validation-output/local-model-profile.json \
  --vram-selection-mode TotalDedicated \
  --pull-missing \
  --unload-after-each \
  --remove-failed-models
```

Models estimated to fit the detected VRAM can be pulled and tested. Oversized
models are skipped before pull with `MODEL_SKIPPED_FOR_VRAM`. The JSON report
records `ModelProfilePath`, `VramSelectionMode`, `AvailableVramGb`,
`AvailableVramSource`, `IncludeOversizedModels`, and per-model
`VramRecommendation` details.

Use `-AvailableVramGb` or `--available-vram-gb` only when you intentionally want
to override the detected profile value. Use `-IncludeOversizedModels` or
`--include-oversized-models` only when you intentionally want to test a model
above the estimated VRAM limit.

## Platform-Specific Pull Safety

The model test scripts also skip tags that do not make sense for the detected
model host before any pull is attempted. Cloud catalog tags are not local Ollama
pull targets and are skipped with `MODEL_SKIPPED_FOR_PLATFORM`. MLX tags are
skipped with the same signal unless the model host platform is macOS.

When `ModelProfilePath` points at a local or remote hardware profile, the
scripts use that profile's `Platform` value as the model host platform. Without
a profile, they use the platform running the script. This matters when, for
example, Windows is controlling a Linux Ollama server or a Mac is controlling a
Linux Ollama server.
## Remove Failed Models

Use cleanup mode only when you intentionally want failed candidates removed from
the Ollama server after the API preflight. This is useful for experimental model
screening, but it is destructive because it deletes local model downloads.

Windows:

```powershell
.\scripts\test-local-agent-models.ps1 `
  -OllamaBaseUrl "http://127.0.0.1:11434" `
  -TargetRepo "C:\path\to\sample-repo" `
  -Models "candidate-model:tag" `
  -PullMissing `
  -UnloadAfterEach `
  -RemoveFailedModels
```

Linux or macOS:

```bash
./scripts/test-local-agent-models.linux.sh \
  --ollama-base-url "http://127.0.0.1:11434" \
  --target-repo "/path/to/sample-repo" \
  --models "candidate-model:tag" \
  --pull-missing \
  --unload-after-each \
  --remove-failed-models
```

Cleanup mode runs only after a tested model fails one of the API checks. Passing
models are kept. Missing models that were never pulled are not removed. The JSON
report includes a `RemoveFailedModels` flag and per-model `Removal` result so
users can see whether deletion was attempted and whether it succeeded.

## Recommendation Output

After all candidates are tested, the runner prints `Recommended model:` and
writes a `Recommendation` object into the JSON report. The recommendation is
chosen only from models that passed the API-level structured tool-call and
exact-content checks. It prefers the smallest passing model first, with a small
preference for coding-oriented local-agent model families.

Treat this as the model to validate next in the editor, not as automatic
approval for write-safe use. Continue read-only validation and approved-write
smoke testing are still required before installing the model into a write-safe
profile.
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
