# Product UI First Slice

## Decision

The first Haven 42 product slice is a local, web-technology interface that can
later run inside the admitted Tauri desktop shell. This phase defines the user
experience and produces a renderer-safe view model; it does not admit Tauri,
React, npm, Cargo, a sidecar binary, installer, or updater into the product.

The first useful vertical slice is local chat plus system readiness. Software
work remains reachable through the validated workflow registry. Image creation
is visible, but it runs only when the evidence-gated provider is discovered as
available for the exact host profile.

## Navigation

```text
First launch
  Welcome -> Privacy and control -> System readiness -> Home

Home: What do you want to do?
  Chat with local AI -----------> Chat
  Work on a software project ---> Software project
  Create an image --------------> Images
  Manage models and providers --> Models
  Check system readiness -------> System

Any executable action
  Compose -> Availability -> Disclosure -> Approval, if required
          -> Progress -> Typed result or typed error

Any configurable capability
  Set it up for me -----------\
                                -> Standard or advanced settings -> Derived state
  Connect existing setup -----/
  Not now ---------------------> Honest unavailable/configuration-required state
```

The persistent navigation is Home, Chat, Software, Images, Models, and System.
Task progress and results are contextual screens rather than primary sections.

## First-Run Wireframes

```text
+----------------------------------------------------------------+
| Haven 42                                                       |
| Your local AI workspace                                       |
|                                                                |
| Chat, create, and work on software with providers you control. |
| Nothing is downloaded and no network probe runs automatically. |
|                                             [Get started]       |
+----------------------------------------------------------------+

+----------------------------------------------------------------+
| Privacy and control                                            |
| [x] Local-first execution                                      |
| [x] No telemetry by default                                    |
| [x] Approvals before downloads, network use, or file changes   |
| [x] Repository access only after you select a folder           |
|                                      [Back] [Check my system]   |
+----------------------------------------------------------------+

+----------------------------------------------------------------+
| System readiness                                               |
| Local engine       Not checked        [Check]                   |
| Text provider      Configuration required                       |
| Image provider     Configuration required                       |
| Repository         Not required                                |
|                                                                |
| Checks are read-only. Network probes require separate consent. |
|                                      [Skip] [Continue to home]  |
+----------------------------------------------------------------+
```

Skipping readiness does not mark providers available. It leads to the Home
screen with honest configuration-required states and remediation actions.

## Shared Setup Wireframe

Every configurable area uses the same progressive pattern from
`config/progressive-onboarding-contract.json`. Labels may say provider, agent,
engine, model, or storage, but the choices and evidence rules do not fork.

```text
+----------------------------------------------------------------+
| Set up: Image generation                 State: Not configured  |
|----------------------------------------------------------------|
| ( ) Set it up for me                                           |
|     Use a validated profile and recommended settings.          |
|     [Customize advanced settings]                              |
|                                                                |
| ( ) Connect or use my existing setup                           |
|     Discover or reference software I already manage.           |
|     [Customize advanced settings]                              |
|                                                                |
| ( ) Not now                                                    |
|                                                                |
| Advanced changes show effect and evidence impact before save.  |
|                                                [Back] [Review]  |
+----------------------------------------------------------------+
```

The engine derives `validated`, `customized`, `unverified`, or `blocked`.
The renderer cannot select or promote that state. Advanced controls are
collapsed by default and never expose arbitrary command or flag entry.

## Home Wireframe

```text
+----------------------------------------------------------------+
| Haven 42                 Local | No repository | Network: off   |
|----------------------------------------------------------------|
| What do you want to do?                                        |
|                                                                |
| [ Chat with local AI ]       [ Work on a software project ]    |
| Ask questions privately       Plan, review, validate, change   |
|                                                                |
| [ Create an image ]          [ Manage models and providers ]   |
| Requires configured provider  Hardware, evidence, downloads    |
|                                                                |
| [ Check system readiness ]                                    |
+----------------------------------------------------------------+
```

Cards show `available`, `configuration-required`, `unavailable`, `blocked`, or
`failed` from runtime discovery. A blocked card may explain remediation but
cannot start execution.

## Chat Wireframe

```text
+----------------------------------------------------------------+
| Chat                                      Provider: Local Ollama|
| Execution: user-controlled local network | Repository: none    |
|----------------------------------------------------------------|
| Conversation                                                   |
|                                                                |
| [ Ask anything...                                         ]    |
| [Attach user content]                              [Send]       |
+----------------------------------------------------------------+
```

The provider and execution location remain visible. Attaching content creates
a user-content read grant; it never grants repository access. Conversation
persistence is off unless a future explicit retention feature is admitted.

## Software Wireframe

```text
+----------------------------------------------------------------+
| Software project                                               |
| Repository: Not selected                    [Select folder]     |
|----------------------------------------------------------------|
| What would you like to do?                                     |
| [Understand] [Plan] [Review] [Validate] [Approved change]      |
|                                                                |
| Available actions come from config/workflows.json.              |
| Write-capable actions always show a dry run and approval.       |
+----------------------------------------------------------------+
```

The renderer receives an opaque path-grant identifier, not unrestricted path
authority. Workflow safety levels and policy determine disclosure and approval.

## Image Wireframe

```text
+----------------------------------------------------------------+
| Create an image                    Provider: Configuration needed|
|----------------------------------------------------------------|
| Prompt                                                         |
| [ Describe the image...                                   ]    |
| Output: application-owned artifacts                             |
|                                                                |
| [Set it up for me] [Use existing provider] [Not now]            |
| [Customize advanced settings]          [Review and generate]    |
+----------------------------------------------------------------+
```

The generate action stays disabled until exact provider discovery passes.
Checkpoint downloads, external access, and artifact writes are separately
disclosed. Partial Windows AMD evidence does not promote that native profile.

## Action Review

Before any effectful task, the review screen displays:

- operation name and execution location;
- provider and whether it is local, user-controlled network, or external;
- network use and model downloads;
- repository reads and writes;
- artifact destination and other file writes.

The choices are **Go back** and **Approve and continue**. Approval is never
remembered, and any input, effect, operation, grant, session, or expiry change
invalidates it.

## Framework-Neutral Skeleton

`config/ui-navigation-contract.json` is the navigation and interaction source
of truth. `scripts/build-ui-view-model.py` joins it with capabilities, providers,
workflows, and an optional runtime availability report. Its output intentionally
contains no entry-point paths, commands, endpoints, credentials, approval token,
or execution authority. `runtimeAdmitted` and `executionEnabled` remain false.

React components should eventually render this view model. Tauri should provide
native folder selection and the independently validated IPC bridge. Neither is
allowed to reinterpret evidence states or bypass the desktop policy.

## Acceptance Criteria

- First run works without a repository, provider, download, or network probe.
- Guided setup, existing setup, and not-now use one shared contract across capabilities.
- Guided and existing paths both expose structured advanced settings and state-impact review.
- Deterministic navigation is always available without an LLM.
- Every home action resolves to a registered capability or UI-ready workflow.
- Provider discovery may reduce or improve availability but cannot promote an
  unknown or policy-blocked operation.
- Effectful work passes through disclosure and approval before execution.
- Results use typed artifacts and versioned events.
- UI state contains no raw command, executable path, credential, endpoint, or
  reusable approval.
- Desktop runtime files remain absent until their separate admission gates pass.
