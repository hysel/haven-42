# Roadmap

_A concise product roadmap. Detailed implementation history remains available separately._

## Current position

Haven 42 is unsigned development software with a runnable browser interface and
one-folder portable packages for Windows, Linux, and macOS. The current admitted
product includes private conversation, bounded attachments, explicit Ollama
connections, model selection, token and timing details, and a promoted Linux
ComfyUI/SDXL image path.

Security-sensitive capabilities remain unavailable until their own evidence and
approval gates are complete. Haven 42 makes no production-readiness claim.

## In progress

- Improve the unified conversation and attachment experience.
- Expand cross-platform package and hardware validation.
- Complete safe local document-context foundations without executing uploads.
- Advance optional encrypted conversation-history architecture without enabling
  persistence prematurely.
- Expand image-provider evidence while keeping unverified profiles unavailable.
- Continue hardware-aware model and inference-engine validation.

## Planned, but not active

- PDF, Office, and OpenDocument attachment parsing in a restricted worker.
- User-controlled persistent conversation history and retained attachment context.
- Controlled web research with bounded retrieval and citations.
- Additional local image, audio, and video providers.
- Offline installer and updater execution after signing, verification, rollback,
  and machine-effect gates are satisfied.

## Parked or externally blocked

- Apple hardware-specific validation where physical hardware is unavailable.
- Signing and notarization until provider, identity, dependency, and release gates
  are complete.
- Public production releases and active online updates.
- Tauri/Rust packaging, which remains unadmitted.

## Milestone map

| Area | Position |
| --- | --- |
| Core pack and engineering workflows | Completed for their defined development scopes |
| Browser product and portable packaging | Runnable development scope; continuing hardening |
| Local images | Linux ComfyUI/SDXL path promoted; other profiles gated |
| Audio and video | Research and evidence only |
| Hardware-adaptive inference | Evidence expanding across NVIDIA, AMD, Intel, and future Apple hardware; WSL2 AMD remains candidate-only |
| Local knowledge and history | Bounded attachments admitted; parsing, retrieval, and persistence gated |
| Controlled web research | Security contracts exist; runtime access unadmitted |

Read [[Project Information|Project-Information]] for the product boundary and
[[Engineering Roadmap|Engineering-Roadmap]] for the complete milestone history,
exit criteria, and implementation record.
