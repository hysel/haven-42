# VSCodium Continue Agent Qwen 3.5 4B MLX strict write smoke

> Generated evidence page. The canonical machine-readable record is
> `evidence-e5ae46fbbffbcb08` in `config/evidence-page-registry.json`.

## What this record says

The agent targeted the existing disposable file but appended instead of replacing and added blank lines in two strict attempts; external Git whitespace verification failed. Do not use this model for VSCodium approved writes.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Editor Agent |
| Area | Editor Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Continue Agent |
| Surface version | not-recorded |
| Provider or runtime | MLX |
| Operating system | macOS |
| Model | mlx-community/Qwen3.5-4B-4bit |
| Operation | Scoped Write |

## Source evidence

[examples/mlx-model-validation.md](https://github.com/hysel/haven-42/blob/main/examples/mlx-model-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
