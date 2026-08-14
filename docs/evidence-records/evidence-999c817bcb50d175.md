# Nemotron 3.5 Lightning Q4 on dual Tesla V100

> Generated evidence page. The canonical machine-readable record is
> `evidence-999c817bcb50d175` in `config/evidence-page-registry.json`.

## What this record says

Exact manifest passed 81 task samples across nine cycles, a 30-minute soak, reported GPU residency, and a separate exact GPU-board energy measurement; tools, thinking, recovery, bounded-context checks, package lifecycle, and automatic admission remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.9 |
| Provider or runtime | Ollama |
| Operating system | Ubuntu 24.04.4 |
| Model | nemotron-3.5-lightning:30b-a3b-q4_K_M |
| Operation | Chat Writing Summary Soak Energy |

## Source evidence

[examples/nvidia-v100-nemotron-validation.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-v100-nemotron-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
