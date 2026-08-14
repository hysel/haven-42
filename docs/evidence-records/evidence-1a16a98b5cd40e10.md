# llama.cpp HIP through WSL2 DXG on Radeon RX 7800 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-1a16a98b5cd40e10` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile candidate evidence: all 11 artifacts passed identity, HIP/DXG detection, fixed benchmark, full model-layer GPU offload, bounded exit, and cleanup; the same four passed the bounded exact-output gate. This does not establish native Linux AMD support or grant runtime, provider, model, package, or production admission.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp CLI |
| Surface version | b10088 |
| Provider or runtime | direct process |
| Operating system | WSL2 Ubuntu |
| Model | revision-and-sha256-pinned-11-model-corpus |
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
