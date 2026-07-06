# Multi-Language Workflow Validation Evidence

This file records sanitized validation evidence for generated multi-language workflow validation.

Do not include private repository names, private paths, private endpoints, usernames, hostnames, tokens, raw private source code, or raw transcripts.

## 2026-07-06 Python And TypeScript Workflow Validation

### Summary

- Validation type: Generated sample repository workflow validation
- Repository categories: Python API sample, TypeScript frontend sample
- Operating system: Windows
- Editor surface: Continue CLI through `npx @continuedev/cli`
- Continue version: CLI available locally; exact version not recorded in committed evidence
- Model: Local Ollama model from ignored local-only config
- Provider: Ollama-compatible local endpoint, endpoint omitted
- MCP state: Not used
- Pack version or commit: `0.2.0` development branch after language rule-pack validation evidence

### Setup

- Generated disposable samples under ignored runtime output.
- Confirmed generated `python-api` includes `README.md`, `SAMPLE-METADATA.md`, `pyproject.toml`, `app/main.py`, `app/settings.py`, and `tests/test_main.py`.
- Confirmed generated `typescript-frontend` includes `README.md`, `SAMPLE-METADATA.md`, `package.json`, `tsconfig.json`, `src/App.tsx`, and `src/app.test.ts`.
- Generated runtime context for each sample repository.
- Ran Continue CLI workflows with a local-only Ollama config after the local model server responded to preflight.
- Kept raw outputs in ignored runtime output and committed only sanitized status evidence.

### Results

| Check | Python API Sample | TypeScript Frontend Sample | Notes |
| --- | --- | --- | --- |
| Generate sample repository | Passed | Passed | Disposable samples were created under ignored runtime output. |
| Generate runtime context | Passed | Passed | Context included file inventory, README excerpt, and project metadata excerpts. |
| Local Ollama API preflight | Passed | Passed | Server responded before Continue CLI workflows started. |
| Repository discovery | Passed verification | Passed verification | Final review text was produced. |
| Architecture review | Passed verification | Passed verification | Final review text was produced. |
| Code review | Passed verification | Passed verification | Final review text was produced. |
| Implementation planning | Passed verification | Passed verification | Final review text was produced. |
| Bug investigation | Passed verification | Passed verification | Final review text was produced. |
| Security review | Passed verification | Passed verification | Final review text was produced. |
| Performance review | Passed verification | Passed verification | Final review text was produced. |
| Documentation review | Failed guardrail verification | Failed guardrail verification | Output referenced documentation filenames that were not present in supplied context. |
| AI framework self-review | Passed verification | Failed guardrail verification | TypeScript output referenced `.continue/config.yaml`, which was not present in supplied context. |
| Refactoring planner | Passed verification | Passed verification | Final review text was produced. |
| Product manager | Passed verification | Passed verification | Final review text was produced. |
| Release readiness | Passed verification | Failed guardrail verification | TypeScript output referenced `CHANGELOG.md`, which was not present in supplied context. |

### Failure Signals

- `FILENAME_NOT_IN_CONTEXT`
- `DOCUMENTATION_WORKFLOW_FILENAME_DRIFT`
- `AI_FRAMEWORK_SELF_REVIEW_FILENAME_DRIFT`
- `RELEASE_READINESS_FILENAME_DRIFT`

### What Worked

- The generated Python and TypeScript samples exercised the runtime runner without relying on private repositories.
- The local Ollama preflight prevented the earlier request-timeout failure mode.
- Continue CLI produced final text for all workflows instead of raw tool-call-only output.
- Runtime output verification caught filename drift in documentation and release-style workflows.

### Gaps

- Documentation review still suggests conventional files such as architecture, contributing, and setup docs even when those files are not present in context.
- Some non-code workflows can still reference configuration or release files that were not provided by the generated sample context.
- The validation confirms workflow execution and guardrail behavior; it does not yet prove language-specific recommendation quality across larger real repositories.

### Pack Follow-Up

- Strengthen documentation, AI framework self-review, and release-readiness prompts to label missing files as recommended additions without implying they exist.
- Add fixture coverage for filename drift in documentation and release-style outputs.
- Continue validating additional generated ecosystems before promoting broader language support.


## 2026-07-06 Candidate Model Continue CLI Validation

### Summary

- Validation type: Candidate model prompt workflow validation
- Repository category: Generated Python API sample
- Surface: Continue CLI through `npx @continuedev/cli`
- Provider: Ollama-compatible local endpoint, endpoint omitted
- Candidate models: `Qwen3-Coder-Next:latest`, `devstral-small-2:latest`
- Raw output location: ignored runtime output only

### Results

| Candidate Model | Workflows Completed | Verification Passed | Guardrail Failures | Notes |
| --- | --- | --- | --- | --- |
| `Qwen3-Coder-Next:latest` | 12 of 12 | 10 of 12 | `ai-framework-self-review`, `release-readiness` | Failed checks were filename-drift issues, not tool-call-only output. |
| `devstral-small-2:latest` | 12 of 12 | 10 of 12 | `ai-framework-self-review`, `release-readiness` | Failed checks were filename-drift issues, not tool-call-only output. |

### Interpretation

- Both candidate models are viable for further Continue CLI prompt validation.
- Both candidates still require manual Continue editor Apply validation before being treated as write-safe.
- Both candidates showed the same remaining prompt-quality risk: non-code workflows can reference files that were not present in supplied runtime context.

### Follow-Up

- Keep `qwen3.5:9b` as the write-safe starter default until a candidate passes manual editor Apply validation.
- Consider `Qwen3-Coder-Next:latest` and `devstral-small-2:latest` for plan/review candidate testing.
- Strengthen `ai-framework-self-review` and `release-readiness` prompts against filename drift.
### Sanitization Checklist

- [x] No private repository names.
- [x] No private local paths.
- [x] No private endpoints, IP addresses, or hostnames.
- [x] No usernames.
- [x] No tokens or secrets.
- [x] No raw private source code.
- [x] No raw transcripts.
- [x] No customer, employer, or internal project identifiers.
