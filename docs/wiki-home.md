# Haven 42

_For people evaluating or using Haven 42 on Windows, Linux, or macOS.
Current packages are unsigned development software._

**Your private, local AI station.**

Haven 42 is a local-first browser application for private AI conversations,
writing, summarization, selected-file context, model management, and an
admitted local image workflow. The application runs on your device and uses a
local or explicitly selected private-network provider.

Haven 42 has no hosted chat service, user account, telemetry, or automatic
model download. Current builds are unsigned development artifacts.

## Start here

1. Follow the [[Quick Start|Quick-Start]] guide to run the source version or an
   exact unsigned portable development package.
2. Open Haven 42 in your browser and choose **Explore** or connect an existing
   Ollama provider.
3. Read [[Using Haven 42|Using-Haven-42]] for chat, attachments, models, and
   image-generation guidance.

If something does not work, begin with [[Troubleshooting]].

## What works today

- One continuous conversation for chat, drafting, and summarization.
- Explicit connection to a same-device or private-network Ollama server.
- Installed-model selection and explicit, download-free public catalog search.
- Memory-only prompt recall and conversation state.
- Bounded text, source-code, structured-text, and PNG screenshot attachments.
- Safe Markdown-style response formatting without model-supplied HTML or links.
- Provider-reported token and timing details.
- A promoted loopback Linux ComfyUI/SDXL image workflow.
- Read-only system readiness, software plans, and bundled evidence views.

Capabilities that are experimental, evidence-only, or not admitted are labeled
as such in the interface and documentation. Haven 42 does not silently install
software, download models, execute attached files, enable online updates, or
modify system configuration.

## Choose a guide

| I want to… | Read… |
| --- | --- |
| Run Haven 42 for the first time | [Quick Start](Quick-Start) |
| Understand the main interface | [Using Haven 42](Using-Haven-42) |
| Choose or find a model | [Choose a Model](Local-Model-Selection) |
| Configure local image generation | [Set Up Local Images](Local-Image-Provider-Onboarding) |
| Understand what stays in memory | [Privacy](Privacy-Policy) |
| Secure a local or private-network provider | [Connection Security](Provider-Endpoint-Security) |
| Fix a problem | [Troubleshooting](Troubleshooting) |
| Use engineering and contributor features | [Advanced Topics](Advanced-Topics) |
| See maturity and future work | [Project Information](Project-Information) |

## Privacy and security

The browser UI is served only on IPv4 loopback. Current conversation text,
selected attachments, settings, and generated image bytes remain in process or
browser memory and are not stored as Haven 42 history. A separately operated
provider may have its own retention behavior.

Private-network HTTP is unencrypted. Haven 42 displays a warning when that
transport is selected; use a trusted HTTPS endpoint or a loopback tunnel when
traffic must cross another machine.

Read [[Privacy|Privacy-Policy]] and [[Connection Security|Provider-Endpoint-Security]]
before using private or sensitive material.

## Project status

The current release line is `0.3.0`; later work remains unreleased. Haven 42 is
still development software. Packages are unsigned, signing and notarization are
inactive, the updater cannot modify a machine, and no public production release
claim is made.

See [[Project Information|Project-Information]], the concise navigation in the
[[Roadmap]], and detailed [[Evidence Dashboard|Evidence-Dashboard]] records.

The source repository is [hysel/haven-42](https://github.com/hysel/haven-42).
