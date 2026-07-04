# Editor Surface Validation Evidence

This file records sanitized editor-surface validation evidence for this pack. It should not include private endpoints, local paths, usernames, raw transcripts, private repository names, or customer names.

## 2026-07-03 Windows Editor Preflight

### Summary

- Date: 2026-07-03
- Operating system: Windows
- CPU architecture: x64
- Repository state: clean before validation
- Config source tested: project-local `.continue/config.yaml`
- Private details removed: Yes

### Detected Editor Surfaces

| Surface | Detection result | Version | Continue extension | Status |
| --- | --- | --- | --- | --- |
| VS Code-compatible build | Found on `PATH` as `code` | 1.125.1 | `continue.continue@2.0.0` | Extension installed; GUI config loading not proven by terminal preflight. |
| VSCodium | Found on `PATH` as `codium` | 1.121.03429 | `continue.continue@2.1.0` | Extension installed; GUI config loading not proven by terminal preflight. |

### CLI Fallback Check

Command shape:

```powershell
npx -y @continuedev/cli --config .continue/config.yaml --readonly -p "Reply OK"
```

Result:

- Status: Failed
- Observed behavior: CLI returned a model connection error.
- Interpretation: The CLI command reached the model-backed execution path but could not connect to the model provider from the current shell using the committed shared config.
- Safe fallback: Confirm Ollama is running, confirm the starter model is installed, or use an ignored local config override for machine-specific endpoints.

### Decision

- VS Code-compatible build: Read-only tool validated with `qwen3-coder:30b` in an application-style sample repository. Duplicate-rule status was not confirmed in this run.
- VSCodium: Candidate editor surface. Continue extension is installed, but project-local config loading and Agent tools still require in-editor validation.
- Continue CLI: Not validated for model-backed execution in this run because the provider connection failed.

## 2026-07-03 VS Code-Compatible Read-Only Agent Test

### Summary

- Date: 2026-07-03
- Editor surface: VS Code-compatible build
- Model: `qwen3-coder:30b`
- Provider: Ollama
- Operating system: Windows
- CPU architecture: x64
- Config source tested: project-local `.continue/config.yaml`
- Repository type tested: .NET Framework Excel-DNA add-in sample repository
- Git status before test: clean
- Git status after test: clean
- Duplicate-rule warnings: Unknown
- Raw JSON tool calls: No
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Read-only repository discovery | Pass | The response identified a .NET Framework Excel-DNA add-in style repository and referenced real project files. |
| Read-only Agent list-files test | Pass | The response summarized top-level files such as the solution, project file, Excel-DNA add-in file, source file, config files, package config, and documentation files. |
| Unexpected file changes | Pass | `git status --short` was empty after the Agent test. |
| Raw JSON tool-call behavior | Pass | The final response did not print raw JSON tool calls. |
| Duplicate-rule warnings | Unknown | The test report did not confirm whether duplicate-rule warnings appeared. |

### Decision

- Mark VS Code-compatible build plus `qwen3-coder:30b` as read-only tool validated for this sample repository.
- Do not mark approved-write ready from this test; no write-mode smoke test was performed.
- Validate duplicate-rule status in a future VS Code-compatible run.

### Follow-Up

- Run the read-only editor test in VSCodium.
- Run the Agent tool test in VSCodium.
- Record whether duplicate-rule warnings appear.
- Record whether the model executes tools or prints raw JSON tool calls in VSCodium.

### Sanitization Checklist

- [x] No private endpoints.
- [x] No private IP addresses.
- [x] No local filesystem paths.
- [x] No usernames.
- [x] No private repository names.
- [x] No customer names.
- [x] No tokens or secrets.
- [x] No raw private-code transcript.
