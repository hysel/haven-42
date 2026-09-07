# Haven 42

**Private AI that runs on hardware you control.**

**[Download Alpha 2 for Windows, Linux or Apple Silicon](https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.2)**

The release includes portable packages, checksums, changes since Alpha 1 and known limitations.

Haven 42 is a browser interface for local AI chat, writing, and summarization.
The application runs on your computer; the model can run there too, or on a
private Ollama server you choose.

There's no Haven 42 account or hosted chat service. If Haven 42 needs to
download a model or send a search, it tells you what it's about to do and asks
first.

> **Before you begin:** Alpha 2 is experimental software. Its Windows launcher
> is signed, its Apple Silicon app is signed and notarized, and its Linux archive
> is unsigned. Verify the checksums and read the release's testing limitations.

## Start here

1. Follow [[Quick Start|Quick-Start]] to run Haven 42.
2. For the normal local setup, choose **Set up this computer · Recommended**.
   If you already run a private Ollama server, connect that instead.
3. Read [[Using Haven 42|Using-Haven-42]] to learn chat, attachments, models,
   and approved web research.

If something breaks, start with [[Troubleshooting]]. The shortest recovery
steps come first, followed by instructions for finding a sanitized support
report.

## What you can do

- Chat, draft, and summarize in one private conversation.
- Let Haven 42 recommend a tested model for your computer and task.
- Choose another installed model or search Ollama's public model catalog.
- Attach bounded text, source-code, structured-text, and PNG screenshot files.
- Connect to Ollama on this computer or on a private server.
- In Alpha 2, approve every web-research request before it
  leaves your computer, routed through Wikipedia or Brave Search. Retrieved
  text stays inert and in memory; the model never receives the search key or
  permission to approve another request. Exact package and manual
  assistive-technology parity remain open.
- See response speed and local CPU, memory, and graphics use.

The current app doesn't generate music or video. It keeps conversation history
in memory instead of saving it. PDF and Office document parsing, signed
installers, and unattended automatic updates aren't shipped either.

## Find the right guide

| I want to… | Read… |
| --- | --- |
| Install or open Haven 42 | [Quick Start](Quick-Start) |
| Learn the main interface | [Using Haven 42](Using-Haven-42) |
| Choose or download a model | [Choose a Model](Local-Model-Selection) |
| Fix a problem | [Troubleshooting](Troubleshooting) |
| Understand what stays private | [Privacy](Privacy-Policy) |
| Connect another computer safely | [Connection Security](Provider-Endpoint-Security) |
| Set up local image generation | [Set Up Local Images](Local-Image-Provider-Onboarding) |
| Use a local model for coding | [Coding Tools for Local Models](Coding-Tools-For-Local-Models) |
| Check hardware compatibility | [Hardware Compatibility](Tested-Hardware-And-AI-Engines) |
| Check model compatibility | [Model Compatibility](Model-And-Hardware-Test-Status) |
| Estimate electricity cost | [Power Use and Electricity Costs](Model-Power-And-Electricity-Evidence) |

## Privacy in plain language

You can open the Haven 42 page only from the computer running the app. Haven 42
doesn't store the current conversation, selected attachments, settings, or
generated image bytes as conversation history.

Connect a separate AI server and its privacy and retention rules apply too.
Plain HTTP on a private network isn't encrypted, so use HTTPS or a loopback
tunnel when traffic crosses another computer.

Read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]] before using sensitive
material.

## About this project

The latest public test build is [Alpha 2 (`0.4.0-alpha.2`)](https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.2),
published for Windows x64, Linux x64 and Apple Silicon. It is a prerelease, not
production certification. The stable release line remains `0.3.0`.

For project background, limitations, and contact information, see
[[About Haven 42|Project-Information]]. Contributors can use the
[[Engineering and Validation Index|Engineering-Index]] and [[Roadmap]].

The source repository is [hysel/haven-42](https://github.com/hysel/haven-42).
