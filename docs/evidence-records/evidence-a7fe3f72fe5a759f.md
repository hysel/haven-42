# macOS Keychain native hosted availability

> Generated evidence page. The canonical machine-readable record is
> `evidence-a7fe3f72fe5a759f` in `config/evidence-page-registry.json`.

## What this record says

The exact source probe and contract passed the platform-gated `/usr/bin/security help` availability cell in the PR 91 macOS smoke job while every Keychain-operation and admission flag remained false; physical Mac, package parity, item lifecycle, runtime, UI, database, and production authority remain open.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Automated Tests |
| Area | Data Protection |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | Haven 42 development availability probe |
| Surface version | 1 |
| Provider or runtime | Apple Keychain Services candidate |
| Operating system | GitHub-hosted macOS 15 |
| Model | none |
| Operation | System Tool Presence |

## Source evidence

[examples/macos-keychain-availability-boundary.md](https://github.com/hysel/haven-42/blob/main/examples/macos-keychain-availability-boundary.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
