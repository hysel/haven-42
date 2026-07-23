# Progressive Onboarding

Haven 42 uses one progressive onboarding pattern for ordinary and advanced users. The machine-readable source is `config/progressive-onboarding-contract.json`. This is a presentation and policy contract, not an installer, provider runtime, or permission to execute.

## The Three Choices

Every configurable capability presents the same decision in language adapted to that capability:

1. **Set it up for me** uses an exact validated profile and recommended settings when one exists.
2. **Connect or use my existing setup** discovers or references user-managed software without silently changing it.
3. **Not now** leaves that capability honestly configuration-required or unavailable without blocking unrelated work.

The first two choices include **Customize advanced settings**. Advanced controls are collapsed by default, show recommended values, explain their effect and evidence impact, and can be reset. They are structured settings rather than arbitrary command or flag entry.

## Where It Applies

The pattern covers chat, writing and summarization providers; engineering agent surfaces; image, audio, music, and video generation; model discovery and quantization; inference engines; local and remote provider connections; and storage, retention, update, rollback, and cleanup preferences. A capability may rename “provider” to “agent,” “engine,” “model,” or “storage,” but it does not invent another onboarding state machine.

Examples include:

| Capability | Guided path | Existing path |
| --- | --- | --- |
| Chat | Select a validated local text profile and recommended model | Connect an existing local or explicitly trusted remote API |
| Software | Configure a maintained agent surface with safe defaults | Discover an existing Continue, Aider, or OpenCode setup |
| Images | Install a promoted native provider profile | Validate an existing ComfyUI endpoint and model mapping |
| Audio or video | Offer a profile only after its exact promotion gates pass | Inspect a user-managed provider without inheriting validation |
| Models | Recommend a fitting trusted artifact | Register an existing local model and verify identity and runtime fit |
| Engines | Select an exact validated engine/backend profile | Connect an installed engine and derive an honest evidence state |

## Configuration States

The engine, not the renderer, derives one visible state:

- **Validated** matches exact passed evidence and its bounded settings.
- **Customized** changes a validated base only inside explicitly tested bounds.
- **Unverified** exceeds exact evidence and cannot be represented as validated or executed through the ordinary product path.
- **Blocked** is unsafe, incompatible, failed, incomplete, or prohibited.

Changing an advanced value always reevaluates the state. Evidence never transfers between operating systems, accelerators, engines, providers, models, operations, or untested setting ranges.

## Safety Boundary

Advanced mode is control, not a bypass. It cannot disable effect-bound consent, immutable download identity and checksum checks, credential protection, network-exposure controls, exact hardware/provider selection, or preservation of preexisting user data. It cannot silently enable custom nodes, plugins, external API nodes, public binding, CPU fallback, or provider fallback.

Connecting an existing setup is read-only by default. Haven 42 clearly distinguishes application-managed and user-managed files, requires a separate trust and privacy review for remote connections, stores credentials through native secret references, and does not overwrite an advanced user's installation or configuration without a separately reviewed action.

## Current Boundary

The current product slice may render these choices and their derived state, but `runtimeAdmitted` remains false. No desktop runtime, provider installer, download, connection, or machine change is admitted by this contract.
