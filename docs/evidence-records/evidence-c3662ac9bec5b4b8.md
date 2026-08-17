# MiniCPM V 4.6 1B Q4 on Radeon RX 5700 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-c3662ac9bec5b4b8` in `config/evidence-page-registry.json`.

## What this record says

Full GPU residency and failure recovery passed, but the required general-chat contract and the separately requested vision grounding contract failed; no soak or automatic promotion is admitted.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.13 |
| Provider or runtime | Ollama Vulkan RADV |
| Operating system | Ubuntu 26.04 LTS |
| Model | minicpm-v:4.6-1b-q4_K_M |
| Operation | Chat Vision Recovery Residency |

## Source evidence

[examples/amd-rx5700xt-ollama03213-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/amd-rx5700xt-ollama03213-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
