# Hardware qualification evidence template

Use this template only after completing the machine-readable result. While a
run is active, keep its result in local review and label it unfinished.

## What was tested

- Accelerator and usable memory:
- Operating system and kernel:
- Driver and compute backend:
- System memory:
- Runtime, exact version, artifact digest, and admission status:
- Qualification profile and pinned model inventory:

## What passed

Summarize the task gates and 30-minute soaks in plain language. Link to the
machine-readable result rather than duplicating every field.

## What did not pass

List every failed, blocked, and not-run cell. Name the exact failure cell. Do
not infer support from another operating system, runtime, editor, or GPU.

## Coding-agent evidence

Record the surface and version separately. Include repository read, planning,
review, filename fidelity, scoped edit, structured tool use, bounded context,
timeout recovery, unload, and unintended-write checks. A chat response or code
benchmark is not coding-agent evidence.

## Power evidence

State whether power is GPU-board-only or whole-system. Include sample count,
idle and task scope, average and peak power, and known omissions. Do not present
GPU telemetry as an electricity-bill measurement.

## Cross-platform comparison

Describe common passes and differences. Never carry a Windows result over to
Linux or apply one driver/runtime result to another untested cell.

## Limits and decision

- Evidence status:
- Known limitations:
- Automatic default/support changes: **not allowed by this evidence alone**
- Owner decision required:

## Privacy

Confirm that the published evidence contains no host name, address, user name,
machine identifier, credential, key, or raw prompt/response content.
