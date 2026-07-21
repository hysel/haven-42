# Local Engineering Agent Pack

The Local Engineering Agent Pack provides local-first, evidence-gated workflows for software engineering agents on Windows, Linux, and macOS.

The maintained agent surfaces are Continue, Aider, and OpenCode. OpenHands is documentation-only while its isolated validation boundary remains unimplemented. Failed or retired integrations do not ship scripts, harnesses, wrappers, configuration, workflows, or active catalog entries.

## Start Here

- New users: [[Quick Start|Quick-Start]]
- Choose a workflow: [[Agent Pack Menu|Agent-Pack-Menu]]
- Select a local model: [[Local Model Selection|Local-Model-Selection]]
- Compare supported agents: [[Agent Surface Options|Agent-Surface-Options]]
- Understand the pass-before-ship rule: [[Agent Integration Admission Policy|Agent-Integration-Admission-Policy]]
- Review current plans: [[Roadmap|Roadmap]]
- Prepare a release: [[Release Guidance|Release-Guidance]]

## Support Model

Every agent integration is evaluated outside the shipped pack first. It enters the repository only after its exact software version passes installation, configuration, health, read-only, planning, write-smoke, scoped-edit, cleanup, sanitization, and cross-platform promotion gates. A failed evaluation produces only a concise sanitized decision record.

Model and tool behavior remains specific to the agent surface, model, operating system, and runtime. Always begin read-only and independently verify approved writes with Git and the target repository's own tests.

## Current Release

The current release line is `0.3.0`. Work after that release remains under `Unreleased` until a new version is deliberately prepared and exact-SHA hosted CI succeeds.

The repository is available at [hysel/local-engineering-agent-pack](https://github.com/hysel/local-engineering-agent-pack).
