# Aider Validation Evidence

This file records sanitized Aider validation evidence for this pack. It should not include private endpoints, local paths, usernames, raw transcripts, private repository names, customer names, or source code from private repositories.

## Evidence: 2026-07-15 Qwen 3.5 9B Read And Write Smoke

### Summary

- Surface: Aider CLI
- Aider version: 0.86.2
- Operating system: Windows
- Model: qwen3.5:9b
- Provider: Ollama
- Target repository source: generated disposable Python sample
- Private details removed: Yes

### Results

| Test | Result | Notes |
| --- | --- | --- |
| Read-only context validation | Pass | The CLI completed the generated-sample read phase. |
| Disposable write smoke | Pass | The harness verified the expected isolated write. |
| External verification | Pass | Git and direct file checks passed before fixture cleanup. |
| Model unload after validation | Pass | The Ollama process list was empty after the run. |

### Decision

- Validation level: read-only-tool-validated and write-smoke-validated for Aider CLI only.
- Real-project approved-write position: blocked. This evidence does not validate a non-generated repository or another agent surface.
- Failure signals: none.

## Current Status

Aider is currently a candidate agent surface. Model-backed read-only context validation, disposable write-smoke validation, and realistic scoped-edit validation have passed for `qwen3-coder:30b` against the generated Python sample. A richer disposable Node service scoped edit has also passed with external Node test verification. Real-project approved-write readiness is still blocked until validation passes in an explicitly approved non-generated repository.

## Evidence: 2026-07-13 Read-Only Context Validation

### Summary

- Date: 2026-07-13
- Surface: Aider CLI
- Aider version: 0.86.2
- Operating system: Windows
- CPU architecture: x64
- Model: qwen3-coder:30b
- Provider: Ollama
- Target repository type: Python API sample
- Target repository source: generated disposable sample
- Tool/write mode: read-only file context
- Git status before test: clean
- Git status after test: clean
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Read-only repository inspection | Pass | Aider received explicit read-only context for `README.md`, `pyproject.toml`, `app/main.py`, `app/settings.py`, and `tests/test_main.py`. |
| Unexpected file changes during read-only test | Pass | Verified outside Aider with Git; generated sample remained clean. |
| Disposable write smoke test | Not run | Still required before approved-write consideration. |
| External changed-file verification | Not run | Required for future write smoke validation. |
| Model unload after validation | Pass | The validation run used unload-after-each behavior and the Ollama process list was empty afterward. |

### Decision

- Validation level: read-only-context-validated
- Approved-write position: blocked pending disposable write-smoke and realistic scoped-edit validation
- Failure signals: none
- Follow-up: Run Aider disposable write-smoke validation against the generated Python sample after read-only evidence is reviewed.

### Sanitization Checklist

- [x] No private endpoints.
- [x] No private IP addresses.
- [x] No local filesystem paths.
- [x] No usernames.
- [x] No private repository names.
- [x] No customer names.
- [x] No tokens or secrets.
- [x] No raw private-code transcript.

## Evidence: 2026-07-13 Realistic Scoped-Edit Validation

### Summary

- Date: 2026-07-13
- Surface: Aider CLI
- Aider version: 0.86.2
- Operating system: Windows
- CPU architecture: x64
- Model: qwen3-coder:30b
- Provider: Ollama
- Target repository type: Python API sample
- Target repository source: generated disposable sample
- Tool/write mode: realistic scoped edit
- Git status before test: clean
- Git status after test: restored to clean
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Scoped source/test edit | Pass | Aider updated only `app/settings.py`, `app/main.py`, and `tests/test_main.py`. |
| Unrelated file protection | Pass | README, sample metadata, project config, and other files were unchanged. |
| External changed-file verification | Pass | Git showed exactly the expected three changed files. |
| Whitespace verification | Pass after correction | Initial whole-file edit left one trailing-whitespace blank line; a follow-up Aider diff-format cleanup removed it and `git diff --check` passed. |
| Behavior verification | Pass | Direct Python checks validated default and overridden service-name responses. |
| Test runner availability | Partial | `pytest` was not installed in the Python 3.12 environment, so verification used `compileall` plus direct function assertions. |
| Model unload after validation | Pass | The model was explicitly unloaded and the Ollama process list was empty afterward. |
| Disposable sample cleanup | Pass | The generated sample repository was restored to clean after evidence capture. |

### Decision

- Validation level: realistic-scoped-edit-validated
- Approved-write position: still blocked for real projects pending realistic disposable application or explicitly approved non-generated repository validation
- Failure signals: initial trailing-whitespace issue corrected by Aider using diff edit format; pytest unavailable in local Python environment
- Follow-up: Add or select a richer disposable application target before promoting Aider beyond generated-sample scoped-edit validation.

### Sanitization Checklist

- [x] No private endpoints.
- [x] No private IP addresses.
- [x] No local filesystem paths.
- [x] No usernames.
- [x] No private repository names.
- [x] No customer names.
- [x] No tokens or secrets.
- [x] No raw private-code transcript.

## Evidence: 2026-07-13 Disposable Write-Smoke Validation

### Summary

- Date: 2026-07-13
- Surface: Aider CLI
- Aider version: 0.86.2
- Operating system: Windows
- CPU architecture: x64
- Model: qwen3-coder:30b
- Provider: Ollama
- Target repository type: Python API sample
- Target repository source: generated disposable sample
- Tool/write mode: read-only file context plus disposable README write smoke
- Git status before test: clean
- Git status after test: clean
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Read-only repository inspection | Pass | Read-only context validation passed before the write-smoke phase. |
| Unexpected file changes during read-only test | Pass | Verified outside Aider with Git; generated sample remained clean after the read phase. |
| Disposable write smoke test | Pass | Aider changed only `README.md` with the expected final line. |
| External changed-file verification | Pass | Harness verified changed-file set, `git diff --check`, and direct README content before restoring the disposable sample. |
| Model unload after validation | Pass | The validation run used unload-after-each behavior and the Ollama process list was empty afterward. |

### Decision

- Validation level: write-smoke-validated
- Approved-write position: blocked pending realistic scoped-edit validation
- Failure signals: none
- Follow-up: Run a realistic scoped-edit validation in a disposable or explicitly approved repository before marking Aider approved-write ready.

### Sanitization Checklist

- [x] No private endpoints.
- [x] No private IP addresses.
- [x] No local filesystem paths.
- [x] No usernames.
- [x] No private repository names.
- [x] No customer names.
- [x] No tokens or secrets.
- [x] No raw private-code transcript.

## Evidence: 2026-07-13 Richer Disposable Node Service Scoped-Edit Validation

### Summary

- Date: 2026-07-13
- Surface: Aider CLI
- Aider version: 0.86.2
- Operating system: Windows
- CPU architecture: x64
- Model: qwen3-coder:30b
- Provider: Ollama
- Target repository type: Node service sample
- Target repository source: generated disposable sample
- Tool/write mode: realistic scoped edit
- Git status before test: clean standalone sample baseline
- Git status after test: restored to clean
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Scoped source/test edit | Pass | Aider updated only `src/server.js` and `test/server.test.js`. |
| Unrelated file protection | Pass | README, sample metadata, package configuration, Dockerfile, and other files were unchanged. |
| External changed-file verification | Pass | Git showed exactly the expected two changed files. |
| Whitespace verification | Pass | `git diff --check` passed. |
| Runtime test verification | Pass | `node --test` passed with ten tests. |
| Edge behavior verification | Pass after correction | An external assertion caught a missed whitespace-only fallback; a follow-up Aider diff-format correction fixed the behavior. |
| Model unload after validation | Pass | The model was explicitly unloaded and the Ollama process list was empty afterward. |
| Disposable sample cleanup | Pass | The generated sample repository was restored to clean after evidence capture. |

### Decision

- Validation level: richer-disposable-scoped-edit-validated
- Approved-write position: still blocked for real projects pending explicitly approved non-generated repository validation
- Failure signals: initial implementation missed whitespace-only service-name fallback; corrected by Aider using diff edit format
- Follow-up: Use an explicitly approved non-generated repository before marking Aider approved-write ready for real projects.

### Sanitization Checklist

- [x] No private endpoints.
- [x] No private IP addresses.
- [x] No local filesystem paths.
- [x] No usernames.
- [x] No private repository names.
- [x] No customer names.
- [x] No tokens or secrets.
- [x] No raw private-code transcript.

## Evidence Template

### Summary

- Date:
- Surface: Aider CLI
- Aider version:
- Operating system:
- CPU architecture:
- Model:
- Provider:
- Target repository type:
- Target repository source: generated disposable sample / other sanitized target
- Tool/write mode: read-only / disposable write-smoke / patch mode
- Git status before test:
- Git status after test:
- Private details removed: Yes

### Tests

| Test | Result | Notes |
| --- | --- | --- |
| Read-only repository inspection | Not run | Record exact inspected filenames, sanitized if needed. |
| Unexpected file changes during read-only test | Not run | Verify outside Aider with Git. |
| Disposable write smoke test | Not run | Only valid against generated samples. |
| External changed-file verification | Not run | Use `git status`, `git diff --check`, and direct file read. |

### Decision

- Validation level:
- Approved-write position:
- Failure signals:
- Follow-up:

### Sanitization Checklist

- [ ] No private endpoints.
- [ ] No private IP addresses.
- [ ] No local filesystem paths.
- [ ] No usernames.
- [ ] No private repository names.
- [ ] No customer names.
- [ ] No tokens or secrets.
- [ ] No raw private-code transcript.
