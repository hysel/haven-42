# Windows NVIDIA GeForce GTX 1650 Super 4 GB eight-model qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-a31a3f4055c25ef1` in `config/evidence-page-registry.json`.

## What this record says

Three exact small-model artifacts passed three Chat, Writing, and Summarization samples with unload checks and independent 30-minute soaks. Five larger candidates stopped at the full-CUDA-residency gate. This exact Windows profile may filter visible model choices but does not change an automatic default, runtime admission, support label, or another 4 GB hardware cell.

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
| Operating system | Windows 11 |
| Model | digest-pinned-eight-model-corpus |
| Operation | Exact Artifact Core Task Gate And 30 Minute Soak |

## Source evidence

[examples/nvidia-gtx1650-super-windows-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-gtx1650-super-windows-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
