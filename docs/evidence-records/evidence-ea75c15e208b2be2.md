# Apple M4 16 GB LFM2.5 OpenCode coding screen

> Generated evidence page. The canonical machine-readable record is
> `evidence-ea75c15e208b2be2` in `config/evidence-page-registry.json`.

## What this record says

Both exact candidates timed out at the bounded 150-second read-only repository gate. No files changed, unload passed, missing gates remain visible, and neither model is eligible for a coding recommendation from this surface.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Disposable Repository Agent |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | OpenCode CLI |
| Surface version | 1.18.19 |
| Provider or runtime | llama.cpp b10520 Metal |
| Operating system | macOS 26.6.2 |
| Model | LFM2.5-1.2B-and-2.6B-Q4_K_M-exact-GGUFs |
| Operation | Read Plan Review Scoped Write Tool Timeout Recovery Unload Unintended Write |

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
