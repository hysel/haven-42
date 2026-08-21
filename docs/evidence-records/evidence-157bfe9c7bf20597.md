# Apple M4 16 GB Qwen 3.5 2B bounded power sample

> Generated evidence page. The canonical machine-readable record is
> `evidence-157bfe9c7bf20597` in `config/evidence-page-registry.json`.

## What this record says

Ten samples reported 0.916 W CPU average, 8.804 W GPU average, 9.720 W combined CPU/GPU/ANE average, 97.776 percent GPU-active residency, nominal thermal pressure, unload, and temporary-model removal. This is not wall or whole-system power.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Apple powermetrics |
| Surface version | macOS 26.6.2 |
| Provider or runtime | Ollama 0.32.15 Metal |
| Operating system | macOS 26.6.2 |
| Model | qwen3.5:2b@324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df |
| Operation | 596 Unit Generation Apple Soc Power Metal Residency Thermal Pressure Unload |

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
