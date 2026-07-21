# Local Engineering Agent Pack

The Local Engineering Agent Pack is evolving into an evidence-gated, local-first AI workbench for software engineering and general-purpose tasks on Windows, Linux, and macOS. The current name reflects its origin; a deliberate product rename is under consideration.

Today, the maintained engineering surfaces are Continue, Aider, and OpenCode. Repository-optional local chat, writing, and summarization have a validated Ollama adapter, and local image generation has a validated Linux ComfyUI/SDXL path. The local web UI is planned, native desktop image profiles remain evidence-gated, and music/video generation remains roadmap-only. OpenHands is documentation-only while its isolated validation boundary remains unimplemented.

Failed or retired integrations do not ship scripts, harnesses, wrappers, configuration, workflows, or active catalog entries. Fixture-backed cross-platform contracts do not broaden native runtime or hardware claims.

## Start Here

- New users: [[Quick Start|Quick-Start]]
- Choose a workflow: [[Agent Pack Menu|Agent-Pack-Menu]]
- Select a local model: [[Local Model Selection|Local-Model-Selection]]
- Compare supported agents: [[Agent Surface Options|Agent-Surface-Options]]
- Understand the pass-before-ship rule: [[Agent Integration Admission Policy|Agent-Integration-Admission-Policy]]
- Review current plans: [[Roadmap|Roadmap]]
- Review local image support: [[Local Image Capability|Local-Image-Capability]]
- Install the validated Linux image provider: [[ComfyUI Image Provider Setup|ComfyUI-Image-Provider-Setup]]
- Prepare a release: [[Release Guidance|Release-Guidance]]

## Current Roadmap

- Milestone 22 — planned local web UI and task composition.
- Milestone 23 — native local image generation in progress; Linux ComfyUI/SDXL validated.
- Milestone 24 — local music/audio research only.
- Milestone 25 — local video research only.

## Support Model

Every agent integration is evaluated outside the shipped pack first. It enters the repository only after its exact software version passes installation, configuration, health, read-only, planning, write-smoke, scoped-edit, cleanup, sanitization, and cross-platform promotion gates. A failed evaluation produces only a concise sanitized decision record.

Model and tool behavior remains specific to the agent surface, model, operating system, and runtime. Always begin read-only and independently verify approved writes with Git and the target repository's own tests.

## Current Release

The current release line is `0.3.0`. Work after that release remains under `Unreleased` until a new version is deliberately prepared and exact-SHA hosted CI succeeds.

The repository is available at [hysel/local-engineering-agent-pack](https://github.com/hysel/local-engineering-agent-pack).
