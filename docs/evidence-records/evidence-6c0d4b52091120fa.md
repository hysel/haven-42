# Qwen 3.6 35B-A3B Q4 on dual Tesla V100

> Generated evidence page. The canonical machine-readable record is
> `evidence-6c0d4b52091120fa` in `config/evidence-page-registry.json`.

## What this record says

The exact artifact passed the required core gate and bounded soak at a measured output rate of 82.668 per second with accelerator residency on the exact dual-V100 review profile; smaller hardware, package lifecycle, broader capabilities, energy, human-quality review, and automatic admission remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.13 |
| Provider or runtime | Ollama CUDA |
| Operating system | Ubuntu 24.04.4 |
| Model | qwen3.6:35b-a3b-q4_K_M |
| Operation | Chat Writing Summary Soak Residency |

## Source evidence

[examples/august-2026-new-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/august-2026-new-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
