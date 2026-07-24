# Haven 42

**Your private, local AI station.**

Haven 42 is an evidence-gated, local-first AI workbench for software engineering and general-purpose tasks on Windows, Linux, and macOS. Product-specific paths, commands, packages, and documentation use the Haven 42 identity consistently.

Today, the maintained engineering surfaces are Continue, Aider, and OpenCode. The runnable local web application begins with keyboard-accessible Guided setup, Connect existing setup, and Explore paths. Guided setup performs an explicit bounded read-only hardware/software scan and builds a disabled, zero-effect setup plan; it does not install software. The chat-first workspace then provides pinned navigation, compact provider/system setup, automatically classified local/LAN Ollama connection, evidence-gated model choices for chat/writing/summarization, advanced manual overrides, typed no-file-written results, read-only provider-health/evidence/update status, and bounded idle/lifecycle cleanup on Windows, Linux, and macOS. Unknown installed models remain unverified, missing recommendations never trigger an automatic download, Software remains visibly not admitted, and Images remains visibly provider-profile-required. Local image generation has a validated Linux ComfyUI/SDXL path but is not yet admitted to the web UI. Native desktop image profiles remain evidence-gated, and music/video candidates remain documentation-only.

Failed or retired integrations do not ship scripts, harnesses, wrappers, configuration, workflows, or active catalog entries. Fixture-backed cross-platform contracts do not broaden native runtime or hardware claims.

## Start Here

- New users: [[Quick Start|Quick-Start]]
- Run the local browser assistant and first-run wizard: [[Local Web MVP|Local-Web-MVP]]
- Choose a workflow: [[Haven 42 Menu|Haven-42-Menu]]
- Select a local model: [[Local Model Selection|Local-Model-Selection]]
- Review writing-model candidates and promotion gates: [[Writing Model Evaluation|Writing-Model-Evaluation]]
- Discover candidates across Ollama and Hugging Face: [[Online Model Discovery|Online-Model-Discovery]]
- Assemble security-aware beginner and advanced model choices: [[Security-Aware Model Catalog|Security-Aware-Model-Catalog]]
- Compare supported agents: [[Agent Surface Options|Agent-Surface-Options]]
- Understand the pass-before-ship rule: [[Agent Integration Admission Policy|Agent-Integration-Admission-Policy]]
- Review current plans: [[Roadmap|Roadmap]]
- Review local image support: [[Local Image Capability|Local-Image-Capability]]
- Install the validated Linux image provider: [[ComfyUI Image Provider Setup|ComfyUI-Image-Provider-Setup]]
- Review consumer-local image onboarding: [[Local Image Provider Onboarding|Local-Image-Provider-Onboarding]]
- Review advanced onboarding security: [[Onboarding Setting Security|Onboarding-Setting-Security]]
- Review audio candidates and consent: [[Local Audio Provider Candidates|Local-Audio-Provider-Candidates]] and [[Generative Media Consent Policy|Generative-Media-Consent-Policy]]
- Review video candidates: [[Local Video Provider Candidates|Local-Video-Provider-Candidates]]
- Plan hardware-adaptive quantization: [[Hardware-Adaptive Quantization|Hardware-Adaptive-Quantization]]
- Review quantization validation evidence: [[Quantization Validation|Quantization-Validation]]
- Understand engine/backend selection: [[Inference Engine Architecture|Inference-Engine-Architecture]]
- Review exact engine evidence: [[Inference Engine Validation|Inference-Engine-Validation]]
- Prepare a release: [[Release Guidance|Release-Guidance]]
- Choose Fast, Integration, or Full validation: [[Test Tiers|Test-Tiers]]
- Review desktop storage, update, and rollback boundaries: [[Desktop Storage And Updates|Desktop-Storage-And-Updates]]

## Current Roadmap

- Milestone 22 — 22A local web chat is runnable; broader capabilities and 22B optional Tauri packaging remain in progress and independently gated.
- Milestone 23 — native local image generation in progress; Linux ComfyUI/SDXL validated.
- Milestone 24 — immutable audio candidate inventory and consent policy complete; live evaluation open.
- Milestone 25 — immutable video candidate inventory and consent policy complete; live evaluation open.
- Milestone 26 — exact Linux NVIDIA and Windows AMD Ollama comparisons passed; llama.cpp CUDA passed on Linux NVIDIA and HIP passed on Windows AMD, Vulkan failed the patch gate, Intel is parked pending hardware, and broader cells remain open.

## Support Model

Every agent integration is evaluated outside the shipped pack first. It enters the repository only after its exact software version passes installation, configuration, health, read-only, planning, write-smoke, scoped-edit, cleanup, sanitization, and cross-platform promotion gates. A failed evaluation produces only a concise sanitized decision record.

Model and tool behavior remains specific to the agent surface, model, operating system, and runtime. Always begin read-only and independently verify approved writes with Git and the target repository's own tests.

## Current Release

The current release line is `0.3.0`. Work after that release remains under `Unreleased` until a new version is deliberately prepared and exact-SHA hosted CI succeeds.

The repository is available at [hysel/haven-42](https://github.com/hysel/haven-42).

## Security

Provider endpoints are trust-scoped and bounded, mutable automated installers are blocked, CI actions are commit-pinned, and vulnerabilities should be reported privately through the repository security policy. See `docs/provider-endpoint-security.md`.
