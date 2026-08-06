# Portable Development Package

Haven 42 can be built as an unsigned PyInstaller one-folder development package on Windows, Linux, and macOS. It reuses the exact browser UI and Python service from source. The package adds no installer, system service, administrator requirement, global Python requirement, Tauri/Rust runtime, updater activation, or machine-modification capability.

## Build And Run

Install the exact hash-locked build dependencies in an isolated environment, then run:

```text
python -m pip install --require-hashes -r package/requirements-build.txt
python scripts/build-portable-development-package.py
```

A source export without `.git` must provide `HAVEN42_SOURCE_COMMIT` and
`HAVEN42_SOURCE_TREE_STATE`. A modified export must additionally provide the
SHA-256 of its exact source archive as `HAVEN42_SOURCE_SNAPSHOT_SHA256`.
Provenance then records the base commit, `modified-uncommitted`, the snapshot
digest, and `commitIsExactSource: false`; it must never present that artifact
as an exact commit build.

The ordinary build verifies the committed protected-resource manifest and
fails closed instead of regenerating trust metadata. After reviewing an
intentional change to an allowlisted UI or data resource, update only that
manifest explicitly and review its diff before building:

```text
python scripts/build-portable-development-package.py --update-resource-integrity
```

Protected resources and the manifest use repository-enforced LF bytes so
caller Git line-ending settings cannot silently change packaged identities.

The native executable is under `dist/portable/bundle/haven42/`. It accepts `--port` and `--no-open`. Port `0` asks the operating system for an unused loopback port. The build also creates a platform archive and evidence in `dist/portable/artifacts/`.

The builder overrides PyInstaller's per-user configuration directory and keeps
its cache beneath the selected ignored build output. A package build therefore
does not depend on or create Haven-specific PyInstaller state in the user's
profile.

Build outputs are restricted to the repository's ignored `dist` tree. Before
inventory or archive creation, every package link must resolve inside the
one-folder bundle; an external or missing target fails the build.

These outputs are unsigned development artifacts. They are not installers or production releases. Antivirus and operating-system reputation prompts are possible because signing and notarization are deliberately outside this batch.

Windows builds also embed deterministic executable identity metadata:
ProductName and FileDescription `Haven 42`, ProductVersion and FileVersion
`0.4.0-alpha.1`, and OriginalFilename `haven42.exe`. The Alpha build reads this metadata
from `package/haven42-version-info.txt` and independently parses the emitted PE
resources before it can create the archive. This identity metadata is not a
digital signature and conveys no publisher trust.

## Security Boundary

The executable binds only to `127.0.0.1`. Automatic browser launch accepts only the server's internally constructed IPv4-loopback HTTP origin and numeric port. Windows delegates that URL to the registered operating-system association. macOS invokes fixed `/usr/bin/open`; Linux prefers fixed `/usr/bin/gio` and falls back to fixed `/usr/bin/xdg-open`. Unix launch uses argument arrays with `shell=False`, a minimal inherited environment, and a fixed `/usr/bin:/bin` search path; `BROWSER`, Python injection variables, dynamic-loader variables, and other unneeded caller values are not passed. Linux application lookup uses only the fixed system-owned `/var/lib/flatpak/exports/share`, `/var/lib/snapd/desktop`, `/usr/local/share`, and `/usr/share` roots so system Flatpak browsers work on immutable desktops such as Bazzite and Snap browsers work on Ubuntu, while any caller-supplied `XDG_DATA_DIRS` is discarded. A launcher counts as successful only after it exits successfully or remains running through the bounded confirmation window; an immediate nonzero exit or process error advances to the next admitted Linux launcher. If no admitted opener is available or launch fails, the server remains available and prints the exact URL for manual use. No user value becomes an executable, argument, or browser command.

Frozen resources are limited to three UI files and six server-owned data files. The data allowlist includes the model recommendations, evidence catalog, agent-surface capability and solution matrices, installation registry, and read-only workflow registry. A build-generated manifest binds every allowed resource by relative path, size, and SHA-256. Startup fails closed if the embedded manifest or any listed resource is malformed, missing, changed, or joined by an unexpected file in the protected resource roots. HTTP routing independently allowlists the three asset paths; no general filesystem serving exists.

The packaged UI preserves the source attachment boundary: only explicitly
selected UTF-8 `.txt`/`.md`/`.csv`/`.json`, the admitted inert
`.cs`/`.py`/`.js`/`.jsx`/`.ts`/`.tsx`/`.java`/`.go`/`.rs`/`.sql`/`.tf`
source-text set, and browsed or clipboard-pasted PNG screenshots enter
browser/process memory. Screenshot selection defaults to two per task and may
be set from one through four without changing the absolute 8-MiB combined and
33.5-million decoded-pixel ceilings. The loopback service revalidates names,
media types, exact byte counts, text limits, PNG structure and CRCs, screenshot
count, dimensions and per-image/combined pixel budgets, and warned
submit-confirmed private-network transfer. Image-input support remains
visibly unverified per model. No path, directory scan, temporary file, browser
storage, broader parser, or persistent index is added by packaging.

A sanitized physical Ubuntu x86_64 desktop/default-Firefox review of the exact
post-merge `haven42-Linux-X64-unsigned-development` artifact from workflow run
`30482923868` passed checksum and artifact verification, automatic browser
launch, loopback serving, native clipboard PNG paste, mixed admitted-file
selection, default and advanced screenshot limits, atomic rejection, cleanup,
normal shutdown, and port release. No prompt or attachment was sent during
that cell, and no selected content, endpoint, username, local path, or machine
identifier was retained. This adds physical Linux development evidence; it
does not replace the remaining physical macOS gate or promote signing,
installation, updates, or production distribution.

The service starts no child process except the already constrained, fixed-command readiness probes owned by the existing system-readiness registry. It exposes no arbitrary process, shell, filesystem, installer, or updater command. Shutdown is a same-origin JSON POST protected by the unpredictable in-memory session token. Models used by the session must be unloaded and verified before shutdown is accepted.

## Validation And Evidence

`scripts/test-portable-package.py` starts both source and native packaged runtimes on operating-system-selected loopback ports. It compares capability, update, privacy, committed-assurance, and browser-asset results; checks security headers and Host rejection; rejects missing shutdown authority, foreign origins, wrong content types, and unexpected shutdown fields; verifies packaged integrity state; invokes protected shutdown; and requires a clean native exit. It also exercises relocation into a path with spaces, startup from a read-only copied package, recovery after abruptly terminating the test-owned native process, hostile inherited environment values, repeated startup/shutdown, and occupied-port failure. Full validation runs the dependency-free source Chromium flow on Windows, Linux, and macOS. Each native packaging job repeats it against the packaged executable, including the read-only assurance panel, unified attachment picker, hostile atomic selection, task locking, compact layout, provider disclosure, cleanup, and typed results. The local-web security suite separately injects each platform launcher dependency, proves strict loopback-URL rejection, verifies fixed macOS/Linux executable and argument selection, confirms `shell=False`, and proves that a hostile `BROWSER` or caller `PATH` is omitted without opening a real browser. Disposable copied packages must fail before serving when a resource is changed, missing, unexpected, replaced by duplicate/absolute/traversal manifest records, or redirected through a symbolic link.

An additional 2026-08-03 physical Windows 11 x64 cell rebuilt the unsigned
package with the locked Python 3.14.6/PyInstaller 6.21.0 toolchain, then ran
that same parity, integrity, and lifecycle suite under a non-administrator
PowerShell 5.1 account on an Intel Arc B580 machine. The bounded display-class
registry fallback reported the Intel accelerator without elevation or raw
registry output, and readiness declared every network, file, installation,
elevation, service, and driver effect false. This is development evidence, not
an Intel image-provider package admission or a production-readiness claim.

On 2026-08-04, a second unsigned Windows x64 build used the same locked
Python 3.14.6/PyInstaller 6.21.0 inputs from a privacy-scanned modified-source
snapshot. Provenance recorded the base commit, `modified-uncommitted`, exact
snapshot SHA-256, and `commitIsExactSource: false`. Artifact, checksum,
inventory, notice, SBOM, archive, source-versus-package parity, relocation,
read-only-startup, hostile-environment, lifecycle, collision, integrity, and
shutdown checks passed on the Windows NVIDIA build host. The exact verified
archive bytes then passed an independent non-administrator Windows
PowerShell 5.1 smoke on the physical Intel host, including loopback binding,
security headers, package integrity, disabled update activation, authorized
shutdown, model cleanup, and zero process exit. This remains unsigned local
development evidence and does not grant release or production authority.

On Ubuntu hosts where Chromium is strictly confined as a Snap, the browser
test places only its disposable profile under Chromium's user-owned Snap
common directory so both processes can observe `DevToolsActivePort`; the
profile is removed during the same bounded cleanup path.

`scripts/verify-portable-development-artifacts.py` rejects unsafe archive paths, links, encrypted ZIP entries, duplicate or case-colliding members, unsupported archive shapes, excessive member count, oversized members or archives, checksum gaps, evidence symlinks, evidence gaps, unexpected platform/architecture/dependency records, malformed provenance/SBOM/inventory documents, notice omissions, target-name mismatch, unclassified packaged files, runtime-component coverage differences, and any mismatch between the archive and its full file inventory.

The GitHub Actions packaging matrix has read-only repository permission, does not persist checkout credentials, pins the official `setup-python` action by immutable commit, selects Python 3.14.6 on every runner, pins PyInstaller, builds independently on each native operating system, runs the parity/smoke test, and retains artifacts for seven days. It does not publish a GitHub Release.

The native runner labels and Python source archives are also fixed:

| Target | Runner | Official Python archive | SHA-256 |
| --- | --- | --- | --- |
| Windows x64 | `windows-2025` | `python-3.14.6-win32-x64.zip` | `dc722964ab28f81f6a0c753ee960871f045d363568f4fb7626cc02c1e0caa1e9` |
| Linux x64 | `ubuntu-24.04` | `python-3.14.6-linux-24.04-x64.tar.gz` | `29dc7f3887a430fe7a0005fee4732b00be1bbed5bf21aa1e43f8d947eb1b9f61` |
| macOS arm64 | `macos-15` | `python-3.14.6-darwin-arm64.tar.gz` | `7ed5b5c399a38b9b5b1bbb70a454c2ac8b0548cd0610871ea443c4747468e97c` |

The identities come from the official
[`actions/python-versions` 3.14.6
release](https://github.com/actions/python-versions/releases/tag/3.14.6-27283001424).
Hosted builds reject missing or different matrix identities and record the
selected release tag, archive, and digest in provenance. Local builds are
explicitly recorded as `local-unverified`.

Each artifact set contains:

- the native unsigned development archive;
- `SHA256SUMS`;
- an allowlisted platform-specific build-tool inventory plus embedded CPython runtime identity;
- generated third-party notices from installed distribution metadata;
- a CycloneDX JSON SBOM;
- a complete package file inventory;
- an exact runtime-component inventory that binds every file to Haven 42 or an
  explicit CPython, OpenSSL, libffi, Microsoft, or unresolved platform-runtime
  group;
- hash-verified CPython 3.14.6 bundled-license evidence, the Apache 2.0
  license text used by OpenSSL 3.5.7, and the exact libffi 3.4.4 MIT license;
- the Haven 42 MIT license, generated third-party notice, and those exact
  upstream license files inside the extracted package as well as the sidecar
  evidence set;
- unsigned build provenance binding a clean build to its exact source commit or a modified development build to its base commit plus exact source-snapshot SHA-256, alongside OS, architecture, Python, PyInstaller, workflow identity, and explicit absence of platform signing, notarization, an in-build attestation, and release publication.

The local build remains unattested. Separately, an approved future push to
`main` can run the least-privilege hosted job documented in
`docs/artifact-attestation.md`. That job reverifies all three native artifact
sets and creates GitHub/Sigstore build provenance for only the unsigned archive
digests. The external attestation does not alter the package, sign executable
code, notarize macOS software, publish a Release, or authorize updater use.

The build dependency file pins every admitted wheel by SHA-256 for the hosted Windows x64, Linux x64, and macOS universal runner paths. Evidence generation reads only the explicit platform allowlist, so unrelated caller-environment packages cannot enter the inventory or notices. The reviewed license expressions remain evidence for review, not a legal conclusion.

The runtime-component inventory carries exact path, digest, size, and file
count coverage. It marks every upstream component ineligible for Haven 42
signing and drives matching SBOM and notice rows. On Windows it also records
the official Python installer/SBOM and immutable CPython, OpenSSL, and libffi
source provenance. Both
`runtimeRedistributionCleared` and production promotion remain false. GitHub
Actions run `30297195387` reproduced and verified the unsigned development
package on clean hosted Windows, Linux, and macOS runners at exact main commit
`04baca39b26ec58c189a6ae21ea78b507444e9fa`, including the Windows component
classifier that rejects host-derived API-set/UCRT files. Exact applicable
Microsoft redistribution terms and repetition for any later immutable release
candidate are still required before public binary promotion.

## Installer And Updater Foundations

The existing installation broker remains simulation-only and explicitly rejects renderer-supplied package paths and hashes as unknown authority. Install, upgrade, and uninstall planning require compatible simulated current state and an exact promotion-evidence shape, but even complete booleans cannot grant authority. The updater remains offline-only: byte-policy tests include same-size mutation and truncated-package rejection, while the separate 45-case lifecycle simulator covers compatibility, healthy and failed health checks, interrupted phase-specific recovery, candidate-digest replay, retained-version collision, rollback, retention, disabled mode, and hostile journals. Neither policy can query a release, download, write, stage, activate, roll back, clean, install, terminate a process, or modify a machine. The portable package adds no call path to either foundation.

Signing, notarization, installer creation, public release publication, automatic updates, and production-readiness claims remain explicit stop gates.
