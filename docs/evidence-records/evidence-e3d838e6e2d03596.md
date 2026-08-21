# Apple M4 16 GB MLX-LM lifecycle

> Generated evidence page. The canonical machine-readable record is
> `evidence-e3d838e6e2d03596` in `config/evidence-page-registry.json`.

## What this record says

The pinned wheelhouse and model passed native Metal generation, timeout recovery, and process cleanup. Production server, authenticated boundary, self-contained package, coding surface, runtime admission, and automatic selection remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Source Test |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | MLX-LM direct inference |
| Surface version | 0.31.3 |
| Provider or runtime | MLX 0.32.1 Metal |
| Operating system | macOS 26.6.2 |
| Model | mlx-community/Qwen3.5-0.8B-OptiQ-4bit@ef605869 |
| Operation | Offline Pinned Generation Metal Memory Timeout Recovery Process Cleanup |

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
