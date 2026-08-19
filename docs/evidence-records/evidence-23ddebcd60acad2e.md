# Gemma 3 1B coding workflow screen

> Generated evidence page. The canonical machine-readable record is
> `evidence-23ddebcd60acad2e` in `config/evidence-page-registry.json`.

## What this record says

API, read, review, approved write, and scoped edit all failed on the generated fixture; no coding-agent admission is allowed.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Generated Sample |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Continue CLI |
| Surface version | 1.5.47 |
| Provider or runtime | Ollama 0.32.13 |
| Operating system | Windows controller and Ubuntu 24.04.4 CUDA model host |
| Model | gemma3:1b-it-q4_K_M |
| Operation | Api Read Review Write Scoped Edit |

## Source evidence

[examples/august-2026-coding-agent-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/august-2026-coding-agent-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
