# Coding Tools for Local Models

_Last reviewed: August 22, 2026._

The Haven 42 chat app does not need an editor extension or coding agent. This
page covers the separate, source-only **Haven 42 Local LLM IDE Tools** helper
for people who want to use a local Ollama model in a coding tool.

## Current surface status

| Surface | Haven 42 status | Practical meaning |
| --- | --- | --- |
| Aider | Candidate setup helper | Preview-first source helper; qualification remains model- and version-specific |
| OpenCode | Candidate setup helper | Preview-first source helper; qualification remains model- and version-specific |
| VS Code native Chat with the official Ollama extension | Evidence collected on exact model/version cells | Read, review, write, and agent capabilities must be qualified separately |
| Continue | Legacy evidence only | No new configuration, packaging, automation, repair, or recommendation work |

Do not infer coding-agent support from a chat response or a coding benchmark.
Haven 42 requires repository read, planning, review, scoped write, exact
filename fidelity, tool use, timeout recovery, and unintended-write checks in
the exact maintained surface before describing a model as suitable for coding.

The source package contains one small setup helper for Aider and OpenCode. It
does not contain Continue project configuration, the Haven 42 app, Ollama,
models, IDEs, drivers, maintainer scripts, or third-party installers.

Setup shows a preview first. It writes only after you add `--apply`, stops
before replacing existing settings unless you add `--replace`, and creates a
backup before replacement.

## Availability

The earlier `0.1.0-development` package is retired because it shipped Continue
project configuration that current editor tests did not load or apply
reliably. The corrected package remains source-only until a new package review
passes. Do not use the old ZIP for a new setup.

Follow the
[package guide](https://github.com/hysel/haven-42/tree/main/packages/local-llm-ide)
for the current source status and safety boundaries.
