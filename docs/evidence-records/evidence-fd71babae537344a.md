# Qwen 3.5 9B baseline MLX endpoint tool call

> Generated evidence page. The canonical machine-readable record is
> `evidence-fd71babae537344a` in `config/evidence-page-registry.json`.

## What this record says

Required function call returned valid JSON arguments on a loopback-only Apple Silicon MLX server; agent-surface behavior remains separate.

| Result | Value |
| --- | --- |
| Status | `read-only-tool-validated` |
| Validation method | Local Endpoint |
| Area | Model Tool Use |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | MLX OpenAI-compatible server |
| Surface version | 0.31.3 |
| Provider or runtime | MLX |
| Operating system | macOS |
| Model | mlx-community/Qwen3.5-9B-4bit |
| Operation | Structured Tool Call |

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
