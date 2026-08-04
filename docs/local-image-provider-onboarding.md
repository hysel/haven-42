# Local Image Provider Onboarding

`config/local-image-onboarding-contract.json` defines consumer-local image setup without requiring an external server. It is a planning and admission contract, not an installer and not evidence that untested native profiles work.

## Distribution boundary

Haven 42 packages do not contain ComfyUI, another provider engine, provider
models or checkpoints, GPU drivers or accelerator runtimes, provider
installers, or provider updater payloads. Users connect an existing compatible
provider that they acquired separately. A future guided flow may identify and
validate an official upstream artifact, but it must not treat discovery,
download guidance, or an audit as authority to bundle, install, or update it.

This boundary does not prohibit reviewed libraries required for Haven 42 itself
from being included in its portable runtime. Those dependencies remain subject
to Haven's package inventory, notices, SBOM, integrity, and security gates.

The exact Windows candidate records now live in
`config/local-image-candidate-profiles.json`. They pin the reviewed AMD,
NVIDIA, and Intel hardware cells to immutable provider archive identities and
one immutable SDXL checkpoint. The records deliberately remain
`partial-pass-unpromoted`; they cannot authorize downloads, installation,
runtime activation, CPU fallback, or evidence inheritance between operating
systems or accelerators.

## Setup Choices

Image generation follows the product-wide `config/progressive-onboarding-contract.json` pattern:

1. **Set it up for me** selects only an exact promoted native profile and offers structured advanced controls for storage, checkpoint, quality/VRAM preset, generation defaults, concurrency, idle shutdown, retention, and admitted update behavior.
2. **Connect or use my existing setup** validates a user-managed local or explicitly trusted remote provider and offers advanced endpoint, credential-reference, timeout, model-mapping, workflow, cleanup, TLS, and generation-default controls without silently changing that provider.
3. **Not now** keeps image generation honestly unavailable without blocking chat, software, or other capabilities.

Both active paths show whether the resulting setup is `validated`, `customized`, `unverified`, or `blocked`. Advanced changes trigger state reevaluation and cannot enable arbitrary commands, custom nodes, external API nodes, public binding, or silent fallback.

## Discovery And Selection

Discovery remains local and reports the operating system, architecture, system memory, available storage, accelerator vendor and model, usable dedicated or unified memory, and installed driver or runtime versions. Missing accelerator or memory evidence makes a profile unavailable; it must never silently select CPU execution.

Provider selection requires an exact operating-system and accelerator match. The validated Linux NVIDIA V100 ComfyUI/SDXL profile does not promote another profile. A disposable Windows 11/Quadro RTX 5000 profile passed the core v0.29.2 gates plus an exact v0.30.0 side-by-side update and rollback to the untouched baseline. Consumer onboarding, automatic idle shutdown, uninstall, package parity, and redistribution review remain open. See `examples/windows-nvidia-image-provider-validation.md`.

Disposable Windows 11/RX 7800 XT cells pass the ComfyUI v0.28.0 core and uninstall gates plus an exact v0.30.0 side-by-side update and rollback. The exact v0.30.0 runtime license inventory is now recorded but remains blocked by unresolved metadata, duplicate-distribution, and native-component findings. Consumer onboarding, automatic idle shutdown, package parity, redistribution approval, and promotion remain unadmitted. See `examples/windows-amd-image-provider-validation.md` and `docs/local-image-runtime-license-review.md`.

A disposable Windows 11/Intel Arc B580 cell passed the exact v0.29.2 and
v0.30.0 XPU transition gates. It remains unpromoted for the same onboarding,
idle-shutdown, package-parity, redistribution, and product-integration gaps.
See `examples/windows-intel-image-provider-validation.md`.

## Consent Boundary

Before any future user-managed acquisition guidance or filesystem change is admitted, onboarding must show the exact provider and model revision, license, source hosts, download and temporary-storage sizes, published checksums, destination locations, hardware fit, loopback exposure, artifact retention, provider-retained copies, cleanup, rollback, and uninstall behavior. Approval is single-use and bound to those exact effects. The current product grants no such effect authority.

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

The current dependency and redistribution boundary is tracked in [Local Image
Runtime License And Redistribution Review](local-image-runtime-license-review.md).

The local dummy-provider test exercises loopback-only on-demand startup,
occupied-port rejection, bounded request timeouts, cancellation, crash
recovery, stale process-identity rejection, exact-process shutdown, idle
shutdown, and exact-file cleanup without installing or contacting ComfyUI.
This is lifecycle implementation evidence only; it does not replace a native
candidate-profile gate.
Its offline inventory is fail-closed and does not grant shipping authority.

The later native source/package runs are defined in [Local Image Native
Validation Packet](local-image-native-validation-packet.md). The parity
contract is intentionally absent from the shipping resource allowlist.

Remaining native validation prioritizes source/package parity, automatic idle
shutdown, redistribution review, and consumer onboarding for the exact Windows
AMD, NVIDIA, and Intel cells. Physical Apple Silicon remains parked until
suitable hardware is available and does not block continued Windows or Linux
development. Failed or partial profiles leave evidence only and ship no
runtime or installer assets.
