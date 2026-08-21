# Apple M4 16 GB LFM2.5 GGUF bounded qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-0ef74d64cf30f4b8` in `config/evidence-page-registry.json`.

## What this record says

Both exact official GGUF files passed checksum, authenticated loopback, full Metal offload, and unload checks. The 1.2B candidate failed chat, summarization, and the planned structured-code execution gate; its generated code was AST-validated but never executed. The 2.6B candidate failed writing, summarization, and structured code. Neither entered a soak or earned a recommendation, and LFM license review remains open.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp server |
| Surface version | b10520 |
| Provider or runtime | llama.cpp Metal |
| Operating system | macOS 26.6.2 |
| Model | LFM2.5-1.2B-and-2.6B-Q4_K_M-exact-GGUFs |
| Operation | Chat Writing Summary Structured Tool Structured Code Metal Offload Unload |

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
