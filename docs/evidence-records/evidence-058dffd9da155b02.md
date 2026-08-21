# Apple M4 16 GB Gemma 4 12B QAT bounded addendum

> Generated evidence page. The canonical machine-readable record is
> `evidence-058dffd9da155b02` in `config/evidence-page-registry.json`.

## What this record says

The exact Gemma 4 12B QAT artifact passed all five bounded endpoint gates with full Metal residency and per-cell unload at an average 14.323 generated units per second. This one-model addendum grants no automatic recommendation, default, support label, runtime change, or another-profile claim.

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
| Model | gemma4:12b-it-qat@38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 |
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
