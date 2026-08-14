# Alpha 2 managed lifecycle on Pop OS 24.04

> Generated evidence page. The canonical machine-readable record is
> `evidence-f15751caa49c9951` in `config/evidence-page-registry.json`.

## What this record says

The corrected system identity path passed fresh setup, exact identity, GPU inference, normal shutdown, process and port closure, zero-download reuse, and marker-owned uninstall; packaged repetition remains open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Managed Lifecycle |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 source candidate |
| Surface version | 0.4.0-alpha.2 |
| Provider or runtime | Ollama 0.32.5 CUDA |
| Operating system | Pop OS 24.04 LTS |
| Model | qwen3.5:0.8b Q8_0 |
| Operation | Setup Inference Reuse Uninstall |

## Source evidence

[docs/linux-managed-lifecycle-validation.md](https://github.com/hysel/haven-42/blob/main/docs/linux-managed-lifecycle-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
