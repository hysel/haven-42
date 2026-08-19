# NVIDIA GeForce RTX 3060 12 GB 19-model qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-7f16789ca3e3811c` in `config/evidence-page-registry.json`.

## What this record says

All 19 artifacts passed exact identity checks; 14 passed Chat, Writing, and Summarization and then passed independent 30-minute soaks, while five stopped at explicit task-contract failures. This exact driver/runtime/hardware evidence does not change automatic defaults, runtime admission, support labels, or other platform cells.

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
| Model | digest-pinned-19-model-corpus |
| Operation | Exact Artifact Core Task Gate And 30 Minute Soak |

## Source evidence

[examples/nvidia-rtx3060-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-rtx3060-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
