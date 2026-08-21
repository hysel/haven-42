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
| Evidence records | 203 |
| Distinct model-field values | 81 |
| Tracked agent surfaces | 4 |

## Evidence Outcomes

| Status | Count |
| --- | ---: |
| `partial-pass` | 97 |
| `failed-validation` | 24 |
| `validated-by-tests` | 22 |
| `read-only-tool-validated` | 13 |
| `write-smoke-validated` | 13 |
| `read-only-cli-validated` | 9 |
| `static-validated` | 9 |
| `candidate-only` | 7 |
| `approved-write-ready` | 4 |
| `plan-review-candidate` | 2 |
| `plan-validated` | 2 |
| `review-validated` | 1 |

## Validation Modes

| Mode | Count |
| --- | ---: |
| Local endpoint | 83 |
| Generated sample | 58 |
| Editor agent | 14 |
| Automated tests | 8 |
| development-native | 7 |
| offline-fixture | 6 |
| physical-source-test | 5 |
| development-network | 3 |
| Static | 3 |
| browser-and-static | 2 |
| generated-sample-editor-chat | 2 |
| offline-mocked | 2 |
| physical-package-test | 2 |
| disposable-repository-agent | 1 |
| generated-sample-agent | 1 |
| live-fixed-provider | 1 |
| offline-local | 1 |
| offline-metadata | 1 |
| offline-primary-source-review | 1 |
| Online discovery | 1 |
| physical-host | 1 |

## Agent Surfaces

| Surface | Validation level | Supported | Validated | Planned | Scaffolded | Blocked |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Aider | plan-and-scoped-edit-validated | 7 | 1 | 0 | 0 | 0 |
| Continue | legacy-evidence-only | 0 | 1 | 0 | 0 | 0 |
| OpenCode | generated-sample-scoped-edit-validated | 7 | 1 | 0 | 0 | 0 |
| OpenHands | candidate | 5 | 0 | 0 | 0 | 3 |

## Install Configure Test

| Surface | Install | Configure | Test | Validation |
| --- | --- | --- | --- | --- |
| Aider | supported | supported | validated | plan-and-scoped-edit-validated |
| Continue | retired | retired | retired | legacy-evidence-only |
| OpenCode | supported | supported | validated | generated-sample-scoped-edit-validated |
| OpenHands | blocked | blocked | blocked | candidate |

## Models

| Model |
| --- |
| 14-model-passed-soak-corpus |
| 16 exact manifest-pinned model profiles |
| 16-exact-manifest-corpus |
| 17 exact manifest-pinned models |
| 19-model-passed-soak-corpus |
| Click 8.2.1 |
| Express 5.1.0 |
| OpenVINO/Qwen3-0.6B-int4-ov@f864c6106efb6c7f7b4ef274a78a98e37210dddd |
| Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Qwen3-Coder-Next:latest |
| Qwen3.5-0.8B-Q4_0-GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| SDXL Base 1.0 |
| acestep-v15-turbo |
| devstral-small-2:24b |
| devstral-small-2:latest |
| digest-pinned-19-model-corpus |
| digest-pinned-eight-model-corpus |
| exact-upstream-candidate-records |
| five exact manifest-pinned models |
| five-model-passed-soak-corpus |
| fixed-validation-item |
| gemma3:12b |
| gemma3:1b-it-q4_K_M |
| gemma4:e2b-qat |
| gemma4:e4b-qat |
| granite4.1:30b |
| granite4.1:30b-q4_K_M |
| granite41-8b-q4_K_M |
| granite4:7b-a1b-h |
| laguna-xs-2.1:q4_K_M |
| lfm2.5:8b |
| lfm2.5:8b-a1b-q4_K_M |
| llama3.2:3b-instruct-q4_K_M |
| local-config |
| minicpm-v4.6:1b |
| minicpm-v:4.6-1b-q4_K_M |
| ministral-3:3b-instruct-2512-q4_K_M |
| ministral-3:8b-instruct-2512-q4_K_M |
| ministral-3:8b-instruct-2512-q4_K_M@1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71 |
| mistral-small3.2:24b-instruct-2506-q4_K_M |
| mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit |
| mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869 |
| mlx-community/Qwen3.5-4B-4bit |
| mlx-community/Qwen3.5-9B-4bit |
| mlx-community/Qwen3.5-9B-OptiQ-4bit |
| muse-glimmer:30b |
| muse-glimmer:30b-q4_K_M |
| nemotron-3-nano-omni:33b-q4_K_M |
| nemotron-3.5-lightning:30b-a3b-q4_K_M |
| nemotron-3.5-lightning:30b-a3b-q8_0 |
| nemotron3:33b |
| nine-core-pass-exact-artifacts |
| no-loaded-model |
| no-model |
| none |
| north-mini-code-1.0:q4_K_M |
| north-mini-code:10-30b-a3b-q4_K_M |
| ornith-10:9b-q4_K_M |
| ornith:9b |
| phi4-mini:3.8b-q4_K_M |
| qwen3-coder:30b |
| qwen3.5:0.8b |
| qwen3.5:0.8b Q8_0 |
| qwen3.5:2b |
| qwen3.5:2b@324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df |
| qwen3.5:35b |
| qwen3.5:4b |
| qwen3.5:4b-q4_K_M |
| qwen3.5:4b@2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd |
| qwen3.5:9b |
| qwen3.5:9b Q4_K_M |
| qwen3.6:27b-q4_K_M |
| qwen3.6:35b-a3b-q4_K_M |
| qwen3.8:27b |
| qwen3.8:27b-q4_K_M |
| revision-and-sha256-pinned-11-model-corpus |
| revision-and-sha256-pinned-follow-on-artifacts |
| serde_json 1.0.140 |
| synthetic-bounded-source-envelope |
| three-model-passed-soak-corpus |
| unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
