# Cline Read-Only Validation Evidence

This file records sanitized Cline validation results. It starts as a template. Do not mark Cline validated until a real read-only run is completed and externally verified.

## Status

| Field | Value |
| --- | --- |
| Surface | Cline |
| Current status | Read-only tool validated for generated Python sample with `qwen3-coder:30b` at 16k context |
| Approved-write status | Write smoke-test validated for disposable generated Python sample; blocked for real projects |
| Evidence state | Passing and failed read-only runs plus passing disposable write smoke test recorded |

## Validation Record Template

Copy this section for each validation run.

### YYYY-MM-DD Cline Read-Only Generated Sample Test

#### Summary

- Date: YYYY-MM-DD
- Surface: Cline
- Surface version: Not recorded
- Editor host: Not recorded
- Operating system: Not recorded
- CPU architecture: Not recorded
- Model: Not recorded
- Provider: Not recorded
- Config source: Not recorded
- Sample repository: Not recorded
- Tool permission mode: Read-only requested
- MCP state: Not recorded
- Private details removed: Yes

#### Prompt Used

```text
Use tools to inspect the opened repository root.

Do not modify files.
Do not create files.
Do not run package installation.
Do not guess.

Return:
1. The exact top-level files and folders you inspected.
2. The project type, based only on files you actually read.
3. The key source and test files you inspected.
4. Any risks or missing information.
5. The failure signal if tools are unavailable.

If tools are unavailable, say TOOLS_UNAVAILABLE.
```

#### Observed Files

| Evidence | Result |
| --- | --- |
| Exact top-level names listed | Not recorded |
| Project marker files read | Not recorded |
| Source files read | Not recorded |
| Test files read | Not recorded |
| Invented files observed | Not recorded |

#### External Verification

| Check | Result |
| --- | --- |
| `git status --short` before test | Not recorded |
| `git status --short` after test | Not recorded |
| `git diff --check` after test | Not recorded |
| Unexpected files created | Not recorded |
| Private details removed | Not recorded |

#### Decision

- Status: Candidate only
- Failure signal: Not recorded
- Promotion decision: Do not promote until the run is completed and externally verified.

## Sanitization Checklist

- [ ] No private endpoints.
- [ ] No private IP addresses.
- [ ] No local filesystem paths.
- [ ] No usernames.
- [ ] No private repository names.
- [ ] No customer names.
- [ ] No tokens or secrets.
- [ ] No raw private-code transcript.

## 2026-07-15 Cline CLI Isolated Read-Only Generated Sample Test

- Surface: Cline CLI 3.0.41 on Windows.
- Model/provider: Devstral Small 2 24B through an isolated OpenAI-compatible local Ollama profile.
- Target: generated Python sample.
- Tool permission mode: Headless auto-approval, required by the CLI for non-interactive tool calls.
- Read result: README and project metadata were read successfully.
- External verification: disposable Git status remained clean and whitespace validation passed.
- Resource check: the tested model was unloaded after the run.
- Decision: read-only CLI evidence is valid for this exact surface/model/OS path. It does not approve editor behavior, headless writes, or real-project changes.
## 2026-07-08 Cline Read-Only Generated Python Sample Test

### Summary

- Date: 2026-07-08
- Surface: Cline
- Surface version: Not recorded
- Editor host: VS Code-compatible editor, exact host not recorded
- Operating system: Windows
- CPU architecture: Not recorded
- Model: `devstral-small-2:24b`
- Provider: Ollama
- Config source: Cline local model configuration, exact config source not recorded
- Sample repository: generated `python-api` sample
- Tool permission mode: Read-only requested
- MCP state: Not recorded
- Private details removed: Yes

### Prompt Used

```text
Use tools to inspect the opened repository root.

Do not modify files.
Do not create files.
Do not run package installation.
Do not guess.

Return:
1. The exact top-level files and folders you inspected.
2. The project type, based only on files you actually read.
3. The key source and test files you inspected.
4. Any risks or missing information.
5. The failure signal if tools are unavailable.

If tools are unavailable, say TOOLS_UNAVAILABLE.
```

### Observed Result

The response announced an intent to inspect files and printed a `list_files` tool-call shape containing a local absolute path. It then switched to a generic task-planning response and asked the user to provide a task, instead of completing the requested repository inspection.

### Observed Files

| Evidence | Result |
| --- | --- |
| Exact top-level names listed | No |
| Project marker files read | No |
| Source files read | No |
| Test files read | No |
| Invented files observed | No generic invented repository structure observed, but the requested inspection did not complete. |

### External Verification

| Check | Result |
| --- | --- |
| `git status --short` after test | Clean |
| `git diff --check` after test | Clean |
| Unexpected files created | No |
| Private details removed | Yes |

### Decision

- Status: Candidate only
- Failure signal: `RAW_TOOL_CALL_OUTPUT`
- Secondary signal: `READ_TOOLS_UNAVAILABLE`
- Promotion decision: Do not promote Cline to read-only validated from this run. Retest only after Cline tool execution is configured so file listing and file reads complete without printed tool-call syntax or task reset behavior.

## 2026-07-08 Cline Read-Only Generated Python Sample Retest At 16k Context

### Summary

- Date: 2026-07-08
- Surface: Cline
- Surface version: Not recorded
- Editor host: VS Code-compatible editor, exact host not recorded
- Operating system: Windows
- CPU architecture: Not recorded
- Provider: Ollama
- Config source: Cline local model configuration, exact config source not recorded
- Sample repository: generated `python-api` sample
- Tool permission mode: Read-only requested
- MCP state: Not recorded
- Private details removed: Yes

### Prompt Used

```text
Use tools to inspect the opened repository root.

Do not modify files.
Do not create files.
Do not run package installation.
Do not guess.

Return:
1. The exact top-level files and folders you inspected.
2. The project type, based only on files you actually read.
3. The key source and test files you inspected.
4. Any risks or missing information.
5. The failure signal if tools are unavailable.

If tools are unavailable, say TOOLS_UNAVAILABLE.
```

### Model Results

| Model | Result | Files read | Notes |
| --- | --- | --- | --- |
| `qwen3-coder:30b` | Read-only pass | `README.md`, `pyproject.toml`, `app/main.py`, `app/settings.py`, `tests/test_main.py` | Returned the requested numbered result, identified the generated Python API sample, and did not modify files. `SAMPLE-METADATA.md` was listed but not read. |
| `qwen3.5:9b` | Read-only pass with caveats | `pyproject.toml`, `README.md`, `SAMPLE-METADATA.md`, `app/main.py`, `app/settings.py`, `tests/test_main.py` | Read actual files and returned a structured answer, but included unsupported/noisy claims such as a configuration risk label without evidence and surface artifact text. |
| `devstral-small-2:24b` | Read-only candidate, partial output captured | `pyproject.toml`, `README.md`, `SAMPLE-METADATA.md`, `app/main.py`, `app/settings.py`, `tests/test_main.py` | Read actual files and started a grounded project summary, but the full final response was not captured in evidence, so it is not promoted from this run. |

### External Verification

| Check | Result |
| --- | --- |
| `git status --short` after test | Clean |
| `git diff --check` after test | Clean |
| Unexpected files created | No |
| Private details removed | Yes |

### Decision

- Status: Read-only tool validated for generated Python sample with `qwen3-coder:30b` at 16k context.
- Caveat: The validation is scoped to Cline, Windows, Ollama, the generated Python sample, and the recorded model/context setup.
- Failure signal: None for the passing `qwen3-coder:30b` run.
- Caution signals for `qwen3.5:9b`: `UNSUPPORTED_CLAIM`, `SURFACE_ARTIFACT`.
- Promotion decision: Promote Cline from candidate-only to read-only validated for the recorded generated-sample scenario only. Keep approved-write blocked until a scoped write smoke test passes and is externally verified.
## 2026-07-08 Cline Approved-Write Smoke Test

### Summary

- Date: 2026-07-08
- Surface: Cline
- Surface version: Not recorded
- Editor host: VS Code-compatible editor, exact host not recorded
- Operating system: Windows
- CPU architecture: Not recorded
- Model: `qwen3-coder:30b`
- Provider: Ollama
- Context setting: 16k
- Config source: Cline local model configuration, exact config source not recorded
- Sample repository: generated `python-api` sample with isolated Git repository
- Tool permission mode: Approved write for one scoped edit
- MCP state: Not recorded
- Private details removed: Yes

### Prompt Used

```text
Use approved write mode for this smoke test only.

Modify the existing README.md in the opened repository root.

Add this exact sentence as the final line of the file:

Cline approved-write smoke test passed.

Do not create any new files.
Do not modify any other files.
Do not run package installation.
Do not reformat the file.

After editing, report only:
1. The changed file.
2. Whether exactly one file was changed.
3. Any failure signal.

Do not commit.
```

### External Verification

| Check | Result |
| --- | --- |
| Git root | Isolated generated `python-api` sample repository |
| `git status --short --untracked-files=all` | Only `README.md` modified |
| `git diff HEAD -- README.md` | One final line added: `Cline approved-write smoke test passed.` |
| `git diff --check` | Clean |
| Direct file-content verification | README ended with the exact expected line |
| Unexpected files created | No |
| Private details removed | Yes |

### Decision

- Status: Write smoke-test validated for disposable generated Python sample.
- Failure signal: None.
- Promotion decision: Do not mark Cline broadly approved-write ready for real projects yet. Next write validation must use a realistic scoped code or configuration edit in a disposable sample and pass external Git and file-content verification.

## 2026-07-20 Cline CLI Realistic Scoped-Edit Attempt

### Summary

- Surface: Cline CLI 3.0.46 on Windows.
- Model/provider: `devstral-small-2:24b` through an isolated OpenAI-compatible Ollama profile.
- Target: fresh disposable generated Python sample with an isolated Git baseline.
- Task: add a `version: v1` health-response field and update its existing exact-dictionary test; only `app/main.py` and `tests/test_main.py` were allowed to change.
- Private endpoint, local paths, raw output, and profile credentials are omitted.

### External Verification

| Check | Result |
| --- | --- |
| Cline process result | Passed; exit code 0 after moving isolated state to a system-temporary directory |
| Changed-file scope | Passed; only `app/main.py` and `tests/test_main.py` changed |
| Direct Python behavior assertion | Passed; exact response contained `service`, `status`, and `version` |
| `git diff --check` | Failed; mixed line endings in `app/main.py` were reported as trailing whitespace |
| Bounded repair attempt | Failed; the model proposed a helper script and exhausted its output-token limit before completing |
| Model unload | Passed; the target model was not resident after each attempt |

### Decision

- Status: Partial pass; do not promote Cline scoped-edit or approved-write readiness.
- Failure signals: `DIFF_CHECK_FAILED`, `MIXED_LINE_ENDINGS`, `REPAIR_NONCOMPLETION`.
- Operational finding: on this Windows setup, a Cline data directory inside the synchronized repository caused repeatable `EEXIST` session-persistence failures after the first tool call. A fresh system-temporary data directory avoided that failure.
- Next gate: repeat a bounded generated-sample source-and-test edit with external scope, behavior, whitespace, line-ending, and unexpected-file verification all passing.

### Hardened Harness Rerun

The new automated scoped-edit gate repeated the Devstral Small 2 24B task with
per-model system-temporary Cline state and explicit workspace anchoring. The
read-only phase passed. During the scoped edit, Cline changed `app/main.py` but
its attempted edit of `tests/test_main.py` failed. The harness rejected the run
instead of accepting the model's completion claim.

| Automated gate | Result |
| --- | --- |
| Read-only inspection | Passed |
| Cline process completion | Passed |
| Exact two-file scope | Failed; only the source edit completed |
| External behavior assertion | Passed for the source behavior |
| `git diff --check` | Failed |
| LF-only edited files | Failed |
| Fixture restoration | Passed; clean after the run |
| Temporary profile cleanup | Passed |
| Model unload | Passed |

Failure signals: `SCOPED_EDIT_SCOPE_FAILED`,
`SCOPED_EDIT_DIFF_CHECK_FAILED`, and `SCOPED_EDIT_LINE_ENDINGS_FAILED`.
Scoped-edit promotion remains blocked.
