# Qwen 3.5 4B VS Code Continue controlled editor retest with Python extension

> Generated evidence page. The canonical machine-readable record is
> `evidence-bcc43e041506855b` in `config/evidence-page-registry.json`.

## What this record says

From a clean baseline with the Python extension already installed, Continue read both files but reported its edit tool unavailable, offered manual code, and incorrectly claimed modification; external Git found zero tracked changes, so Python tooling did not resolve the editor write failure.

| Result | Value |
| --- | --- |
| Status | `failed-validation` |
| Validation method | Editor Agent |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | VS Code-compatible + Continue |
| Surface version | 1.127.0 + 2.1.0 + Python 2026.4.0 |
| Provider or runtime | Ollama 0.32.13 |
| Operating system | Windows editor and Ubuntu 26.04 AMD Radeon RX 5700 XT model host |
| Model | qwen3.5:4b |
| Operation | Exact File Read Edit Tool Availability External Diff |

## Source evidence

[examples/august-2026-coding-agent-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/august-2026-coding-agent-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
