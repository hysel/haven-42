# Ubuntu NVIDIA GeForce RTX 3060 12 GB 19-model qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-f5989f6fc215258e` in `config/evidence-page-registry.json`.

## What this record says

All 19 exact artifacts passed three Chat, Writing, and Summarization samples with unload checks and then passed independent 30-minute soaks. This exact Ubuntu, driver, runtime, and hardware result remains separate from Windows evidence and does not change automatic defaults, runtime admission, support labels, or other platform cells.

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
| Model | digest-pinned-19-model-corpus |
| Operation | Exact Artifact Core Task Gate And 30 Minute Soak |

## Source evidence

[examples/nvidia-rtx3060-linux-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-rtx3060-linux-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
