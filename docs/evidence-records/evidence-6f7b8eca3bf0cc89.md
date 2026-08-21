# Apple M4 16 GB official llama.cpp b10520 distribution boundary

> Generated evidence page. The canonical machine-readable record is
> `evidence-6f7b8eca3bf0cc89` in `config/evidence-page-registry.json`.

## What this record says

The exact official arm64 archive passed release-size and SHA-256 checks, bounded safe extraction, fresh-folder relocation, native launch, and launch without a package manager or system Python. The executable is ad-hoc signed, not proven notarized, and rejected by Gatekeeper; no runtime, package, support, default, or release admission was granted.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Physical Package Test |
| Area | Inference Engine |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | llama.cpp macOS arm64 archive |
| Surface version | b10520 |
| Provider or runtime | llama.cpp Metal |
| Operating system | macOS 26.6.2 |
| Model | none |
| Operation | Official Digest Safe Extraction Relocation Native Launch Platform Trust |

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
