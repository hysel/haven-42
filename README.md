# Haven 42

**Your private, local AI station.**

[Quick start](#quick-start) · [What works](#what-works-today) ·
[Roadmap](#roadmap-at-a-glance) · [Wiki](https://github.com/hysel/haven-42/wiki) ·
[Alpha downloads and feedback](docs/windows-alpha-download-and-feedback.md) ·
[Contact](mailto:haven42localai@gmail.com) ·
[Code signing policy](CODE-SIGNING-POLICY.md) · [Privacy policy](PRIVACY.md)

> **Before you start:** Haven 42 is still being tested. Windows may warn you
> because the current package is not digitally signed. Use only a package you
> received from a trusted Haven 42 test source.

> **Windows Alpha available:** `0.4.0-alpha.1` targets invited Windows
> 11 x64 testing with Chat, Writing, and Summarization in one text workspace.
> Its unsigned package and local setup are available only for this early test.
> See [what the Alpha includes](docs/windows-alpha-0.4-alpha-1.md).

Download the unsigned package from the
[Haven 42 0.4.0 Alpha 1 prerelease](https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.1).
Testers should use the
[Windows Alpha download and feedback guide](docs/windows-alpha-download-and-feedback.md)
to verify the download and report problems without exposing private data.

Haven 42 is a private app for chat, writing, and summarization. It opens in
your web browser, but it runs on your computer. It can use a model on the same
computer or on a private server you choose.

You do not need to understand Python, model sizes, graphics runtimes, or server
settings to use guided setup. Haven 42 checks your computer, recommends a safe
choice, explains each download, and asks before making the approved changes.

The main download is for everyday use. Coding tools for Continue, Aider, and
OpenCode are now kept in a separate
[Local LLM IDE Tools package](packages/local-llm-ide/README.md). You do not
need that package to use Haven 42. People who use these coding tools can get
the optional package from the [Local LLM IDE Tools development prerelease](https://github.com/hysel/haven-42/releases/tag/local-llm-ide-tools-v0.1.0-development).

## What works today

| Capability | Current state |
| --- | --- |
| Application | Opens in your normal web browser while staying on your computer. |
| Chat, writing, and summarization | Uses one continuous conversation that Haven 42 does not save. |
| Models | Shows available AI models, recommends a suitable choice, and lets you search without automatically downloading. |
| Attachments | Accepts a bounded set of selected UTF-8 text, CSV, JSON, source-code, and PNG screenshot files. Clipboard PNG paste is supported. Attachments are never executed. |
| Response display | Safely renders headings, lists, emphasis, code, quotations, and Unicode emoji without model-supplied active HTML or links. |
| Response information | Shows token totals, response time, and tokens per second. |
| Local images | Haven connects to image software that the user installs separately. One Linux ComfyUI/SDXL setup has passed testing. Windows image setup is not ready. |
| Software workflows | Shows registered read-only plans. The browser cannot start their processes, read a repository, or write files. |
| System information | Shows whether the computer is ready and summarizes completed tests without running background checks. |

Music and video are not available in the product. Audio has partial external
Linux CUDA evidence, and video remains research-only after a fail-closed
hardware/storage preflight. Unshipped media providers remain
documentation-only candidate inventories. Persistent
conversation history, PDF/Office/OpenDocument parsing, folder scanning,
controlled web research, signing, notarization, installers, and active online
updates are not shipped.

Advanced engineering plans and test evidence are kept outside this beginner
overview. Contributors can start with [Project information](PROJECT.md) and the
[documentation index](docs/wiki-documentation-index.md).

## Quick start

### Run from source · Advanced

Most users should use the portable package. Running from source is for
developers and requires Python 3. Ollama and an installed model are needed only
for AI responses; you can still look around without them.

From the repository root, run the command for your platform.

Windows PowerShell 5.1 or PowerShell 7:

```powershell
.\scripts\start-haven42-web.ps1
```

PowerShell 7 is optional on Windows. Haven 42's committed PowerShell scripts
are parser-checked and smoke-tested under both the built-in Windows PowerShell
5.1 engine and PowerShell 7 in hosted Windows validation.

Linux:

```bash
./scripts/start-haven42-web.linux.sh
```

macOS:

```bash
./scripts/start-haven42-web.macos.sh
```

Haven 42 starts on `http://127.0.0.1:4242` and asks the operating system to
open its default browser. If that does not happen, copy the exact loopback URL
printed in the terminal into your browser.

### First-run choices

- **Set up this computer · Recommended** safely checks the computer, recommends
  a model, explains every download, and asks permission before starting.
- **Use another AI server · Advanced** connects to Ollama that you already
  manage on this computer or your private network.
- **Look around first** opens Haven 42 without checking, downloading, or
  connecting anything.

After guided local setup finishes, Haven 42 checks those files again on every
launch, starts its local AI engine, and opens the conversation. You can still
switch to another AI server later from **System**.

For same-machine Ollama, use `http://127.0.0.1:11434`. A private-network HTTP
connection is unencrypted, so Haven 42 displays a warning. Use a trusted HTTPS
endpoint or a loopback tunnel when sensitive traffic must cross another
machine.

If the Ollama endpoint requires authentication, expand **Advanced connection
settings** and choose **Bearer token** or **X-API-Key**. Authenticated
private-network connections require HTTPS. Haven 42 keeps the key only for the
current session and never stores or returns it. Most users should keep
**Automatic (Recommended)**; a future Haven-managed HTTPS
gateway will select its configured authentication mode during setup.

Normal model search never downloads a model. The separate Windows Alpha guided
setup may download its exact recommended model only after the tester approves
the displayed setup plan.

### Portable package · Recommended for testers

The portable package includes everything Haven 42 itself needs. Extract the ZIP
into a folder you own, keep all extracted files together, and run `haven42.exe`.
It does not require administrator access or install Haven 42 as a Windows
service. Guided setup explains and asks permission before downloading Ollama or
an AI model into the same extracted folder.

See [Portable Development Package](docs/portable-development-package.md) for
the build, integrity, inventory, SBOM, and native smoke-test evidence. Haven 42
does not publish a GitHub Release or claim production readiness from these
artifacts.

## Using Haven 42

- Press **Enter** to send and **Shift+Enter** for a new line.
- Use **Up** and **Down** at the start or end of the text box to recall prompts.
- Use **New task** to clear the current in-memory conversation.
- Open **Models** to choose an installed model or explicitly search the public
  catalog without downloading anything.
- Use **Attach files** or paste a PNG screenshot to give the AI more context.
- Expand **Response details · Advanced** for token and timing information.
- Use **System** to choose immediate, 5-minute, 15-minute, or 30-minute idle
  model cleanup.

Current prompts, responses, selected attachments, provider settings, and image
bytes are kept in process or browser memory. They are not stored as Haven 42
history. A separately managed provider may have its own retention behavior.

Start with the [wiki Quick Start](https://github.com/hysel/haven-42/wiki/Quick-Start),
then use the [Using Haven 42 guide](https://github.com/hysel/haven-42/wiki/Using-Haven-42)
or [Troubleshooting](docs/troubleshooting.md).

## Privacy and safety

- The Haven 42 page is available only from this computer.
- AI server addresses are limited to this computer or a private network.
- Haven 42 blocks public AI server addresses, passwords placed in an address,
  and unsafe redirects. Advanced API keys stay in memory and require an
  encrypted HTTPS connection when another computer is used.
- Haven 42 checks attachment names, formats, and contents and rejects files
  that look suspicious or do not match their stated type.
- Attachments are information for the AI to read. Haven 42 never runs attached
  code or treats attachment instructions as computer commands.
- Models do not receive an unrestricted internet tool.
- Features remain unavailable until their exact security tests pass.

## Common words

- **Model:** the AI that reads your request and writes the response.
- **Ollama:** the local AI engine that loads and runs a model.
- **AI server:** the computer and software running Ollama. It can be this
  computer or another computer on your private network.
- **Token:** a small piece of text counted by the model. Tokens per second is a
  rough measure of response speed.
- **Portable package:** a folder you can run and later remove without a normal
  application installer.

Read the [privacy policy](PRIVACY.md), [security policy](SECURITY.md),
[threat model](docs/security-threat-model.md), and
[provider endpoint security](docs/provider-endpoint-security.md) before using
sensitive material. Report vulnerabilities privately; do not place secrets,
private prompts, or personal files in a public issue.

## Roadmap at a glance

The table is intentionally brief. [`ROADMAP.md`](ROADMAP.md) is authoritative
for scope, evidence, blockers, and exit criteria.

| Milestone | Status | Summary |
| --- | --- | --- |
| Milestone 20: Choose models for the computer | Complete | Haven can inspect hardware and recommend suitable local model settings. |
| Milestone 21: Shared text and image foundations | Complete | Chat, writing, summarization, and the tested image path use common safety checks. |
| Milestone 22: Main application | In progress | The browser app and Windows Alpha work. Signing, normal installers, and stable release work remain open. |
| Milestone 23: Local images | In progress | One Linux setup works. Windows setup is still being tested. |
| Milestone 24: Local audio | In progress | Some Linux testing passed, but audio is not available in the app. |
| Milestone 25: Local video | Research | Video is not available in the app. |
| Milestone 26: Match model size to hardware | More hardware tests complete | NVIDIA, AMD, and Intel tests exist; automatic model conversion is not available. |
| Milestone 27: Use local files as context | In progress | Selected text and PNG attachments work. Folder libraries, PDF, and Office files are not ready. |
| Milestone 28: Web research | Proposed | Web research is not available in the app. |

Haven 42 lists a feature as working only when that exact software, model,
operating system, and hardware combination has passed its tests. A simulated
test does not prove that the feature works on a real computer.

## Coding tools are a separate package

If you want to connect Continue, Aider, or OpenCode to local Ollama, use the
[Local LLM IDE Tools package](packages/local-llm-ide/README.md). It has one
small setup command, previews changes before writing, and contains only the
files needed for those tools. It does not include the Haven 42 app, test
scripts, Ollama, models, IDEs, or drivers.

[Download the unsigned development ZIP](https://github.com/hysel/haven-42/releases/download/local-llm-ide-tools-v0.1.0-development/haven42-local-llm-ide-tools-0.1.0-development.zip),
then follow the package guide to verify the checksum before extracting it. The
[release page](https://github.com/hysel/haven-42/releases/tag/local-llm-ide-tools-v0.1.0-development)
also provides the checksum and package manifest.

Contributors can still read the detailed [IDE compatibility notes](docs/agent-surface-options.md),
[Continue testing guide](docs/continue-cli-model-testing.md), and
[setup design](docs/agent-surface-solutions.md). The complete
[setup-path reference](docs/setup-paths.md) remains available for maintainers.
Those documents are not part of the normal app setup.

## Documentation

| Need | Start here |
| --- | --- |
| End-user setup and operation | [Haven 42 wiki](https://github.com/hysel/haven-42/wiki) |
| Current plans and blockers | [Roadmap](ROADMAP.md) and [project status](PROJECT.md) |
| Security and privacy | [Security](SECURITY.md), [privacy](PRIVACY.md), and [threat model](docs/security-threat-model.md) |
| Exact validation records | [Evidence catalog](docs/evidence-catalog.md) and [evidence dashboard](docs/evidence-dashboard.md) |
| Architecture | [Architecture](ARCHITECTURE.md) and [solution review](docs/solution-architecture-review.md) |
| Contribution workflow | [Contributing](CONTRIBUTING.md) and [test tiers](docs/test-tiers.md) |

<details>
<summary>Contributor and engineering documentation index</summary>

This compact index keeps implementation material available without making it
part of the main end-user reading path.

- Models and hardware: [online discovery](docs/online-model-discovery.md),
  [hardware-aware model/config recommendation](docs/hardware-aware-recommendations.md),
  [remote hardware profile](docs/remote-hardware-profile.md), and
  [configuration strategy](docs/config-generation-strategy.md).
- Agent testing: [CLI surface testing](docs/agent-cli-surface-model-testing.md),
  [Continue CLI testing](docs/continue-cli-model-testing.md), and
  [promotion gates](docs/agent-surface-promotion-gates.md).
- Languages and projects: [language support](docs/language-support.md),
  [language rule packs](docs/language-rule-packs.md),
  [rule-pack evidence](examples/language-rule-pack-validation.md), and
  [project detection](docs/project-detection.md).
- Repository validation: [multi-repository guidance](docs/multi-repository-validation.md),
  [runtime output verification](docs/runtime-output-verification.md),
  [evidence template](examples/multi-repository-validation.md),
  [sample factory](docs/sample-repository-factory.md), and
  [sample evidence](examples/sample-repository-factory-validation.md).
- Workflow internals: [registry](docs/workflow-registry.md),
  [chooser](docs/workflow-chooser.md),
  [script consolidation](docs/script-consolidation-plan.md),
  [script appendix](docs/script-reference-appendix.md), and
  [maintainer queue](docs/autonomous-maintainer-queue.md).
- Advanced configuration: [shared assets](docs/shared-asset-installation.md),
  [surface bundles](docs/surface-specific-config-bundles.md), and
  [scenario packs](docs/sample-scenario-packs.md).
- Product architecture: [solution review](docs/solution-architecture-review.md)
  and [unified UI design](docs/unified-starter-toolkit-ui.md).

Capability identifiers used by the engineering contracts include
`general.chat`, `content.write`, `content.summarize`, and `media.image.create`.

</details>

## Contributor validation

Use the smallest appropriate local gate while developing:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
```

```bash
./scripts/test-pack.linux.sh --tier fast
```

Run Integration when a boundary changes and Full once near completion. See
[Test Tiers](docs/test-tiers.md). Hosted GitHub checks remain independent and
must pass for the exact proposed commit.

Advanced write behavior, troubleshooting signals, `ModelLanes`, and the
`1 - WRITE SAFE` lane are documented in [Tool Use Modes](docs/tool-use-modes.md)
and [Troubleshooting](docs/troubleshooting.md), rather than duplicated here.
If write tools are not validated yet, first prove that the surface can read file contents. Resolve paths from the currently opened repository folder and verify
approved changes with `git diff -- <file>`. `WORKSPACE_UNAVAILABLE`,
`APPLY_TARGET_MISMATCH`, printed `edit_file` text, or a claim that a tool created and read back a file are not proof of a successful write. Exclude
`create_new_file` when validating an existing-file edit. Two approval prompts
for the same line can duplicate content. `READ_TOOLS_UNAVAILABLE` cannot be labeled `read-only tool validated`.

## Version and license

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. Version `0.3.0` is the latest stable release line. Later work
remains under `Unreleased` until deliberately versioned and verified.

Haven 42 is licensed under the [MIT License](LICENSE).
