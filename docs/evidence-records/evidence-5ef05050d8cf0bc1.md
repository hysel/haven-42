# Windows AMD Radeon RX 6800 16 GB nineteen-model qualification

> Generated evidence page. The canonical machine-readable record is
> `evidence-5ef05050d8cf0bc1` in `config/evidence-page-registry.json`.

## What this record says

All 19 exact artifacts passed Chat, Writing, and Summarization and then passed independent 30-minute soaks on this exact RX 6800 Windows profile. Filtered HWiNFO GPU ASIC telemetry is aggregate-only; the raw file is excluded and represented only by SHA-256 and size. Driver version, per-model power, wall power, coding surfaces, automatic defaults, and support changes remain out of scope.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Hardware Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama ROCm |
| Surface version | 0.32.14 |
| Provider or runtime | Ollama |
| Operating system | Windows 11 |
| Model | digest-pinned-nineteen-model-corpus |
| Operation | Exact Artifact Core Task Gate 30 Minute Soak And Filtered Power Summary |

## Source evidence

[examples/amd-rx6800-windows-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/amd-rx6800-windows-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
