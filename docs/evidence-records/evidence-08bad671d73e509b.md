# Qwen 3.5 9B synchronized power on Radeon RX 7800 XT

> Generated evidence page. The canonical machine-readable record is
> `evidence-08bad671d73e509b` in `config/evidence-page-registry.json`.

## What this record says

Exact 30-minute workload passed 50 of 50 cells with full GPU offload; the synchronized Adrenalin measurement met the 120-second idle-baseline floor and was admitted as exact-profile GPU-only energy evidence. Model qualification remains partial and grants no automatic model, runtime, or cost promotion.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.5 |
| Provider or runtime | Ollama |
| Operating system | Windows 11 |
| Model | qwen3.5:9b Q4_K_M |
| Operation | Chat Writing Summary Soak Energy |

## Source evidence

[examples/windows-amd-rx7800xt-power-validation.md](https://github.com/hysel/haven-42/blob/main/examples/windows-amd-rx7800xt-power-validation.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
