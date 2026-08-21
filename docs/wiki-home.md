# Haven 42

**Private AI that runs on hardware you control.**

Haven 42 gives you a simple interface for local AI chat, writing, and
summarization. It opens in a browser, while the application and AI model run on
your computer or on a private Ollama server you choose.

There is no Haven 42 account or hosted chat service. Haven 42 does not silently
download models or send searches: it shows what will happen and asks first.

> **Before you begin:** Haven 42 is development software. Current packages are
> unsigned, so your operating system may show a security warning. Use only a
> package from a trusted Haven 42 test source.

## Start here

1. Follow [[Quick Start|Quick-Start]] to run Haven 42.
2. Choose **Set up this computer · Recommended** for guided local setup, or
   connect an existing private Ollama server.
3. Read [[Using Haven 42|Using-Haven-42]] to learn chat, attachments, models,
   and approved web research.

If something does not work, open [[Troubleshooting]]. It begins with the
shortest recovery steps and shows where to find a sanitized support report.

## What you can do

- Chat, draft, and summarize in one private conversation.
- Let Haven 42 recommend a tested model for your computer and task.
- Choose another installed model or search Ollama's public model catalog.
- Attach bounded text, source-code, structured-text, and PNG screenshot files.
- Connect to Ollama on this computer or on a private server.
- In the development source, review and approve a web search before any query
  leaves your computer. The published Alpha 1 package predates this feature.
- See response speed and local CPU, memory, and graphics use.

Music and video generation are not part of the current app. Conversation
history is kept in memory rather than saved. PDF and Office document parsing,
signed installers, and unattended automatic updates are not shipped.

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

The Haven 42 page is available only from the computer running the app. Current
conversation text, selected attachments, settings, and generated image bytes
are not stored as Haven 42 conversation history.

If you connect a separately operated AI server, that server has its own privacy
and retention behavior. Plain HTTP on a private network is not encrypted; use
HTTPS or a loopback tunnel when traffic must cross another computer.

Read [[Privacy|Privacy-Policy]] and
[[Connection Security|Provider-Endpoint-Security]] before using sensitive
material.

## About this project

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. The latest stable release line is `0.3.0`. Newer source changes are
not a published release until they are deliberately packaged and verified.

For project background, limitations, and contact information, see
[[About Haven 42|Project-Information]]. Contributors can use the
[[Engineering and Validation Index|Engineering-Index]] and [[Roadmap]].

The source repository is [hysel/haven-42](https://github.com/hysel/haven-42).
