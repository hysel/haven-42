# Qwen 3.5 9B Q4_K_M versus Q8_0

> Generated evidence page. The canonical machine-readable record is
> `evidence-abbec916eccdc9c2` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile only: Q4_K_M retained the bounded response, structured tool-call, and engineering-patch behavior with lower storage and accelerator memory and higher generation throughput; the disposable Q8_0 candidate was removed.

| Result | Value |
| --- | --- |
| Status | `validated-by-tests` |
| Validation method | Local Endpoint |
| Area | Model Quantization |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.1 |
| Provider or runtime | Ollama |
| Operating system | Linux |
| Model | qwen3.5:9b |
| Operation | Trusted Artifact Comparison |

## Source evidence

[examples/quantization-validation.md](https://github.com/hysel/haven-42/blob/main/examples/quantization-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
