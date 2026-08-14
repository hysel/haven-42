# llama.cpp SYCL on Intel Arc B580

> Generated evidence page. The canonical machine-readable record is
> `evidence-a43711f9d74d1e5f` in `config/evidence-page-registry.json`.

## What this record says

Exact-profile candidate evidence: text, vision, prompt pressure, tool call, bounded-reasoning patch, adapter, and cleanup cells passed, but 3 of 53 upstream tests failed; no runtime or package admission is granted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp server |
| Surface version | 5f55650a |
| Provider or runtime | OpenAI-compatible loopback API |
| Operating system | Linux |
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
