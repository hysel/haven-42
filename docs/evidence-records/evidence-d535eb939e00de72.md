# llama.cpp Windows NVIDIA and AMD follow-on matrix

> Generated evidence page. The canonical machine-readable record is
> `evidence-d535eb939e00de72` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile candidate evidence: CUDA and HIP passed full-offload lifecycle, Gemma vision, and independent direct Qwen 3.5 9B structured tool-call cells; patch outcomes differed for Qwen 3.5, and Qwen 3 8B failed context and patch quality on both. Tool arguments remain untrusted and no execution, runtime, provider, model, UI, package, or production promotion is granted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp CLI and server |
| Surface version | b10088 |
| Provider or runtime | direct process |
| Operating system | Windows |
| Model | revision-and-sha256-pinned-follow-on-artifacts |
| Operation | Backend Validation |

## Source evidence

[examples/cross-accelerator-model-validation.md](https://github.com/hysel/haven-42/blob/main/examples/cross-accelerator-model-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
