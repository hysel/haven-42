# Ubuntu 26.04 NVIDIA GeForce RTX 5050 8 GB five-model inference qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-1319a87ecf24fbe1` in `config/evidence-page-registry.json`.

## What this record says

Five exact artifacts passed 738 Chat, Writing, and Summarization responses with per-sample unload checks on driver 610.43.02. Windows combines original and resumed runs; the original 9B duration is wall-clock reconstructed and original final cleanup unverified. Ubuntu managed package setup did not complete. Coding-agent and interactive package gates are not-run; no automatic default or support change. Power limitations are explicit in the report.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Hardware Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama CUDA |
| Surface version | 0.32.14 |
| Provider or runtime | Ollama |
| Operating system | Ubuntu 26.04 |
| Model | digest-pinned-five-model-corpus |
| Operation | Core Task Gate And 30 Minute Repeated Load Soak |

## Source evidence

[examples/nvidia-rtx5050-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-rtx5050-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
