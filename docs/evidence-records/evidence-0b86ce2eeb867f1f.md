# Radeon RX 5700 XT Qwen 3.5 0.8B Windows llama.cpp paced-soak power

> Generated evidence page. The canonical machine-readable record is
> `evidence-0b86ce2eeb867f1f` in `config/evidence-page-registry.json`.

## What this record says

Across 898 samples during the paced 30-minute soak, software-reported GPU ASIC power averaged 23.322 W time-weighted, integrated to 11.666022 Wh, and reached 168 W; post-soak idle averaged 6.322 W, conditional GPU-active samples averaged 113.633 W, hotspot reached 65 C, and memory junction reached 54 C. This is not wall power or necessarily total board input, the exact logger version was not independently captured, and the observed two-second interval may miss short peaks.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Power Evidence |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | HWiNFO64 sensor logger |
| Surface version | version-not-independently-captured |
| Provider or runtime | llama.cpp b10375 Vulkan AMD proprietary 26.7.1 |
| Operating system | Windows 10.0.26200.8973 |
| Model | Qwen 3.5 0.8B Q4_0 GGUF@57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf |
| Operation | Idle Paced Soak Conditional Active Peak Energy Thermals |

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
