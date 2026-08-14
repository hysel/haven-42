# llama.cpp CUDA on Quadro RTX 5000

> Generated evidence page. The canonical machine-readable record is
> `evidence-599dbc1e05b646b6` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile engine evidence: source-built CUDA passed isolated-device discovery, fixed benchmark, bounded response, required tool call, Git-applicable patch, cleanup, and service-preservation checks; agent-surface and consumer-installer readiness are not claimed.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp server |
| Surface version | b10088 |
| Provider or runtime | OpenAI-compatible loopback API |
| Operating system | Linux |
| Model | unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| Operation | Backend Validation |

## Source evidence

[examples/inference-engine-validation.md](https://github.com/hysel/haven-42/blob/main/examples/inference-engine-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
