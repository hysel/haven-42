# OpenCode 1.18.11 19-model disposable-repository screen on RTX 3060

> Generated evidence page. The canonical machine-readable record is
> `evidence-7148c5d475b46ccd` in `config/evidence-page-registry.json`.

## What this record says

Granite 4.1 8B Q4 passed repository read, approved write, scoped edit, external Git-diff, unintended-write, and unload checks; every other model missed at least one required workflow gate. Granite remains a candidate because its remaining policy gates and separate editor surfaces are incomplete, and cross-surface inheritance is forbidden.

| Result | Value |
| --- | --- |
| Status | `partial-pass` |
| Validation method | Generated Sample Agent |
| Area | Agent Surface |

## Tested scope

| Scope | Tested value |
| --- | --- |
| Surface | OpenCode CLI |
| Surface version | 1.18.11 |
| Provider or runtime | Ollama 0.32.14 |
| Operating system | Windows 11 |
| Model | digest-pinned-19-model-corpus |
| Operation | Repository Read Approved Write Scoped Edit External Diff Unload |

## Source evidence

[examples/nvidia-rtx3060-model-qualification.md](https://github.com/hysel/haven-42/blob/main/examples/nvidia-rtx3060-model-qualification.md)

## Boundary of this result

This result applies only to the exact scope above. It must not be inherited by
another operating system, model, provider, surface, version, operation, or
validation method without separate evidence.

## Future update use

This record can inform a future compatibility check. It does not authorize an
automatic download, installation, model-default change, runtime change, or
promotion. Those actions require their own signed metadata, compatibility
checks, user policy, health checks, and rollback gates.
