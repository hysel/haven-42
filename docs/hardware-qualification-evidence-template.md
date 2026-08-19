# Hardware qualification evidence template

Use this page only after the machine-readable result is complete. During a run,
keep the result in local review and say plainly that it is unfinished.

## What was tested

- Accelerator and usable memory:
- Operating system and kernel:
- Driver and compute backend:
- System memory:
- Runtime, exact version, artifact digest, and admission status:
- Qualification profile and pinned model inventory:

## What passed

Summarize the task gates and 30-minute soaks in ordinary language. Link to the
machine-readable result instead of duplicating every field.

## What did not pass

List every failed, blocked, and not-run cell. Include the exact failure cell and
do not infer support from another operating system, runtime, editor, or GPU.

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

Describe common passes and divergences. Never carry a Windows result over to
Linux, or a result from one driver/runtime version to another untested cell.

## Limits and decision

- Evidence status:
- Known limitations:
- Automatic default/support changes: **not allowed by this evidence alone**
- Owner decision required:

## Privacy

Confirm that the published evidence contains no host name, address, user name,
machine identifier, credential, key, or raw prompt/response content.
