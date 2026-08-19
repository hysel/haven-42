# Qwen 3.5 4B coding workflow on Radeon RX 5700 XT 8 GiB

> Generated evidence page. The canonical machine-readable record is
> `evidence-93e8cb104f42daa6` in `config/evidence-page-registry.json`.

## What this record says

All generated-repository coding workflow gates passed with the exact 3.14 GB artifact fully resident in 8 GiB GPU memory; the separate bounded coding-reliability result is recorded independently, while human review, editor surfaces, and automatic admission remain blocked.

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
| Operation | Api Read Review Write Scoped Edit Full Gpu Residency |

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
