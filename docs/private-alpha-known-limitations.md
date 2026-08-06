# Private alpha known limitations

These limitations are mandatory disclosures for the published, unsigned Haven
42 `0.4.0-alpha.1` Windows prerelease.

- Artifacts are unsigned and not notarized. Operating-system reputation or
  antivirus warnings may appear.
- The release page provides hashed runtime license and third-party-notice files
  as separate downloads, but Alpha 1's application ZIP does not contain those
  documents. The next package builder embeds them; the published Alpha archive
  remains immutable.
- The package has no installer, automatic updater, system service, or
  privileged setup. Its optional guided path writes a pinned standalone Ollama
  runtime and recommended model inside `Haven42-Data` in the extracted package
  folder after explicit approval; neither is bundled.
- Drivers and TLS gateways are separately acquired. Haven 42 never installs or
  changes drivers, Windows Update, services, firewall rules, certificate trust,
  firmware, or system runtimes.
- Same-device Ollama may use HTTP loopback. Authenticated private-network
  connections require an already trusted HTTPS endpoint.
- Provider settings, API keys, prompts, messages, attachments, and responses
  are memory-only in the admitted browser runtime. Conversation persistence is
  not active.
- File context is limited to the admitted bounded UTF-8 text/source formats
  and PNG screenshots. PDF, Office, OpenDocument, folders, OCR, embeddings,
  and persistent libraries are not admitted.
- Alpha 1 exposes Chat, Writing, and Summarization in one text workspace.
  Images, software workflows, audio, video, research, persistence, and online
  updates remain server-blocked.
- Managed model setup is currently evidence-approved only for the pinned Qwen
  3.5 9B Q4 artifact on the tested Windows Intel Vulkan, AMD ROCm, and NVIDIA
  CUDA paths. An earlier candidate has exact managed reuse evidence on all
  three paths. The published Alpha adds portable-storage, managed-process
  lifecycle, component-progress, and cleanup hardening changes and still
  requires fresh external-hardware validation.
  Other catalog tiers are visible as hardware-fit candidates
  with manual instructions but cannot be downloaded or run automatically by
  Haven.
- Linux and macOS are outside this Alpha even though development packages have
  separate evidence.
- GPU utilization uses NVIDIA telemetry when available and otherwise uses
  Windows vendor-neutral GPU performance counters. The first baseline sample
  or a system without usable counters may briefly or persistently report
  `Unavailable`; values are never estimated.
- Tauri/Rust, signing, notarization, stable or production promotion, and
  production readiness remain unadmitted.

Any future candidate must freeze this page at its exact revision and add newly
known issues before distribution. A tester report does not silently widen
support.
