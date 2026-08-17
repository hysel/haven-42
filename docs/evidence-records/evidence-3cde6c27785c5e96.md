# Nemotron 3.5 Lightning Q4 on Ollama 0.32.13 dual Tesla V100

> Generated evidence page. The canonical machine-readable record is
> `evidence-3cde6c27785c5e96` in `config/evidence-page-registry.json`.

## What this record says

The exact artifact passed the required core gate at a measured output rate of 78.317 per second on the exact dual-V100 review profile; additional capability evidence and license review remain incomplete, so no support label or automatic promotion is admitted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.13 |
| Provider or runtime | Ollama CUDA |
| Operating system | Ubuntu 24.04.4 |
| Model | nemotron-3.5-lightning:30b-a3b-q4_K_M |
| Operation | Chat Writing Summary Soak |

## Source evidence

[examples/august-2026-new-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/august-2026-new-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
