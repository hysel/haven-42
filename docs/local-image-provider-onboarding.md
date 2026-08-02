# Local Image Provider Onboarding

`config/local-image-onboarding-contract.json` defines consumer-local image setup without requiring an external server. It is a planning and admission contract, not an installer and not evidence that untested native profiles work.

## Setup Choices

Image generation follows the product-wide `config/progressive-onboarding-contract.json` pattern:

1. **Set it up for me** selects only an exact promoted native profile and offers structured advanced controls for storage, checkpoint, quality/VRAM preset, generation defaults, concurrency, idle shutdown, retention, and admitted update behavior.
2. **Connect or use my existing setup** validates a user-managed local or explicitly trusted remote provider and offers advanced endpoint, credential-reference, timeout, model-mapping, workflow, cleanup, TLS, and generation-default controls without silently changing that provider.
3. **Not now** keeps image generation honestly unavailable without blocking chat, software, or other capabilities.

Both active paths show whether the resulting setup is `validated`, `customized`, `unverified`, or `blocked`. Advanced changes trigger state reevaluation and cannot enable arbitrary commands, custom nodes, external API nodes, public binding, or silent fallback.

## Discovery And Selection

Discovery remains local and reports the operating system, architecture, system memory, available storage, accelerator vendor and model, usable dedicated or unified memory, and installed driver or runtime versions. Missing accelerator or memory evidence makes a profile unavailable; it must never silently select CPU execution.

Provider selection requires an exact operating-system and accelerator match. The validated Linux NVIDIA V100 ComfyUI/SDXL profile does not promote another profile. A disposable Windows 11/Quadro RTX 5000/ComfyUI v0.29.2 NVIDIA portable cell passed integrity, CUDA, hardened loopback startup, production-adapter generation, PNG inspection, repeated-run stability, invalid-workflow recovery, active cancellation, exact-process forced recovery, retention cleanup, and secure shutdown. It remains partial because real update/rollback, consumer onboarding, idle lifecycle, uninstall, package parity, and redistribution review are open. See `examples/windows-nvidia-image-provider-validation.md`.

Disposable Windows 11/RX 7800 XT/ComfyUI v0.28.0 AMD portable cells pass production-adapter generation, visual, privacy, history, repeated-run stability, active cancellation, invalid-workflow recovery, forced process recovery, retention cleanup, restart, and uninstall. That profile also remains partial because a genuine immutable update/rollback transition and consumer onboarding/installer behavior remain unadmitted. See `examples/windows-amd-image-provider-validation.md`.

## Consent Boundary

Before any download or filesystem change, onboarding must show the exact provider and model revision, license, source hosts, download and temporary-storage sizes, published checksums, destination locations, hardware fit, loopback exposure, artifact retention, provider-retained copies, cleanup, rollback, and uninstall behavior. Approval is single-use and bound to those exact effects.

A candidate-only profile produces an unavailable result and setup guidance. It cannot download a runtime, model, custom node, or installer. Custom nodes and external API nodes remain disabled unless separately promoted.

## Lifecycle And Promotion

A passing provider must start on demand, bind to `127.0.0.1`, confirm the intended accelerator, stop after a bounded idle period, and keep provider state outside the replaceable Haven 42 engine. Installation, health, model checksum, generation, PNG validation, metadata, cancellation, recovery, cleanup, update, rollback, and uninstall all belong to the exact profile gate.

`config/local-image-lifecycle-contract.json` and
`scripts/simulate-local-image-lifecycle.py` now provide an effect-free
consumer lifecycle planner for those gates. It accepts only an exact
`tested-passed` profile, strict artifact identities and digests, complete
compatibility/evidence booleans, an idle or interrupted journal shape, and
explicit retention choices. It rejects candidate-only profiles, including the
partial Windows AMD cell, as well as raw paths, URLs, commands, arguments,
environment values, credentials, secrets, approvals, artifact replay, unsafe
health, and incomplete recovery state. Install, update, failed-health rollback,
explicit rollback, interrupted recovery, retention, and uninstall outputs are
plans only: every network, download, filesystem, process, activation, rollback,
uninstall, user-data, and approval effect remains false. Synthetic artifacts
are never counted as provider evidence.

Remaining native validation prioritizes the open lifecycle gates for Windows
NVIDIA and Windows AMD plus an exact Windows Intel XPU cell. Physical Apple
Silicon remains parked until suitable hardware is available and does not block
continued Windows or Linux development. Failed or partial profiles leave
evidence only and ship no runtime or installer assets.
