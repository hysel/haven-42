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

Provider selection requires an exact operating-system and accelerator match. The validated Linux NVIDIA V100 ComfyUI/SDXL profile does not promote another profile. Disposable Windows 11/RX 7800 XT/ComfyUI v0.28.0 AMD portable cells now pass production-adapter generation, visual, privacy, history, repeated-run stability, active cancellation, invalid-workflow recovery, forced process recovery, retention cleanup, restart, and uninstall. The profile remains partial because v0.28.0 is still the latest immutable AMD release, so a real update/rollback transition cannot yet be tested, and consumer onboarding/installer behavior remains unadmitted. See `examples/windows-amd-image-provider-validation.md`.

## Consent Boundary

Before any download or filesystem change, onboarding must show the exact provider and model revision, license, source hosts, download and temporary-storage sizes, published checksums, destination locations, hardware fit, loopback exposure, artifact retention, provider-retained copies, cleanup, rollback, and uninstall behavior. Approval is single-use and bound to those exact effects.

A candidate-only profile produces an unavailable result and setup guidance. It cannot download a runtime, model, custom node, or installer. Custom nodes and external API nodes remain disabled unless separately promoted.

## Lifecycle And Promotion

A passing provider must start on demand, bind to `127.0.0.1`, confirm the intended accelerator, stop after a bounded idle period, and keep provider state outside the replaceable Haven 42 engine. Installation, health, model checksum, generation, PNG validation, metadata, cancellation, recovery, cleanup, update, rollback, and uninstall all belong to the exact profile gate.

Remaining native validation prioritizes Windows NVIDIA and Windows Intel XPU, completion of the Windows AMD gate, and finally Apple Silicon on a physical Mac. Failed or partial profiles leave evidence only and ship no runtime or installer assets.
