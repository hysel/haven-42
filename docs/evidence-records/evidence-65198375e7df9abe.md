# Ubuntu NVIDIA GeForce GTX 1650 Super 4 GB eight-model qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-65198375e7df9abe` in `config/evidence-page-registry.json`.

## What this record says

Five exact small-model artifacts passed three Chat, Writing, and Summarization samples with unload checks and independent 30-minute soaks. Three larger candidates stopped at the full-CUDA-residency gate. This exact profile does not change automatic defaults, runtime admission, support labels, or other 4 GB hardware cells.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama CUDA |
| Surface version | 0.32.14 |
| Provider or runtime | Ollama |
| Operating system | Ubuntu 26.04 LTS |
| Model | digest-pinned-eight-model-corpus |
| Operation | Exact Artifact Core Task Gate And 30 Minute Soak |

## Source evidence

[examples/nvidia-gtx1650-super-linux-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-gtx1650-super-linux-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
