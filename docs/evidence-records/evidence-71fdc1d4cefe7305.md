# Apple M4 16 GB 16-model bounded qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-71fdc1d4cefe7305` in `config/evidence-page-registry.json`.

## What this record says

Nine of 16 exact artifacts passed all five bounded endpoint gates with full Metal residency and per-cell unload; seven exact failures remain visible. This exact core result does not grant an automatic recommendation, default, support label, or another-profile claim.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama Metal |
| Surface version | 0.32.15 |
| Provider or runtime | Ollama |
| Operating system | macOS 26.6.2 |
| Model | 16-exact-manifest-corpus |
| Operation | Chat Writing Summary Structured Tool Structured Code Metal Residency Unload |

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
