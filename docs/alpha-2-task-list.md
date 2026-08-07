# Haven 42 0.4 Alpha 2 task list

This checklist controls preparation of the unsigned Haven 42
`0.4.0-alpha.2` prerelease. Alpha 2 is intended to provide separate Windows
x64 and Linux x64 portable packages for invited testing. It is not an
installer, signed product, stable release, or production-readiness claim.

Completing a task records only that task's stated evidence. It does not promote
another operating system, distribution, accelerator, model, or package.

## Fixed Alpha 2 boundaries

- Keep the shared browser UI and minimum trusted PyInstaller launcher/service.
- Keep Tauri and Rust unadmitted.
- Expose only Chat, Writing, and Summarization.
- Distribute separate unsigned Windows x64 and Linux x64 portable archives.
- Bundle no Ollama runtime, model, driver, package manager, or other external
  software inside the Haven 42 application archive.
- Download only exact registered artifacts after the tester reviews the plan
  and gives explicit, single-use permission.
- Store Haven-managed runtimes, models, temporary files, and state only beside
  the extracted application. Keep sanitized logs in the existing separate
  sibling log directory.
- Require no administrator or root access. Do not change drivers, firmware,
  package-manager state, operating-system updates, services, firewall rules,
  certificate stores, login items, shell profiles, or global environment.
- Bind the Haven service and Haven-managed Ollama only to IPv4 loopback.
- Keep signing, installers, automatic updates, machine-wide modification,
  stable promotion, and production claims outside Alpha 2.
- Stop release preparation on any unresolved security or privacy finding.

## Evidence labels

- **Supported Alpha**: the exact package and release candidate passed every
  required native, security, lifecycle, and user-flow gate on that target.
- **Tested**: a dated exact target passed its stated cells, but Haven does not
  promise broader or future compatibility.
- **Experimental**: useful evidence exists, but one or more release gates are
  incomplete or the distribution changes continuously.
- **Blocked**: a named failure or missing prerequisite prevents promotion.

## Phase 1: Release scope and control

- [ ] Record the owner-approved Alpha 2 capabilities, platforms, audience, and
  stop boundaries in a versioned release contract.
- [ ] Freeze `0.4.0-alpha.1`; never replace its tag or published assets.
- [ ] Use `0.4.0-alpha.2` consistently in code, package metadata, evidence,
  documentation, issue forms, and release notes.
- [ ] Define these candidate assets:
  - `haven42-0.4.0-alpha.2-windows-x64-unsigned.zip`
  - `haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz`
- [ ] Define separate checksums, inventories, notices, SBOMs, provenance, and
  known-limitations evidence for each archive.
- [ ] Update the release gate so one platform cannot inherit another
  platform's passing result.

## Phase 2: Shared cross-platform product boundary

- [ ] Separate Windows-specific managed-setup operations from the shared
  readiness, planning, approval, progress, recovery, and UI contracts.
- [ ] Add an explicit platform adapter interface with an allowlist of supported
  operations; reject unknown platforms and operation identifiers.
- [ ] Preserve exact source-versus-package behavior for Chat, Writing,
  Summarization, attachments, logs, metrics, provider switching, and cleanup.
- [ ] Keep all renderer input untrusted and keep process, path, download,
  integrity, and lifecycle authority in the local engine.
- [ ] Add hostile tests proving that renderer or model content cannot choose a
  command, executable, environment variable, destination, archive member,
  local path, or process to terminate.
- [ ] Confirm Windows behavior remains unchanged while Linux support is added.

## Phase 3: Linux system and distribution detection

- [ ] Detect Linux x64 through bounded operating-system APIs and `/etc/os-release`
  without invoking a shell or trusting environment-provided paths.
- [ ] Report the distribution name/version, kernel, architecture, desktop,
  Wayland/X11 session, CPU, logical processors, RAM, free space, and detected
  accelerator in novice-friendly language.
- [ ] Detect glibc and required shared-library compatibility before setup.
- [ ] Detect NVIDIA, AMD, Intel, and CPU-only profiles without requiring root.
- [ ] Record driver and runtime versions when bounded read-only probes can
  obtain them; otherwise show **Unavailable** rather than estimating.
- [ ] Show only components applicable to the detected platform and accelerator.
- [ ] Deny managed setup below the approved CPU, RAM, storage, architecture, or
  runtime-compatibility threshold with a clear remediation message.
- [ ] Add deterministic fixtures for missing, malformed, spoofed, oversized,
  and conflicting distribution and hardware information.

## Phase 4: Linux component supply chain

- [ ] Register an exact official standalone Linux x64 Ollama artifact with
  immutable version, byte length, SHA-256, source, license, and provenance.
- [ ] Register every optional accelerator supplement independently; never
  infer that a Windows runtime artifact applies to Linux.
- [ ] Register only prequantized model artifacts with exact manifest and layer
  digests, sizes, licenses, capability evidence, and hardware limits.
- [ ] Complete the exact packaged dependency and license review for both Haven
  archives and every downloadable managed component.
- [ ] Reject redirects, changed sizes/digests, unregistered archive members,
  links, devices, sockets, traversal, absolute paths, collisions, expansion
  abuse, and unsupported file types.
- [ ] Prove that component downloads, staging, extraction, models, temporary
  files, and runtime state remain under the extracted Haven 42 directory.
- [ ] Keep failed, cancelled, or interrupted transactions recoverable without
  accepting partially verified content.
- [ ] Generate component descriptions that explain what is downloaded, why it
  is needed, its version, size, source, and removal behavior before approval.

## Phase 5: Linux managed runtime and lifecycle

- [ ] Start the exact registered Ollama executable directly without `sudo`, a
  shell, a package manager, `systemd`, a desktop autostart entry, or global
  installation.
- [ ] Use a minimal child environment with managed home, model, cache, config,
  and temporary directories beneath Haven's portable data directory.
- [ ] Bind the managed provider only to `127.0.0.1` on an engine-selected port.
- [ ] Track the exact owned process tree and never stop a process by name.
- [ ] Stop all Haven-owned processes after normal exit, cancellation, setup
  failure, browser closure followed by app shutdown, crash recovery, and
  termination of the Haven launcher.
- [ ] Verify port closure, model unload, and absence of surviving managed
  processes after every lifecycle test.
- [ ] Revalidate receipts, file inventories, model identity, paths, platform,
  hardware plan, and loopback health before reusing an existing setup.
- [ ] Skip downloads and setup work when every required managed component is
  already present and valid.
- [ ] Return to guided setup when a required local component is missing,
  changed, corrupt, incompatible, or unable to start.
- [ ] Implement marker-owned uninstall that removes only Haven-managed
  components and preserves the application and sanitized logs unless the user
  separately chooses to remove logs.
- [ ] Handle read-only directories, `noexec` mounts, full disks, permission
  failures, signals, stale ports, stale receipts, and abrupt power loss safely.

## Phase 6: Hardware-aware Linux model selection

- [ ] Use the same owner-approved hardware-derived automatic-selection policy
  on Windows and Linux; do not change the default model without explicit owner
  approval.
- [ ] Select the largest admitted prequantized model that fits conservative
  RAM, accelerator memory, context, concurrency, and storage budgets.
- [ ] Prefer a smaller registered model over local quantization when it fits.
- [ ] Keep automatic quantization disabled until its separate provenance,
  quality, temporary-storage, recovery, and compatibility gates pass.
- [ ] Require nonzero accelerator residency when an accelerated profile is
  promised; never silently report CPU fallback as GPU success.
- [ ] Provide a safe CPU-only path for eligible machines without an admitted
  accelerator.
- [ ] Keep unknown GPU/driver combinations manual or experimental rather than
  extrapolating from another device.
- [ ] Add exact fixtures for multi-GPU selection, shared memory, missing VRAM,
  low memory, low storage, unsupported drivers, and CPU-only systems.

## Phase 7: Novice Linux experience

- [x] Replace the fragmented Alpha 1 dashboard styling with the owner-reviewed
  conversation-first dark interface, consolidated status presentation, unified
  text-backed status indicators, and quieter system details requested by issue
  #73. This records implementation only, not reporter acceptance.
- [x] Add the self-assessed WCAG 2.1 AA interface changes and separate local
  accessibility statement: semantic landmarks and headings, labeled controls,
  high-contrast focus, deterministic contrast checks, 44-pixel primary
  targets, reduced-motion and forced-color support, described connection
  errors, and bounded live announcements.
- [x] Address issue #72 by shortening the public problem form and adding an
  explicit, user-triggered helper that prepares only the Haven 42 version,
  operating-system version/build, architecture, memory, and graphics details.
  The reviewable text excludes identity, addresses, local paths, conversation
  content, and attachment names; it is never uploaded automatically.
- [x] Close issue #73 by owner approval with a clear note that the redesigned
  interface and accessibility improvements will be available in Alpha 2. Any
  remaining Alpha 2 accessibility or usability barrier should be reported with
  the specific screen and action involved; reporter validation was not claimed.
- [x] Close issue #74 by owner approval after implementing its reusable,
  section-scoped help system for Chat,
  Models, System, Technical details, and About. Each short tour has an
  independent first-visit flag, an always-available manual Help entry point,
  Back, Next, Skip, close, and Escape controls, focus containment and return,
  reduced-motion behavior, and no cross-section navigation. This records local
  implementation and automated validation only; reporter acceptance and Alpha
  2 publication remain separate. The published Alpha 1 package remains
  unchanged.
- [ ] Use the existing guided-first language and explain Linux terms only when
  needed.
- [ ] Show one recommended setup, with advanced controls collapsed by default.
- [ ] Ask explicit permission immediately before downloads or process start;
  bind approval to the exact component list and expire it after use.
- [ ] Display overall and per-component progress for download, verification,
  extraction, model preparation, startup, and private local validation.
- [ ] Explain why Haven will not install or repair GPU drivers automatically
  and provide distribution-appropriate manual guidance.
- [ ] Open the default browser through the existing fixed, shell-free Linux
  opener policy and always provide a usable manual loopback URL fallback.
- [ ] Make Back, Cancel, Retry, Troubleshooting, local/external switching, and
  uninstall available at the relevant stages.
- [ ] After verified managed setup, open the text workspace directly on later
  launches without showing a redundant provider-connection screen.
- [ ] Ensure GNOME and KDE layouts, scrolling, dialogs, file selection,
  clipboard paste, focus, keyboard navigation, and text scaling remain usable.
- [ ] Use human-readable errors while retaining only sanitized stable reference
  codes in logs and support reports.

## Phase 8: Shared capability and privacy validation

- [ ] Validate automatic routing plus explicit Chat, Writing, and
  Summarization on Windows and every promoted Linux target.
- [ ] Validate tokens/second, prompt/output/session tokens, CPU, RAM, GPU, and
  accelerator-memory reporting; show **Unavailable** for unsupported metrics.
- [ ] Validate Stop, retry, New task, prompt recall, model unload, and idle
  cleanup without retaining prompt or response content.
- [ ] Validate bounded text/source attachments, PNG browse/paste, disguised-file
  rejection, removal, private-network disclosure, and memory-only cleanup.
- [ ] Validate external Ollama HTTP-loopback and authenticated HTTPS/private-LAN
  paths independently from managed local setup.
- [ ] Verify that local API keys remain memory-only and never enter logs,
  support reports, process arguments, environment variables, or URLs.
- [ ] Verify sanitized log rotation, disk-full behavior, abnormal-shutdown
  evidence, support-report export, clear logs, and uninstall separation.
- [ ] Run the response-guardrail matrix against every automatically selectable
  exact model without changing model eligibility from subjective quality alone.

## Phase 9: Distribution compatibility matrix

For every row, record the exact ISO/image identity, installation date, package
set or immutable image revision, kernel, glibc, desktop, session type, hardware,
Haven commit, archive digest, model digest, and pass/fail cells. Do not record a
hostname, username, address, personal path, prompt, response, or API key.

- [ ] Ubuntu 26.04 LTS x64 with GNOME: complete the full package, guided setup,
  reuse, external provider, capability, attachment, metrics, lifecycle,
  uninstall, and privacy sequence.
- [ ] Ubuntu 24.04 LTS x64 with GNOME: complete the same sequence as the oldest
  supported compatibility baseline.
- [ ] Debian 13.6 stable x64 with GNOME: complete the same sequence as an
  independent upstream Debian-family baseline; begin as **Tested** and promote
  only from its own exact package and lifecycle evidence.
- [ ] Linux Mint x64 with Cinnamon: complete the same sequence before any
  **Supported Alpha** label.
- [ ] Pop!_OS 24.04 LTS x64 with COSMIC: complete the same sequence, including
  COSMIC browser launch, file selection, clipboard, permissions, lifecycle,
  and generic-versus-NVIDIA image behavior; begin as **Tested**.
- [ ] Fedora Workstation 44 x64 with GNOME: complete the same sequence and begin
  as **Tested** or **Experimental**.
- [ ] Bazzite x64 with KDE Desktop: test the immutable host, Flatpak browser,
  executable permissions, local-folder-only setup, lifecycle, and uninstall;
  never use `rpm-ostree` or package layering.
- [ ] CachyOS x64 with KDE Plasma: record the exact rolling snapshot and test
  archive compatibility, browser launch, managed setup, lifecycle, and update
  drift; begin as **Experimental**.
- [ ] Arch Linux x64 with one declared desktop: record the exact rolling
  snapshot and test the advanced-user path; begin as **Experimental**.
- [ ] Repeat a CPU-only or virtual-GPU package/lifecycle cell across each
  distribution without claiming accelerator evidence.
- [ ] Record every failure and retain the lower label until the exact failed
  release candidate passes again.

## Phase 10: Native accelerator matrix

- [ ] Windows 11 x64 NVIDIA: repeat the complete current-candidate CUDA cell.
- [ ] Windows 11 x64 AMD: repeat the complete current-candidate ROCm cell.
- [ ] Windows 11 x64 Intel: repeat the exact admitted Arc/Vulkan cell.
- [ ] Windows 11 x64 CPU-only or constrained profile: validate threshold,
  automatic model selection, inference, metrics, and cleanup.
- [ ] Ubuntu Linux x64 NVIDIA: validate exact CUDA driver, runtime, model,
  nonzero residency, Chat/Writing/Summarization, metrics, unload, and shutdown.
- [ ] Bazzite NVIDIA: treat as a separate exact profile and promote only after
  the immutable-host lifecycle and browser cells pass.
- [ ] Native Linux Intel: validate only the exact available Intel GPU,
  distribution, driver, runtime, and model combination.
- [ ] Native Linux AMD: keep acceleration unpromoted until a physical native
  Linux AMD cell passes; WSL2 evidence cannot substitute for it.
- [ ] Low-memory hardware: confirm the smaller admitted model is chosen without
  quantization or an unsafe overcommit.
- [ ] Mixed-GPU hardware: confirm recommendation, execution backend, metrics,
  and evidence all refer to the same selected accelerator.

## Phase 11: Packaging and supply-chain evidence

- [ ] Build Linux on the oldest admitted hosted baseline and verify its glibc
  and shared-library floor on every distribution target.
- [ ] Package Linux as a tar archive that preserves executable permissions and
  rejects links, devices, unsafe modes, absolute paths, and traversal.
- [ ] Keep Windows packaging as a bounded ZIP with its existing hostile archive
  controls.
- [ ] Verify package relocation, spaces and Unicode in the extraction path,
  read-only startup behavior, repeated lifecycle, occupied ports, hostile
  environment variables, and abrupt exit on both platforms.
- [ ] Generate exact package file inventories, dependency inventories,
  third-party notices, CycloneDX SBOMs, checksums, and unsigned provenance.
- [ ] Verify that each archive contains the Haven 42 license and every required
  redistributed dependency license.
- [ ] Confirm no model, Ollama binary, driver, secret, local evidence, machine
  identity, test prompt, ignored output, `Haven42-Data`, or `Haven42-Logs`
  directory enters either archive.
- [ ] Run source-versus-package browser and API parity on Windows and Linux.
- [ ] Run the full repository gate once against the exact staged tree near
  completion, then bind hosted checks to the exact release commit.

## Phase 12: Security review

- [ ] Update the threat model for Linux process, filesystem, archive,
  permissions, signals, dynamic-loader variables, browser launch, and
  distribution-detection boundaries.
- [ ] Test symlink, hard-link, mount, case, Unicode, ownership, mode, special
  file, archive, race, path replacement, and cleanup attacks.
- [ ] Test command/argument/environment injection and hostile child output.
- [ ] Test download origin, redirect, certificate, size, digest, archive,
  interrupted-transfer, and replay failures.
- [ ] Test loopback binding, Host/Origin validation, request-token protection,
  provider scope, API-key handling, and shutdown authority.
- [ ] Test attachment XSS, Markdown rendering, filename/type confusion,
  clipboard input, prompt injection, and log/support-report privacy.
- [ ] Run dependency vulnerability, secret, privacy, license, package, and SBOM
  reviews against the exact candidate.
- [ ] Fix every finding regardless of severity and repeat the affected checks.
- [ ] Record a zero-finding review for the exact staged tree before a large
  commit; stop and notify the owner if any finding remains.

## Phase 13: Documentation and tester support

- [ ] Update README, architecture, security documentation, roadmap, project
  status, changelog, release guide, tested-hardware matrix, and mapped wiki.
- [ ] Add a Linux novice quick start covering download, checksum verification,
  extraction, executable permission, launch, browser fallback, setup,
  troubleshooting, logs, uninstall, and complete folder removal.
- [ ] Publish an exact compatibility table using the four evidence labels and
  include the tested distribution revision/date.
- [ ] Explain that rolling-release results apply only to the recorded snapshot.
- [ ] Expand Alpha issue forms to collect operating system, distribution,
  version, desktop, session type, CPU/RAM/GPU, setup path, package digest, and
  sanitized error reference without collecting private content.
- [ ] Provide separate Windows and Linux download links, checksum commands,
  known limitations, and report-a-problem links.
- [ ] Review all novice-facing language and remove unexplained engineering
  terms, internal status language, stale versions, and obsolete package names.
- [ ] Verify documentation and wiki navigation, links, formatting, version
  consistency, and absence of trailing blank lines.

## Phase 14: Release-candidate closure

- [ ] Complete the exact Windows and Linux dependency/license audit, including
  all redistributed native libraries.
- [ ] Build both candidates from one clean, exact commit using pinned isolated
  toolchains; do not install build tools globally.
- [ ] Run the full local gate once against the exact candidate tree.
- [ ] Push one coherent branch and require every hosted Windows, Linux, macOS
  regression, package, CodeQL, privacy, and wiki check to pass.
- [ ] Re-run only genuinely failed or affected checks after a correction; do
  not weaken a gate to obtain a pass.
- [ ] Obtain owner review of the Windows and Linux user flows and release-page
  wording.
- [ ] Obtain explicit owner approval before tagging or publishing Alpha 2.
- [ ] Publish both unsigned archives as one GitHub prerelease with checksums,
  inventories, notices, SBOMs, provenance, limitations, and feedback links.
- [ ] Verify the immutable tag, asset names, sizes, digests, download links,
  issue forms, and public documentation after publication.
- [ ] Keep the prerelease flag and unsigned warnings visible; make no stable,
  signed, installer, universal-Linux, or production-readiness claim.

## External-machine schedule

Phases 1 through 8 and 11 through 13 can be developed and tested locally with
offline fixtures and hosted CI preparation. Native evidence is required before
promotion:

1. Run CPU/desktop compatibility VMs for every Phase 9 distribution.
2. Run the Windows NVIDIA, AMD, Intel, and constrained cells.
3. Run native Ubuntu NVIDIA and exact Linux Intel cells.
4. Run Bazzite NVIDIA separately because the passthrough GPU cannot be assigned
   to two virtual machines at the same time.
5. Add native Linux AMD only when appropriate physical hardware is available.
6. Run a final clean Windows and Linux candidate pass after all fixes are in
   the exact archives.
