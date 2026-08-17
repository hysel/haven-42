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
| Evidence records | 149 |
| Distinct model-field values | 54 |
| Tracked agent surfaces | 4 |

## Evidence Outcomes

| Status | Count |
| --- | ---: |
| `partial-pass` | 64 |
| `validated-by-tests` | 21 |
| `write-smoke-validated` | 13 |
| `read-only-tool-validated` | 11 |
| `read-only-cli-validated` | 9 |
| `static-validated` | 9 |
| `candidate-only` | 7 |
| `failed-validation` | 6 |
| `approved-write-ready` | 4 |
| `plan-review-candidate` | 2 |
| `plan-validated` | 2 |
| `review-validated` | 1 |

## Validation Modes

| Mode | Count |
| --- | ---: |
| Local endpoint | 66 |
| Generated sample | 38 |
| Editor agent | 9 |
| Automated tests | 8 |
| development-native | 7 |
| offline-fixture | 6 |
| development-network | 3 |
| Static | 3 |
| browser-and-static | 2 |
| offline-mocked | 2 |
| live-fixed-provider | 1 |
| offline-local | 1 |
| offline-metadata | 1 |
| offline-primary-source-review | 1 |
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
| 16 exact manifest-pinned model profiles |
| 17 exact manifest-pinned models |
| Click 8.2.1 |
| Express 5.1.0 |
| OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd |
| Qwen3-Coder-Next:latest |
| SDXL Base 1.0 |
| acestep-v15-turbo |
| devstral-small-2:24b |
| devstral-small-2:latest |
| exact-upstream-candidate-records |
| five exact manifest-pinned models |
| gemma3:12b |
| gemma3:1b-it-q4_K_M |
| gemma4:e2b-qat |
| gemma4:e4b-qat |
| granite4.1:30b-q4_K_M |
| granite41-8b-q4_K_M |
| granite4:7b-a1b-h |
| laguna-xs-2.1:q4_K_M |
| lfm2.5:8b-a1b-q4_K_M |
| llama3.2:3b-instruct-q4_K_M |
| local-config |
| minicpm-v:4.6-1b-q4_K_M |
| ministral-3:3b-instruct-2512-q4_K_M |
| ministral-3:8b-instruct-2512-q4_K_M |
| mistral-small3.2:24b-instruct-2506-q4_K_M |
| mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit |
| mlx-community/Qwen3.5-4B-4bit |
| mlx-community/Qwen3.5-9B-4bit |
| mlx-community/Qwen3.5-9B-OptiQ-4bit |
| muse-glimmer:30b-q4_K_M |
| nemotron-3-nano-omni:33b-q4_K_M |
| nemotron-3.5-lightning:30b-a3b-q4_K_M |
| nemotron-3.5-lightning:30b-a3b-q8_0 |
| no-model |
| none |
| north-mini-code:10-30b-a3b-q4_K_M |
| ornith-10:9b-q4_K_M |
| phi4-mini:3.8b-q4_K_M |
| qwen3-coder:30b |
| qwen3.5:0.8b Q8_0 |
| qwen3.5:35b |
| qwen3.5:4b-q4_K_M |
| qwen3.5:9b |
| qwen3.5:9b Q4_K_M |
| qwen3.6:27b-q4_K_M |
| qwen3.6:35b-a3b-q4_K_M |
| qwen3.8:27b-q4_K_M |
| revision-and-sha256-pinned-11-model-corpus |
| revision-and-sha256-pinned-follow-on-artifacts |
| serde_json 1.0.140 |
| synthetic-bounded-source-envelope |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
