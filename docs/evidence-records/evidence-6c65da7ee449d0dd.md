# Apple M4 16 GB llama.cpp lifecycle

> Generated evidence page. The canonical machine-readable record is
> `evidence-6c65da7ee449d0dd` in `config/evidence-page-registry.json`.

## What this record says

The exact binary and GGUF passed full-layer Metal offload, authenticated loopback inference, timeout recovery, restart, and listener cleanup. Trusted distribution, self-contained packaging, maintained coding surface, runtime admission, and automatic selection remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Source Test |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp server |
| Surface version | cd644c395 |
| Provider or runtime | llama.cpp Metal |
| Operating system | macOS 26.6.2 |
| Model | Qwen3.5-0.8B-Q4_0-GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Operation | Full Layer Offload Authenticated Loopback Inference Timeout Recovery Restart Cleanup |

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
