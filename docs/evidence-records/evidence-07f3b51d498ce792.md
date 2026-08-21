# Apple M4 16 GB Gemma 4 12B OpenCode coding screen

> Generated evidence page. The canonical machine-readable record is
> `evidence-07f3b51d498ce792` in `config/evidence-page-registry.json`.

## What this record says

The deterministic API code and tool contracts passed, as did explicit write approval, forced-timeout handling, and unload. Repository read, planning, review, scoped-edit, external-diff, bounded-context, and post-failure-recovery requirements did not all pass, so the model is not eligible for a coding recommendation from this surface.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Disposable Repository Agent |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | OpenCode CLI |
| Surface version | 1.18.19 |
| Provider or runtime | Ollama 0.32.15 Metal |
| Operating system | macOS 26.6.2 |
| Model | gemma4:12b-it-qat@38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 |
| Operation | Structured Code Read Plan Review Scoped Write Tool Timeout Recovery Unload Unintended Write |

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
