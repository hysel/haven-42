# Local Image Provider Onboarding

`config/local-image-onboarding-contract.json` defines consumer-local image setup without requiring an external server. It is a planning and admission contract, not an installer and not evidence that untested native profiles work.

## Discovery And Selection

Discovery remains local and reports the operating system, architecture, system memory, available storage, accelerator vendor and model, usable dedicated or unified memory, and installed driver or runtime versions. Missing accelerator or memory evidence makes a profile unavailable; it must never silently select CPU execution.

Provider selection requires an exact operating-system and accelerator match. The validated Linux NVIDIA V100 ComfyUI/SDXL profile does not promote another profile. A disposable Windows 11/RX 7800 XT/ComfyUI v0.28.0 AMD portable cell passed production-adapter generation, visual, privacy, history, restart, and uninstall checks, but remains partial until cancellation, forced recovery, update/rollback, and consumer onboarding pass. See `examples/windows-amd-image-provider-validation.md`.

## Consent Boundary

Before any download or filesystem change, onboarding must show the exact provider and model revision, license, source hosts, download and temporary-storage sizes, published checksums, destination locations, hardware fit, loopback exposure, artifact retention, provider-retained copies, cleanup, rollback, and uninstall behavior. Approval is single-use and bound to those exact effects.

A candidate-only profile produces an unavailable result and setup guidance. It cannot download a runtime, model, custom node, or installer. Custom nodes and external API nodes remain disabled unless separately promoted.

## Lifecycle And Promotion

A passing provider must start on demand, bind to `127.0.0.1`, confirm the intended accelerator, stop after a bounded idle period, and keep provider state outside the replaceable Haven 42 engine. Installation, health, model checksum, generation, PNG validation, metadata, cancellation, recovery, cleanup, update, rollback, and uninstall all belong to the exact profile gate.

Remaining native validation prioritizes Windows NVIDIA and Windows Intel XPU, completion of the Windows AMD gate, and finally Apple Silicon on a physical Mac. Failed or partial profiles leave evidence only and ship no runtime or installer assets.
