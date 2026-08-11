# Haven 42

_For people evaluating or using Haven 42 on Windows, Linux, or macOS.
Current packages are unsigned development software._

**Your private, local AI station.**

Haven 42 is an application for private AI chat, writing, and summarization. It
opens in your browser, but the application runs on your computer. It can use an
AI model on the same computer or on a private server you choose.

Haven 42 has no hosted chat service, user account, or tracking. It never
downloads a model silently: guided setup first shows what is needed and asks
permission. Current builds are unsigned development packages.

## Start here

1. Follow the [[Quick Start|Quick-Start]] guide to run the source version or an
   exact unsigned portable development package.
2. Choose **Set up this computer · Recommended**. Haven 42 checks your computer,
   explains what it needs, and asks before downloading anything.
3. Read [[Using Haven 42|Using-Haven-42]] for chat, attachments, models, and
   image-generation guidance.

If something does not work, begin with [[Troubleshooting]].

## What works today

- One continuous conversation for chat, drafting, and summarization.
- Automatic connection to a completed Haven-managed local setup, or an advanced
  connection to Ollama on another private computer.
- Installed-model selection and explicit, download-free public catalog search.
- Memory-only prompt recall and conversation state.
- Bounded text, source-code, structured-text, and PNG screenshot attachments.
- Safe response formatting for headings, lists, code, quotations, and emoji.
- Token totals, response timing, and tokens per second.
- A promoted loopback Linux ComfyUI/SDXL image workflow.
- Read-only system readiness, software plans, and bundled evidence views.

Features that are still experimental are kept out of the main experience.
Haven 42 explains approved setup downloads, never runs attached files, and does
not silently change drivers, Windows settings, or automatic updates.

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
| Configure Continue, Aider, or OpenCode | [Coding Tools for Local Models](Coding-Tools-For-Local-Models) |
| See the computers and AI engines tested | [Tested Hardware and AI Engines](Tested-Hardware-And-AI-Engines) |
| Check exact model and hardware test status | [Model and Hardware Test Status](Model-And-Hardware-Test-Status) |
| See maturity and future work | [Roadmap](Roadmap) |
| Find contributor and validation records | [Engineering and Validation Index](Engineering-Index) |

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

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. The latest stable release line is `0.3.0`. Haven 42 is still
development software: signing and notarization are inactive, the updater cannot
modify a machine, and no production-readiness claim is made.

Windows testers can review the exact published files, checksums, and limits in
the [Windows Alpha release record](https://github.com/hysel/haven-42/blob/main/docs/windows-alpha-release.md).

See [[Project Information|Project-Information]], [[Roadmap]], and the
[[Engineering and Validation Index|Engineering-Index]].

The source repository is [hysel/haven-42](https://github.com/hysel/haven-42).
