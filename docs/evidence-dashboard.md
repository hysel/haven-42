# Evidence Dashboard

This committed, sanitized snapshot summarizes what Haven 42 has actually
validated. Counts are evidence inventory, not usage statistics, quality
rankings, or production-readiness claims.

Generated from `config/evidence-catalog.tsv`,
`config/agent-surface-capabilities.json`, and
`config/agent-surface-solutions.json`.

See [Evidence Catalog](Evidence-Catalog),
[Capability Evidence Contract](Capability-Evidence-Contract), and
`docs/agent-surface-solutions.md` for detailed evidence boundaries.

## Current Snapshot

| Metric | Count |
| --- | ---: |
| Evidence records | 83 |
| Distinct model-field values | 21 |
| Tracked agent surfaces | 4 |

## Evidence Outcomes

| Status | Count |
| --- | ---: |
| `validated-by-tests` | 19 |
| `partial-pass` | 18 |
| `write-smoke-validated` | 13 |
| `read-only-tool-validated` | 11 |
| `read-only-cli-validated` | 9 |
| `approved-write-ready` | 4 |
| `candidate-only` | 2 |
| `plan-review-candidate` | 2 |
| `plan-validated` | 2 |
| `static-validated` | 2 |
| `review-validated` | 1 |

## Validation Modes

| Mode | Count |
| --- | ---: |
| Generated sample | 38 |
| Local endpoint | 25 |
| Editor agent | 9 |
| Automated tests | 7 |
| Static | 3 |
| Online discovery | 1 |

## Agent Surfaces

| Surface | Validation level | Supported | Validated | Planned | Scaffolded | Blocked |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Aider | plan-and-scoped-edit-validated | 7 | 1 | 0 | 0 | 0 |
| Continue | approved-write-ready | 7 | 1 | 0 | 0 | 0 |
| OpenCode | generated-sample-scoped-edit-validated | 7 | 1 | 0 | 0 | 0 |
| OpenHands | candidate | 5 | 0 | 0 | 0 | 3 |

## Install Configure Test

| Surface | Install | Configure | Test | Validation |
| --- | --- | --- | --- | --- |
| Aider | supported | supported | validated | plan-and-scoped-edit-validated |
| Continue | supported | supported | validated | approved-write-ready |
| OpenCode | supported | supported | validated | generated-sample-scoped-edit-validated |
| OpenHands | blocked | blocked | blocked | candidate |

## Models

| Model |
| --- |
| OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd |
| Qwen3-Coder-Next:latest |
| SDXL Base 1.0 |
| acestep-v15-turbo |
| devstral-small-2:24b |
| devstral-small-2:latest |
| gemma3:12b |
| granite4:7b-a1b-h |
| laguna-xs-2.1:q4_K_M |
| local-config |
| mistral-small3.2:24b-instruct-2506-q4_K_M |
| mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit |
| mlx-community/Qwen3.5-4B-4bit |
| mlx-community/Qwen3.5-9B-4bit |
| mlx-community/Qwen3.5-9B-OptiQ-4bit |
| qwen3-coder:30b |
| qwen3.5:35b |
| qwen3.5:9b |
| revision-and-sha256-pinned-11-model-corpus |
| revision-and-sha256-pinned-follow-on-artifacts |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
