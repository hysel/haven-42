# Apple M4 16 GB idle Apple SoC sample

> Generated evidence page. The canonical machine-readable record is
> `evidence-cea92a2e0ac35bf8` in `config/evidence-page-registry.json`.

## What this record says

Ten samples reported 0.052 W CPU average, 0.002 W GPU average, 0.054 W combined CPU/GPU/ANE average, 0.481 percent GPU-active residency, and nominal thermal pressure. Background processes and display state were not controlled; this is not wall or whole-system power.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Host |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Apple powermetrics |
| Surface version | macOS 26.6.2 |
| Provider or runtime | Ollama 0.32.15 Metal |
| Operating system | macOS 26.6.2 |
| Model | no-loaded-model |
| Operation | Ten Sample Idle Apple Soc Power Gpu Residency Thermal Pressure |

## Source evidence

[examples/apple-m4-16gib-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/apple-m4-16gib-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
