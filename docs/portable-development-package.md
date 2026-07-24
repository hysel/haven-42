# Portable Development Package

Haven 42 can be built as an unsigned PyInstaller one-folder development package on Windows, Linux, and macOS. It reuses the exact browser UI and Python service from source. The package adds no installer, system service, administrator requirement, global Python requirement, Tauri/Rust runtime, updater activation, or machine-modification capability.

## Build And Run

Install the exact hash-locked build dependencies in an isolated environment, then run:

```text
python -m pip install --require-hashes -r package/requirements-build.txt
python scripts/build-portable-development-package.py
```

The native executable is under `dist/portable/bundle/haven42/`. It accepts `--port` and `--no-open`. Port `0` asks the operating system for an unused loopback port. The build also creates a platform archive and evidence in `dist/portable/artifacts/`.

These outputs are unsigned development artifacts. They are not installers or production releases. Antivirus and operating-system reputation prompts are possible because signing and notarization are deliberately outside this batch.

## Security Boundary

The executable binds only to `127.0.0.1`. The browser URL is constructed from the server's actual loopback address and numeric port, then passed to the standard browser controller as a new tab. No user value becomes an executable or browser command.

Frozen resources are limited to three UI files and three server-owned data files. A build-generated manifest binds every allowed resource by relative path, size, and SHA-256. Startup fails closed if the embedded manifest or any listed resource is malformed, missing, changed, or joined by an unexpected file in the protected resource roots. HTTP routing independently allowlists the three asset paths; no general filesystem serving exists.

The service starts no child process except the already constrained, fixed-command readiness probes owned by the existing system-readiness registry. It exposes no arbitrary process, shell, filesystem, installer, or updater command. Shutdown is a same-origin JSON POST protected by the unpredictable in-memory session token. Models used by the session must be unloaded and verified before shutdown is accepted.

## Validation And Evidence

`scripts/test-portable-package.py` starts both source and native packaged runtimes on operating-system-selected loopback ports. It compares capability, update, privacy, and browser-asset results; checks security headers and Host rejection; rejects missing shutdown authority, foreign origins, wrong content types, and unexpected shutdown fields; verifies packaged integrity state; invokes protected shutdown; and requires a clean native exit. Disposable copied packages must fail before serving when a resource is changed, missing, unexpected, or replaced by a traversal manifest record.

`scripts/verify-portable-development-artifacts.py` rejects unsafe archive paths, links, duplicate or case-colliding members, unsupported archive shapes, checksum gaps, evidence gaps, malformed provenance/SBOM/inventory documents, notice omissions, and any mismatch between the archive and its full file inventory.

The GitHub Actions packaging matrix has read-only repository permission, does not persist checkout credentials, pins PyInstaller, builds independently on each native operating system, runs the parity/smoke test, and retains artifacts for seven days. It does not publish a GitHub Release.

Each artifact set contains:

- the native unsigned development archive;
- `SHA256SUMS`;
- an allowlisted platform-specific build-tool inventory plus embedded CPython runtime identity;
- generated third-party notices from installed distribution metadata;
- a CycloneDX JSON SBOM;
- a complete package file inventory;
- unsigned build provenance binding the exact source commit, OS, architecture, Python, PyInstaller, workflow identity, and explicit absence of signing, notarization, attestation, and release publication.

The build dependency file pins every admitted wheel by SHA-256 for the hosted Windows x64, Linux x64, and macOS universal runner paths. Evidence generation reads only the explicit platform allowlist, so unrelated caller-environment packages cannot enter the inventory or notices. The reviewed license expressions remain evidence for review, not a legal conclusion.

## Installer And Updater Foundations

The existing installation broker remains simulation-only and now explicitly rejects renderer-supplied package paths and hashes as unknown authority. The existing updater policy remains offline-only: its hostile suite includes same-size mutation and truncated-package rejection, but it cannot query a release, download, stage, activate, roll back, or modify a machine. The portable package adds no call path to either foundation.

Signing, notarization, installer creation, public release publication, automatic updates, and production-readiness claims remain explicit stop gates.
