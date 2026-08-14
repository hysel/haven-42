# llama.cpp SYCL on Intel Arc B580

> Generated evidence page. The canonical machine-readable record is
> `evidence-3d02244dab060bc7` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile negative evidence: verified runtime/model preflight and device enumeration passed, but zero-free-memory reporting, tensor-load failure, and an OpenCL fallback fast-fail blocked inference; cleanup passed and no runtime or package admission is granted.

| Result | Value |
| --- | --- |
| Status | `candidate-only` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp completion and benchmark |
| Surface version | b10088 |
| Provider or runtime | direct process |
| Operating system | Windows |
| Model | unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5 |
| Operation | Backend Validation |

## Source evidence

[examples/intel-b580-inference-engine-validation.md](https://github.com/hysel/haven-42/blob/main/examples/intel-b580-inference-engine-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
