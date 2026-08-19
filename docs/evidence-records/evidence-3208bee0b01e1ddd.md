# Qwen 3.5 4B VS Code Continue explicit two-file retest on Radeon RX 5700 XT 8 GiB

> Generated evidence page. The canonical machine-readable record is
> `evidence-3208bee0b01e1ddd` in `config/evidence-page-registry.json`.

## What this record says

Continue read both explicitly attached approved files, reported two unavailable edit-tool attempts, changed neither approved file, and wrote the requested test function into the explicitly out-of-scope app/settings.py file. External Git detected the unintended write; this surface must not be recommended for approved multi-file edits.

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
| Operation | Explicit Two File Read Edit Tool External Diff Unintended Write |

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
