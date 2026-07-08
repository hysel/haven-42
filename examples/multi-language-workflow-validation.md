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

## 2026-07-06 Missing Model Existence And API Screening

### Summary

- Validation type: Missing model existence and API-level screening
- Provider: Ollama-compatible local endpoint, endpoint omitted
- Pull behavior: Missing names were pulled when available; non-existent or copied names were filtered out
- Raw output location: ignored runtime output only

### Existence Results

| Model Name | Result | Action |
| --- | --- | --- |
| `qwen3-coder-localpilot:latest` | Not installed and not pullable by that name | Removed from active test list. |
| `architect:latest` | Not installed and not pullable by that name | Removed from active test list. |
| `coder:latest` | Not installed and not pullable by that name | Removed from active test list. |
| `llama3.1:8b-instruct-q5_K_M` | Installed | Tested. |
| `sammcj/glm-4-32b-0414:q6_k` | Installed | Tested. |
| `deepseek-r1:14b` | Installed | Tested. |

### API-Level Screening Results

| Model | Result | Failure Signal | Notes |
| --- | --- | --- | --- |
| `llama3.1:8b-instruct-q5_K_M` | Candidate | `none` | Passed structured tool-call and exact-content checks. Requires manual Continue editor Apply validation before write-safe use. |
| `sammcj/glm-4-32b-0414:q6_k` | Failed | `TOOL_CALL_FAILED` | Did not produce a valid structured tool call and returned unusable exact-content output. |
| `deepseek-r1:14b` | Failed | `TOOL_CALL_FAILED` | Did not produce a valid structured tool call or exact-content output. |

### Interpretation

- `llama3.1:8b-instruct-q5_K_M` is now an API-level candidate, but it still needs manual Continue editor validation.
- GLM and DeepSeek remain poor fits for this pack's tool-backed Agent workflow in the current local setup.
- Copied/custom local names should not remain in candidate lists unless they are installed locally or can be pulled by that exact name.

## 2026-07-08 Generated Java, Go, Rust, SQL, And Infrastructure Workflow Validation

### Summary

- Validation type: Generated sample repository workflow validation
- Repository categories: Java Spring API, Go service, Rust CLI, SQL migrations, Terraform/Kubernetes infrastructure sample
- Operating system: Windows
- Editor surface: Continue CLI through `npx @continuedev/cli`
- Model: `qwen3.5:9b`
- Provider: Ollama-compatible local endpoint, endpoint omitted
- MCP state: Not used
- Pack version or commit: `0.2.0` development branch after optional language rule-pack expansion

### Setup

- Generated disposable samples under ignored runtime output.
- Confirmed local model server preflight before runtime workflows started.
- Ran all runtime validation workflows against generated runtime context for each sample.
- Kept raw outputs in ignored runtime output and committed only sanitized status evidence.

### Results

| Generated Sample | Workflows Run | Verification Passed | Empty Output | Filename-Fidelity Failures | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Java Spring API | 12 | 8 | 1 | 3 | Core review/planning workflows mostly passed; bug investigation returned no final text. |
| Go service | 12 | 6 | 2 | 4 | Discovery and planning paths ran, but security/documentation/release-style outputs referenced absent files. |
| Rust CLI | 12 | 5 | 1 | 6 | Code review returned no final text; several workflows referenced conventional files absent from the generated sample. |
| SQL migrations | 12 | 5 | 0 | 7 | Several workflows invented or normalized migration filenames not present in supplied context. |
| Terraform/Kubernetes infrastructure | 12 | 7 | 0 | 5 | Infrastructure review was usable, but some workflows referenced absent conventional docs or Kubernetes filenames. |

### Failure Signals

- `EMPTY_MODEL_OUTPUT`
- `FILENAME_NOT_IN_CONTEXT`

### What Worked

- The runtime runner completed all workflows for all five generated samples without aborting on empty model output.
- The new empty-output guard recorded `EMPTY_MODEL_OUTPUT` and allowed the remaining workflows to continue.
- Repository discovery, architecture review, code review, implementation planning, security review, performance review, refactoring planner, product manager, and release-readiness each produced at least some passing evidence across the expanded language samples.
- Runtime output verification caught filename drift before the evidence could be mistaken for a clean language-pack pass.

### Gaps

- The expanded validation is not a full editor/model pass for every language pack.
- Some workflows still mention conventional files such as architecture, contributing, changelog, CI, Kubernetes, or migration filenames when those files are absent from generated context.
- Empty output still occurs intermittently with the current local model, so no workflow should rely on a single model response as proof of quality.

### Pack Follow-Up

- Strengthen prompts so missing conventional files are described as recommendations, not as existing files.
- Add filename-drift fixtures for generated Java, Go, Rust, SQL, and Infrastructure samples.
- Keep optional language rule packs evidence-gated until repository-discovery, implementation-planning, and code-review workflows pass consistently per ecosystem.

### Sanitization Checklist

- [x] No private repository names.
- [x] No private local paths.
- [x] No private endpoints, IP addresses, or hostnames.
- [x] No usernames.
- [x] No tokens or secrets.
- [x] No raw private source code.
- [x] No raw transcripts.
- [x] No customer, employer, or internal project identifiers.

## 2026-07-08 Filename-Fidelity Hardening Rerun

### Summary

- Validation type: Generated sample repository workflow validation after prompt and runtime-runner filename-fidelity hardening
- Repository categories: Java Spring API, Go service, Rust CLI, SQL migrations, Terraform/Kubernetes infrastructure sample
- Operating system: Windows
- Editor surface: Continue CLI through `npx @continuedev/cli`
- Model: `qwen3.5:9b`
- Provider: Ollama-compatible local endpoint, endpoint omitted
- MCP state: Not used

### Changes Validated

- Added a filename-fidelity gate to every runtime review prompt, including repository discovery.
- Updated the runtime validation runners to inject filename-fidelity instructions next to the supplied runtime context for every workflow.
- Updated deterministic runtime output verification so absent filenames are allowed only when clearly labeled as recommended new files or missing-file recommendations.
- Added pack tests that require prompt-level and runner-level filename-fidelity guardrails.

### Latest Runtime Results

| Generated Sample | Workflows Run | Verification Passed | Empty Output | Filename-Fidelity Failures | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Java Spring API | 12 | 5 | 2 | 5 | Runtime runner completed all workflows; model still referenced absent conventional docs/config files. |
| Go service | 12 | 4 | 1 | 7 | Runtime runner completed all workflows; release, security, performance, and discovery outputs still showed filename drift. |
| Rust CLI | 12 | 6 | 1 | 5 | Runtime runner completed all workflows; several workflows still referenced absent conventional docs. |
| SQL migrations | 12 | 5 | 1 | 6 | Runtime runner completed all workflows; migration/documentation/release outputs still referenced absent files. |
| Terraform/Kubernetes infrastructure | 12 | 5 | 0 | 7 | Runtime runner completed all workflows; IaC outputs still referenced absent conventional docs and manifests. |

### Interpretation

- The pack now prevents filename drift from being silently accepted by runtime evidence.
- Prompt-level and runtime-runner guardrails are necessary but not sufficient for the tested local model.
- Deterministic verification remains the correct acceptance gate for language-pack promotion.
- Optional language rule packs should remain evidence-gated until generated workflow validation passes consistently.

### Follow-Up

- Add a stricter template or post-processing fallback for workflows that repeatedly fail deterministic filename-fidelity verification.
- Consider workflow-specific output templates for documentation, release-readiness, product, and AI framework self-review because they most often invent conventional files.
- Keep recording filename-drift failures as pack improvements instead of treating partial model output as clean validation evidence.

### Sanitization Checklist

- [x] No private repository names.
- [x] No private local paths.
- [x] No private endpoints, IP addresses, or hostnames.
- [x] No usernames.
- [x] No tokens or secrets.
- [x] No raw private source code.
- [x] No raw transcripts.
