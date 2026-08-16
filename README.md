# Haven 42

**Your private, local AI station.**

[Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start) ·
[What works today](https://github.com/hysel/haven-42/wiki#what-works-today) ·
[Roadmap](ROADMAP.md) ·
[Common Words](https://github.com/hysel/haven-42/wiki/Glossary) ·
[Code signing policy](CODE-SIGNING-POLICY.md) ·
[Contact](mailto:haven42localai@gmail.com)

> **Before you start:** Haven 42 is still being tested. Current packages are
> unsigned, so Windows may display a warning. Use only a package from a trusted
> Haven 42 test source.

Haven 42 is an application for private AI chat, writing, and summarization. It
opens in your browser, but the application runs on your computer. It can use an
AI model on the same computer or an Ollama server on a private network.

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. Download it from the
[Alpha 1 release](https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.1),
then follow the [Windows download and feedback guide](docs/windows-alpha-download-and-feedback.md)
to check the package and report a problem without exposing private data.

## What works today

This is a short summary. The wiki [What works today](https://github.com/hysel/haven-42/wiki#what-works-today)
section is the authoritative capability list.

| Area | Current capability |
| --- | --- |
| Text | Private chat, writing, and summarization with safe response formatting and token-speed details. |
| Models | A suitable local model is recommended from tested evidence. A person can search the public catalog, review an exact model and destination, and approve a verified Ollama download; Haven 42 never downloads or selects one silently. |
| Context | Selected, bounded text, source-code, structured-text, and PNG screenshot attachments. Haven 42 never executes an attachment. |
| Local providers | A managed local Ollama setup or a private Ollama server. One Linux ComfyUI/SDXL image path has passed testing; other media paths remain gated. |
| Web research | The development source offers reviewed Wikipedia lookup, a bounded multi-source cited answer using a session-only Brave Search key and the selected local model, and a browser-search fallback. Every query needs a person’s one-time approval; models cannot browse, approve, follow links, or start another search. Exact package parity remains open. |

Music and video are not available in the product. Persistent conversation
history, PDF and Office parsing, folder scanning, autonomous model browsing,
signed installers, and active online updates are not shipped. The published
Alpha 1 package predates the development web-research slice above.

## Quick start

Use the wiki [Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start).
It is the single maintained setup guide for the portable package and advanced
source startup. The guide continues to [Using Haven 42](https://github.com/hysel/haven-42/wiki/Using-Haven-42)
and then [Troubleshooting](https://github.com/hysel/haven-42/wiki/Troubleshooting).

The portable Windows package keeps Haven-managed files beside the app and does
not install Haven 42 as a Windows service. Guided setup shows every required
download and asks permission before it continues.

## Privacy and safety

- The Haven 42 page is available only from the computer running the app.
- Conversation text, selected attachments, provider settings, and generated
  image bytes remain in process or browser memory. Haven 42 does not save them
  as conversation history.
- Haven 42 blocks public AI server addresses, credentials embedded in an
  address, and unsafe redirects. An authenticated server on another computer
  requires HTTPS.
- Attachments are checked, bounded, and treated only as information for the
  model. They are never run as code or computer commands.
- Features remain unavailable until their exact security and validation gates
  pass.

Read the [privacy policy](PRIVACY.md), [security policy](SECURITY.md), and
[connection security guide](https://github.com/hysel/haven-42/wiki/Provider-Endpoint-Security) before
using sensitive material. Report vulnerabilities privately; never place
secrets, private prompts, or personal files in a public issue.

## Roadmap

[`ROADMAP.md`](ROADMAP.md) is the authoritative roadmap. Roadmap labels describe
milestone delivery; evidence labels describe the result of a bounded test.
`In progress` on the roadmap does not mean `🧪 Engineering evidence` or
`✅ Verified` on an evidence page.

See the human-readable [tested hardware](https://github.com/hysel/haven-42/wiki/Tested-Hardware-And-AI-Engines)
and [model and hardware status](https://github.com/hysel/haven-42/wiki/Model-And-Hardware-Test-Status)
pages for exact evidence boundaries.

Want Haven 42 to evaluate a particular locally runnable model? Submit the
[short model test request form](https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml).
You do not need to know the model's technical details, and a request does not
change Haven 42's automatic model choices.

## Coding tools are separate

Continue, Aider, and OpenCode support is distributed as the optional
[Local LLM IDE Tools package](packages/local-llm-ide/README.md). It is not
required to use Haven 42 and does not include the app, Ollama, models, IDEs, or
drivers.

The unsigned package is available from the
[Local LLM IDE Tools development release](https://github.com/hysel/haven-42/releases/tag/local-llm-ide-tools-v0.1.0-development).

## Documentation

| Need | Start here |
| --- | --- |
| Install and use Haven 42 | [Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start) |
| Fix a user-facing problem | [Troubleshooting](https://github.com/hysel/haven-42/wiki/Troubleshooting) |
| Understand a term | [Common Words](https://github.com/hysel/haven-42/wiki/Glossary) |
| Check hardware or model evidence | [Tested Hardware and AI Engines](https://github.com/hysel/haven-42/wiki/Tested-Hardware-And-AI-Engines) and [Model and Hardware Test Status](https://github.com/hysel/haven-42/wiki/Model-And-Hardware-Test-Status) |
| Review plans and blockers | [Roadmap](ROADMAP.md) and [project status](PROJECT.md) |
| Contribute or inspect engineering records | [Engineering and Validation Index](docs/engineering-index.md) |

The repository `docs/` files are canonical for contributor and engineering
material. Wiki pages beginning with `Eng-` are labeled pointers to those files,
not separately maintained copies.

## Contributor validation

Use the smallest appropriate local gate while developing:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
```

```bash
./scripts/test-pack.linux.sh --tier fast
```

Run Integration when a boundary changes and Full near completion. See
[Test Tiers](docs/test-tiers.md). Hosted checks must pass for the exact proposed
commit.

## Version and license

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. Version `0.3.0` is the latest stable release line. Later work
remains under `Unreleased` until deliberately versioned and verified.

Haven 42 is licensed under the [MIT License](LICENSE).
