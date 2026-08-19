# Ubuntu NVIDIA GeForce RTX 3060 12 GB mixed-task model soak power

> Generated evidence page. The canonical machine-readable record is
> `evidence-ad94c1f53c81365c` in `config/evidence-page-registry.json`.

## What this record says

Across 37,443 one-second GPU-board samples, pre-run idle averaged 13.962 W and post-run idle averaged 14.175 W; model-window averages ranged from 23.577 W to 32.876 W and observed peaks ranged from 56.54 W to 139.18 W. These readings exclude the rest of the computer and wall-power losses.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | nvidia-smi |
| Surface version | 610.43.02 |
| Provider or runtime | Ollama 0.32.14 CUDA |
| Operating system | Ubuntu 26.04 LTS |
| Model | 19-model-passed-soak-corpus |
| Operation | One Second Board Telemetry Bounded Soak Pre And Post Idle |

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
