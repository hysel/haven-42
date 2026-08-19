# Qwen 3.5 4B coding reliability soak on Radeon RX 5700 XT 8 GiB

> Generated evidence page. The canonical machine-readable record is
> `evidence-492ea3ff6c97b8c5` in `config/evidence-page-registry.json`.

## What this record says

A 30.2-minute run passed 26 complete coding workflows, three transport cancellation recoveries, 29 full-residency checks, and 30 unload checks; internal application cancellation, the remaining reliability scenarios, human review, editor surfaces, and automatic admission remain blocked.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Generated Sample |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Continue CLI |
| Surface version | 1.5.47 |
| Provider or runtime | Ollama 0.32.13 |
| Operating system | Windows controller and Ubuntu 26.04 AMD Radeon RX 5700 XT model host |
| Model | qwen3.5:4b |
| Operation | 26 Read Review Write Scoped Edit Workflows Cancellation Recovery Residency Unload |

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
