# Evidence Dashboard

The Evidence Dashboard answers a narrow question: **what has Haven 42 actually
validated, for which surface, provider, model, operating system, operation, and
validation mode?**

It is generated from three committed, sanitized sources:

- `config/evidence-catalog.tsv`
- `config/agent-surface-capabilities.json`
- `config/agent-surface-solutions.json`

The current committed snapshot contains 79 evidence records, 18 distinct
non-empty model-field values, and four tracked agent surfaces. These are
evidence counts, not usage statistics, quality rankings, or production
readiness claims.

## Current Snapshot

Snapshot date: 2026-07-27

| Metric | Count |
| --- | ---: |
| Evidence records | 79 |
| Distinct model-field values | 18 |
| Tracked agent surfaces | 4 |
| Supported agent surfaces | 3 |
| Candidate agent surfaces | 1 |

## Evidence Outcomes

Every record uses a conservative status from Capability Evidence Contract v2.
The count is the number of exact catalog rows carrying that status.

| Outcome | Count | What it proves |
| --- | ---: | --- |
| `validated-by-tests` | 19 | Repository tests enforce the recorded behavior. |
| `partial-pass` | 14 | Useful evidence exists, but a recorded limitation or follow-up remains. |
| `write-smoke-validated` | 13 | A minimal disposable-repository write passed external file/Git verification; broad approved-write readiness is not claimed. |
| `read-only-tool-validated` | 11 | Read-only tool use passed for the exact recorded surface and environment. |
| `read-only-cli-validated` | 9 | CLI/context validation passed; editor Agent behavior is not implied. |
| `approved-write-ready` | 4 | A scoped write passed and was independently verified outside the agent surface. |
| `candidate-only` | 2 | The item is recorded for consideration but is not validated for local tool use. |
| `plan-review-candidate` | 2 | Generated-sample planning or review may be useful; write readiness is not established. |
| `plan-validated` | 2 | The exact capability key produced an evidence-based plan without writing files. |
| `static-validated` | 2 | Static file or script checks passed without model execution. |
| `review-validated` | 1 | The exact capability key completed the recorded review operation. |

The totals above add to all 79 committed records. A higher count does not make
one model or surface “better”; it means more distinct evidence rows exist.

## Validation Areas

| Area | Records |
| --- | ---: |
| Model tool use | 25 |
| Agent surface | 14 |
| General capability | 10 |
| Language workflow matrix | 6 |
| Editor surface | 4 |
| Multi-language workflow | 4 |
| Inference engine | 2 |
| Installer profile | 2 |
| Language rule pack | 2 |
| Media provider | 2 |
| Model quantization | 2 |
| Sample repository | 2 |
| Hardware recommendation | 1 |
| Model provider | 1 |
| Online discovery | 1 |
| Remote profile | 1 |

## How Validation Ran

| Validation mode | Records | Interpretation |
| --- | ---: | --- |
| Generated sample | 38 | Ran against a disposable generated repository or bounded fixture. It does not establish real-repository readiness. |
| Local endpoint | 21 | Exercised a locally controlled provider endpoint for the exact recorded profile. |
| Editor Agent | 9 | Ran through the recorded editor Agent surface. |
| Automated tests | 7 | Deterministic repository tests enforce the boundary. |
| Static | 3 | Inspected contracts or scripts without model/provider execution. |
| Online discovery | 1 | Discovered a candidate only; it does not promote or install the candidate. |

## Operations Covered

| Operation | Records | Operation | Records |
| --- | ---: | --- | ---: |
| Read file | 12 | Scoped write | 9 |
| Write smoke | 9 | Workflow suite | 6 |
| Structured tool call | 4 | Test harness | 4 |
| Writing constraint screen | 4 | Backend validation | 2 |
| Image generation | 2 | Repository discovery | 2 |
| Repository list | 2 | Rule validation | 2 |
| Trusted artifact comparison | 2 | Workflow review | 2 |
| Code review | 1 | Config recommendation | 1 |
| General chat | 1 | General summarization | 1 |
| General writing | 1 | Hardware profile | 1 |
| Implementation plan | 1 | Install approved-write | 1 |
| Install read-only | 1 | Instrumental generation | 1 |
| Intent routing | 1 | Model discovery | 1 |
| Plan | 1 | Provider conformance | 1 |
| Provider discovery | 1 | Read and write | 1 |
| Read workflows | 1 |  |  |

An operation proves only itself. For example, `read-file` evidence cannot be
used as `scoped-write` evidence, and `general-chat` cannot be treated as
`general-writing`.

## Agent Surface Readiness

| Surface | Type | Tier | Current validation level | Supported activities | Validated activities | Blocked activities | Install | Configure | Test |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| Continue | Editor and CLI | Supported | `approved-write-ready` | 7 | 1 | 0 | Supported | Supported | Validated |
| Aider | CLI agent | Supported | `plan-and-scoped-edit-validated` | 7 | 1 | 0 | Supported | Supported | Validated |
| OpenCode | CLI agent | Supported | `generated-sample-scoped-edit-validated` | 7 | 1 | 0 | Supported | Supported | Validated |
| OpenHands | Platform agent | Candidate | `candidate` | 5 | 0 | 3 | Blocked | Blocked | Blocked |

### Continue

- Installation uses project-local or shared Continue assets with dry-run and
  backup support.
- Configuration is generated locally from hardware-aware model
  recommendations.
- Testing combines local-model checks, Continue CLI validation, runtime
  validation, and deterministic output verification.
- `approved-write-ready` remains specific to the recorded versions, models,
  providers, operating systems, operations, and validation modes.

### Aider

- Installation is routed through the unified surface adapter with explicit
  dry-run support.
- Local-only Ollama configuration disables automatic commits.
- The shared CLI harness has Aider-specific read, plan, write-smoke, and
  constrained scoped-edit evidence.
- This does not automatically establish approved writes against arbitrary
  non-generated repositories.

### OpenCode

- A local-only Ollama configuration and explicit npm install plan are
  available.
- Generated-sample read, write-smoke, and constrained scoped-edit validation
  passed for the recorded Devstral Small 2 24B profile.
- Non-generated-repository validation remains pending, so the evidence must
  not be presented as general approved-write readiness.

### OpenHands

OpenHands remains candidate-only and excluded from default setup:

- Installation is blocked because platform-style agents introduce different
  workspace, sandbox, and credential boundaries.
- Configuration is blocked pending explicit platform and workspace policy.
- Testing is blocked until a rootless isolated runtime, bounded workspace
  mounts, a credential-free provider path, and deny-by-default network policy
  are implemented and validated.

For the exact user-facing install, configuration, test solutions, evidence
paths, and blocked reasons behind this summary, see
[Agent Surface Solutions](Agent-Surface-Solutions)
(`docs/agent-surface-solutions.md`).

## Evidence Records By Surface

This table counts catalog records using each execution surface. Similar names
remain separate because the surface boundary matters.

| Execution surface | Records |
| --- | ---: |
| Continue CLI | 29 |
| Continue Agent | 9 |
| Local text capability adapter | 8 |
| Aider CLI | 7 |
| MLX OpenAI-compatible server | 4 |
| OpenCode CLI | 4 |
| Pack scripts | 3 |
| Installer scripts | 2 |
| Local image capability adapter | 2 |
| Ollama | 2 |
| Static validation | 2 |
| llama.cpp server | 2 |
| ACE-Step REST API | 1 |
| Agent CLI surfaces | 1 |
| Capability availability discovery | 1 |
| LLM intent routing | 1 |
| OpenCode | 1 |

## Model-Field Inventory

The following values currently appear in the catalog's model field:

- `qwen3.5:9b`
- `qwen3.5:35b`
- `qwen3-coder:30b`
- `Qwen3-Coder-Next:latest`
- `gemma3:12b`
- `granite4:7b-a1b-h`
- `mistral-small3.2:24b-instruct-2506-q4_K_M`
- `devstral-small-2:24b`
- `devstral-small-2:latest`
- `laguna-xs-2.1:q4_K_M`
- `mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit`
- `mlx-community/Qwen3.5-4B-4bit`
- `mlx-community/Qwen3.5-9B-4bit`
- `mlx-community/Qwen3.5-9B-OptiQ-4bit`
- `unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5`
- `SDXL Base 1.0`
- `acestep-v15-turbo`
- `local-config`

This is an inventory, not a recommended-model list. Some values describe a
provider artifact or configuration lane rather than a generally selectable
chat model. Each value must be evaluated through its complete evidence key.

## How To Read An Exact Evidence Claim

Capability Evidence Contract v2 keys every record by:

1. surface;
2. surface version;
3. provider;
4. model;
5. operating system;
6. operation; and
7. validation mode.

All seven fields must match before evidence can drive a recommendation. The
catalog uses the most conservative status when duplicate records share a
complete key and retains all distinct evidence paths.

Examples of invalid inference:

- Continue evidence does not transfer to Aider or OpenCode.
- Windows evidence does not transfer to Linux or macOS.
- Generated-sample success does not establish success on a real repository.
- CLI validation does not prove editor Agent behavior.
- Read-only success does not authorize a write.
- One provider revision does not promote another revision or quantization.
- A fixture-backed cross-platform contract does not prove untested native
  hardware behavior.

For exact row fields and maintenance rules, see
[Evidence Catalog](Evidence-Catalog) and
[Capability Evidence Contract](Capability-Evidence-Contract).

## Generate A Fresh Local Dashboard

Windows PowerShell:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/generate-evidence-dashboard.ps1 `
  -OutputPath runtime-validation-output/evidence-dashboard.json `
  -MarkdownOutputPath runtime-validation-output/evidence-dashboard.md `
  -AsJson
```

Linux:

```bash
./scripts/generate-evidence-dashboard.linux.sh \
  --output-path runtime-validation-output/evidence-dashboard.json \
  --markdown-output-path runtime-validation-output/evidence-dashboard.md \
  --as-json
```

macOS:

```bash
./scripts/generate-evidence-dashboard.macos.sh \
  --output-path runtime-validation-output/evidence-dashboard.json \
  --markdown-output-path runtime-validation-output/evidence-dashboard.md \
  --as-json
```

All wrappers delegate to `scripts/evidence_dashboard.py`, so Windows, Linux,
macOS, the source web application, and the portable package use one validation
and aggregation implementation.

The generator is read-only except for explicitly requested output files.
Generated output belongs in ignored local directories such as
`runtime-validation-output/`.

## Browser Page Versus Full Dashboard

The browser's advanced **Evidence** page intentionally presents a bounded
subset:

- total record and model-field counts;
- complete outcome distribution;
- per-surface supported, validated, and blocked activity counts;
- install/configure/test status; and
- one fixed explicit-click link to this detailed wiki page.

The browser page excludes raw catalog notes, evidence paths, machine paths,
provider endpoints, and raw validation output. Loading it reads no user
repository, contacts no provider, starts no process, writes no file, and makes
no production-readiness claim. The wiki link is never fetched in the
background and opens with no opener or referrer authority.
