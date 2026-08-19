# NVIDIA GeForce RTX 3060 12 GB mixed-task model soak power

> Generated evidence page. The canonical machine-readable record is
> `evidence-58d8481eef7a394b` in `config/evidence-page-registry.json`.

## What this record says

Across 39,327 one-second samples, the five-minute pre/post idle baseline averaged 22.116 W; model-window averages ranged from 25.36 W to 33.54 W and observed peaks ranged from 51.53 W to 140.06 W. The paced safety soak unloads between requests, and these GPU-board readings exclude CPU, memory, storage, cooling, display, PSU losses, and wall power.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | nvidia-smi |
| Surface version | 610.88 |
| Provider or runtime | Ollama 0.32.14 CUDA |
| Operating system | Windows 11 |
| Model | 14-model-passed-soak-corpus |
| Operation | One Second Board Telemetry Bounded Soak Idle Baseline |

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
