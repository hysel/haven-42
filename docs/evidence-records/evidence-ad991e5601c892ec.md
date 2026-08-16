# Radeon RX 7800 XT 17-model Ollama 0.32.9 recertification

> Generated evidence page. The canonical machine-readable record is
> `evidence-ad991e5601c892ec` in `config/evidence-page-registry.json`.

## What this record says

Fourteen exact artifacts completed 30-minute Chat, Writing, and Summarization soaks with full ROCm offload; Granite 4 7B and Ministral 3 3B/8B failed the mandatory Summarization control before soak. The sanitized result does not independently attest firmware or driver identity and grants no automatic promotion.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Local Endpoint |
| Area | Model Qualification |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Ollama |
| Surface version | 0.32.9 |
| Provider or runtime | Ollama |
| Operating system | Windows 11 |
| Model | 17 exact manifest-pinned models |
| Operation | Chat Writing Summary Soak |

## Source evidence

[examples/windows-amd-rx7800xt-ollama0329-recertification.md](https://github.com/hysel/haven-42/blob/main/examples/windows-amd-rx7800xt-ollama0329-recertification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
