# Haven 42

**Your private, local AI station.**

[Quick start](#quick-start) · [What works](#what-works-today) ·
[Roadmap](#roadmap-at-a-glance) · [Wiki](https://github.com/hysel/haven-42/wiki) ·
[Alpha downloads and feedback](docs/windows-alpha-download-and-feedback.md) ·
[Code signing policy](CODE-SIGNING-POLICY.md) · [Privacy policy](PRIVACY.md)

> **Before you start:** Haven 42 is still being tested. Windows may warn you
> because the current package is not digitally signed. Use only a package you
> received from a trusted Haven 42 test source.

> **Windows Alpha work in progress:** `0.4.0-alpha.1` targets invited Windows
> 11 x64 testing with Chat, Writing, and Summarization in one text workspace.
> Its unsigned package, managed current-user
> setup, and private delivery are not yet admitted. See the
> [Alpha boundary](docs/windows-alpha-0.4-alpha-1.md).

The unsigned package is not public yet. When the exact candidate passes its
security review and hosted checks, testers will use the
[Windows Alpha download and feedback guide](docs/windows-alpha-download-and-feedback.md)
to verify the download and report problems without exposing private data.

Haven 42 is a local-first AI workbench for private chat, writing, and
summarization. It runs in your web browser, but the application itself runs on
your computer. It can use an AI model on the same computer or one on a private
server you choose.

You do not need to understand Python, model sizes, graphics runtimes, or server
settings to use guided setup. Haven 42 checks your computer, recommends a safe
choice, explains each download, and asks before making the approved changes.

The primary experience is for everyday users. Deeper software-engineering tools
for Continue, Aider, and OpenCode remain available to advanced users and
contributors.

## What works today

| Capability | Current state |
| --- | --- |
| Application | Opens in your normal web browser while staying on your computer. |
| Chat, writing, and summarization | Uses one continuous conversation that Haven 42 does not save. |
| Models | Shows available AI models, recommends a suitable choice, and lets you search without automatically downloading. |
| Attachments | Accepts a bounded set of selected UTF-8 text, CSV, JSON, source-code, and PNG screenshot files. Clipboard PNG paste is supported. Attachments are never executed. |
| Response display | Safely renders headings, lists, emphasis, code, quotations, and Unicode emoji without model-supplied active HTML or links. |
| Response information | Shows token totals, response time, and tokens per second. |
| Local images | Haven connects to separately acquired providers and never bundles their engines, models, drivers, or installers. Linux ComfyUI/SDXL is validated for one promoted loopback profile; Windows profiles remain independently gated. |
| Software workflows | Shows registered read-only plans. The browser cannot start their processes, read a repository, or write files. |
| Evidence and readiness | Displays bounded system readiness and bundled sanitized evidence without running background tests. |

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
- Use **Up** and **Down** at the appropriate text boundary to recall prompts.
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
| Milestone 20: Hardware-Aware Model And Config Automation | Complete | Recommendation, configuration, dispatch, health, cleanup, and evidence foundations. |
| Milestone 21: General-Purpose AI Assistant And Intent Routing | Complete | Repository-optional local text and image capabilities, routing, and typed artifacts. |
| Milestone 22: Unified Product UI And Task Composition | In progress | Runnable browser product, read-only workflow plans, hardened unsigned portable packages, private-alpha preparation, and inactive post-quantum migration planning; no alpha candidate or distribution is admitted, and signing, PQC activation, and machine effects remain gated. |
| Milestone 23: Native Local Image Generation | In progress | One promoted Linux profile; Windows NVIDIA and AMD exact-profile cells are partial; remaining lifecycle and platform gates are open. |
| Milestone 24: Local Music And Audio Generation | Live feasibility in progress | Partial Linux CUDA evidence exists; no audio provider is promoted. |
| Milestone 25: Local Video Generation | Research in progress | Candidate research and a fail-closed Quadro hardware/storage preflight exist; no executable video integration ships. |
| Milestone 26: Hardware-Adaptive Model Quantization | Engine evidence expanded | Exact NVIDIA, AMD, and Intel evidence plus bounded Ollama 0.32.5 tool-envelope validation exists; WSL2 AMD and every tool-execution path remain unadmitted. |
| Milestone 27: Local Knowledge Context And Retrieval | In progress | Bounded attachments are available; lexical, temporary-database, explicit-folder, parser, embedding-evaluation, and encrypted-library foundations remain inactive or independently gated. |
| Milestone 28: Controlled Web Research | Proposed; runtime unadmitted | Offline security contracts, transport guards, exact approval state, and a disabled fixed-provider fixture adapter exist without live transport, UI, page retrieval, or a model tool. |

The project uses a pass-before-ship rule: evidence is specific to the exact
artifact, model, provider, operating system, hardware, and operation tested.
A fixture-backed contract does not establish general native support.

## For software engineering

The maintained agent surfaces are Continue, Aider, and OpenCode. Begin with
read-only review and planning; approve narrow writes only after confirming the
target and independently verifying the resulting diff.

- [VS Code and Continue setup](docs/vscode-continue-setup.md)
- [Agent surface options](docs/agent-surface-options.md)
- [Agent surface solutions](docs/agent-surface-solutions.md)
- [Setup paths](docs/setup-paths.md)
- [Tool-use modes](docs/tool-use-modes.md)
- [Approved tool-backed changes](docs/approved-tool-backed-changes.md)

These engineering tools operate outside the everyday browser flow and may have
separate repository, software, or network effects.

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

Version `0.3.0` is the current release line. Later work remains under
`Unreleased` until deliberately versioned and verified.

Haven 42 is licensed under the [MIT License](LICENSE).
