# Haven 42

**Your private, local AI station.**

Private AI that runs on hardware you control.

[Get started](https://github.com/hysel/haven-42/wiki/Quick-Start) ·
[Learn the interface](https://github.com/hysel/haven-42/wiki/Using-Haven-42) ·
[Choose a model](https://github.com/hysel/haven-42/wiki/Local-Model-Selection) ·
[Troubleshoot](https://github.com/hysel/haven-42/wiki/Troubleshooting) ·
[Contact](mailto:haven42localai@gmail.com)

Haven 42 is an application for private AI chat, writing, and summarization. It
opens in a browser, while the application and AI model run on your computer or
on a private Ollama server you choose.

There is no Haven 42 account or hosted chat service. The app does not silently
download a model: it shows what is needed, where files will be stored, and asks
before downloading anything.

> **Development notice:** Current packages are unsigned test builds. Windows
> or macOS may display a security warning. Use only a package from a trusted
> Haven 42 test source.

Version `0.3.0` is the current stable release line. See the
[code signing policy](CODE-SIGNING-POLICY.md) for why development packages are
currently unsigned.

## What you can do

- Chat, draft, and summarize in one private conversation.
- Let Haven 42 recommend a tested model for your computer and task.
- Choose another installed model or search Ollama's public model catalog.
- Attach bounded text, source-code, structured-text, and PNG screenshot files.
- Connect to Ollama on the same computer or on a private server.
- In the development source, review and approve a web search before any query
  leaves your computer. The published Alpha 1 package predates this feature.
- See response speed and local CPU, memory, and graphics use.

Music and video generation are not part of the current app. Conversation
history is kept in memory rather than saved. PDF and Office document parsing,
signed installers, and unattended automatic updates are not shipped.
One Linux ComfyUI/SDXL image path has passed testing; other media paths remain gated.

## Start using Haven 42

The wiki contains the single maintained setup path:

1. Follow [Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start).
2. Continue with [Using Haven 42](https://github.com/hysel/haven-42/wiki/Using-Haven-42).
3. If something goes wrong, open [Troubleshooting](https://github.com/hysel/haven-42/wiki/Troubleshooting).

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. It is available from the
[Alpha 1 release](https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.1).
The [Windows download guide](docs/windows-alpha-download-and-feedback.md)
explains how to verify the package and report a problem safely.

## Privacy and safety

- The Haven 42 page is available only from the computer running the app.
- Conversation text, selected attachments, provider settings, and generated
  image bytes are not stored as Haven 42 conversation history.
- Public AI-server addresses, credentials embedded in addresses, and unsafe
  redirects are blocked. Private remote servers should use HTTPS.
- Attachments are treated as information for the model and are never executed.
- Downloads, web searches, and managed updates require a clear review and
  approval step.

Read the [privacy policy](PRIVACY.md), [security policy](SECURITY.md), and
[connection security guide](https://github.com/hysel/haven-42/wiki/Provider-Endpoint-Security)
before using sensitive material. Never put passwords, private prompts, or
personal files in a public issue.

## Models, hardware, and power

Haven 42 keeps recommendations tied to the exact model, runtime, operating
system, and hardware that were tested. A result on one graphics card does not
automatically apply to another.

- [Choose a model](https://github.com/hysel/haven-42/wiki/Local-Model-Selection)
- [Hardware compatibility](https://github.com/hysel/haven-42/wiki/Tested-Hardware-And-AI-Engines)
- [Model compatibility](https://github.com/hysel/haven-42/wiki/Model-And-Hardware-Test-Status)
- [Power use and electricity costs](https://github.com/hysel/haven-42/wiki/Model-Power-And-Electricity-Evidence)

To request testing for a locally runnable model, use the
[model request form](https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml).
You do not need to know the model's technical details.

## Coding tools

Aider and OpenCode configuration is developed separately in the optional
[Local LLM IDE Tools package](packages/local-llm-ide/README.md). Continue is a
legacy, evidence-only integration retained to explain historical results; it is
not required or recommended for Haven 42.

## For contributors

The repository `docs/` directory contains engineering and contributor
material. Start with the [Engineering and Validation Index](docs/engineering-index.md)
or the detailed [Roadmap](ROADMAP.md).

Run the smallest appropriate test tier while developing:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
```

```bash
./scripts/test-pack.linux.sh --tier fast
```

Haven 42 is licensed under the [MIT License](LICENSE).
