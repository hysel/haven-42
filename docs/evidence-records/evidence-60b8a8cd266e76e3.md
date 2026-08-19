# Ubuntu NVIDIA GeForce GTX 1650 Super 4 GB mixed-task model soak power

> Generated evidence page. The canonical machine-readable record is
> `evidence-60b8a8cd266e76e3` in `config/evidence-page-registry.json`.

## What this record says

Across 9,879 one-second GPU-board samples, pre-run idle averaged 8.360 W and post-run idle averaged 8.203 W; model-window averages ranged from 12.585 W to 16.208 W and observed peaks ranged from 48.88 W to 103.74 W. These readings exclude the rest of the computer and wall-power losses.

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
| Model | five-model-passed-soak-corpus |
| Operation | One Second Board Telemetry Bounded Soak Pre And Post Idle |

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
