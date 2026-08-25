# Desktop Storage, Updates, And Rollback

## Purpose

`config/desktop-storage-contract.json` defines where each class of Haven 42 data belongs on Windows, Linux, and macOS. The core-update contracts define the future immutable engine-update boundary, offline GitHub Release candidate check, native-verifier handoff, verifier and trust-root transitions, and effect-free lifecycle simulation. The policy scripts validate and model those inputs offline; they are not network clients, cryptographic verifiers, trust-store managers, downloaders, installers, activators, cleanup tools, or admitted desktop runtimes.

The central rule is simple: Haven 42-managed files stay inside the folder the
user extracted. The fixed mutable root is `Haven42-Data` beside the executable.
An application update may replace a versioned engine only inside that portable
boundary, and it must not own or silently change user-selected repositories or
inputs. Persistent secrets are not written to the portable folder.

## Native Path Resolution

The application resolves its portable installation root from the running
executable, not from an environment variable, registry entry, home directory,
or application-data directory. It canonicalizes that root before use and
rejects reparse-point or symbolic-link redirection. Native platform APIs remain
appropriate for user-selected external inputs, but those inputs stay in their
original locations.

- Windows managed state uses only `portable-install-root/Haven42-Data`. The former `%LocalAppData%/Haven42/alpha` path may be read only by the bounded legacy cleanup flow and is never a write target.
- Linux managed state uses only `portable-install-root/Haven42-Data`; XDG directories are not managed-write targets.
- macOS managed state uses only `portable-install-root/Haven42-Data`; Application Support, Caches, Documents, and Keychain are not managed-write targets.
- Tauri path helpers may implement native resolution, but the native bridge remains responsible for canonicalization, protected-directory checks, and path grants. See the [Tauri path API](https://v2.tauri.app/reference/javascript/api/namespacepath/).

## Ownership Boundaries

| Class | Examples | Update behavior |
| --- | --- | --- |
| Immutable engine | Desktop shell, packaged engine sidecar, bundled UI assets | Install as a complete version; never overwrite files in place. |
| User configuration | Preferences, provider references, policy choices | Preserve; migrate only through a compatible, reversible process. |
| User content | Repositories, selected inputs, generated artifacts | Remains user-owned and outside engine version directories. |
| Provider data | Ollama, ComfyUI, managed model files, provider caches | Preserve; remove only through an explicit provider cleanup preview. |
| Reconstructible cache | Download cache, rendered indexes, disposable extraction | May be cleaned while the application is stopped. |
| Update state | Verified downloads, staged versions, activation journal, rollback version | Preserve until activation and rollback retention rules permit cleanup. |
| Secrets | Provider tokens or credentials | Memory only by default; never ordinary JSON configuration or a file in `Haven42-Data`. |

Repositories remain where the user selected them. Desktop access uses the opaque path-grant rules in `config/desktop-ipc-contract.json`; the renderer never gains a raw-path execution surface.

## Platform Shape

The machine-readable contract records paths relative to the canonical portable
installation root rather than hard-coded absolute paths. The package does not
use an installer-managed application location.

On every platform, configuration, state, caches, models, generated artifacts,
update downloads, staged versions, and activation journals all remain beneath
`Haven42-Data`. Removing managed components uses a marker-owned, bounded,
link-free cleanup; after Haven 42 is closed, deleting the extracted folder
removes the application itself. Linux and macOS remain future packages, but
their storage contracts enforce the same portable boundary.

## Immutable Update Manifest

The future updater reads a strict, signed schema-v1 manifest from an immutable GitHub Release. GitHub Releases bind packaged assets to a tagged release; see [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

Each platform asset must record its operating system, architecture, target triple, package type, exact byte size, SHA-256, signature or attestation, SBOM, and third-party notices. The manifest also binds the release to a full commit SHA and declares compatible IPC, workflow-envelope, artifact, engine API, configuration, and operating-system versions.

The updater must never use unattended `git pull`, a moving branch, an unverified redirect, or an asset selected only by filename.

## Activation And Rollback

The required sequence is:

1. Check only when the user opted into stable-release checks; the default is disabled.
2. Verify the manifest before selecting or downloading an asset.
3. Match OS, architecture, target triple, compatibility, and storage headroom.
4. Download into the platform update-download directory.
5. Verify byte size, SHA-256, signature or attestation, provenance, SBOM, and notices.
6. Stage the complete version beside—not over—the active engine.
7. Run compatibility and staged health checks.
8. Atomically select the new version and journal the previous known-good version.
9. Run post-activation health checks; automatically restore the prior version on failure.
10. Clean old retained versions only through a separate bounded retention policy.

Rollback cannot silently downgrade user data. A configuration migration must be reversible or forward-compatible before activation is allowed.

## Offline Policy Reference

The cross-platform `core-update-policy` wrappers validate strict manifest shape, a full release commit, channel and version ordering, engine/schema compatibility, exactly one host OS/architecture/target asset, approved HTTPS GitHub hosts, and—when package bytes are supplied—exact size and SHA-256. The fixture command is exercised by the Full test suite.

The result always reports manifest-signature verification, asset-attestation verification, OS compatibility completion, compatibility preflight completion, and activation as false. The policy makes no network request, writes no file, touches no user data, and cannot download, stage, activate, roll back, or clean an engine version. Those capabilities remain native-runtime promotion gates.

The separate offline release-candidate path consumes committed fixture data shaped like an official GitHub Release response. It accepts only the exact `hysel/haven-42` repository, a stable non-draft/non-prerelease release explicitly marked immutable, exact repository/tag-bound GitHub release and manifest URLs, a tag that matches the update manifest, a bounded asset list, and exactly one named manifest asset with a positive non-boolean size. Hostile source, tag, URL identity, immutability, and asset cases fail closed. Its output always sets network use, download, writes, and activation to false. Live GitHub querying remains unimplemented and requires explicit network consent plus a separately reviewed acquisition boundary.

## Cryptographic Verifier Handoff

The candidate mechanism and dependency decision is recorded in
`docs/core-update-cryptographic-verifier-review.md`. Native Windows and macOS
verification plus a pinned offline Sigstore-bundle verifier are research
candidates only. No cryptographic dependency or trusted identity is admitted.

`scripts/core-update-trust-handoff.py` validates the shape and binding of a
future native verifier receipt. The receipt contains bounded identifiers,
verifier profile/version and binary digest, trust-root identifier, exact
repository/release/commit/manifest/asset digests, target platform identity,
verification outcome booleans, timestamps, and replay history. It accepts no
raw signature, certificate, transparency proof, URL, or filesystem path.
Unknown fields, unknown verifier profiles, false verification claims, malformed
digests, repository confusion, future-issued or expired receipts, and replayed
receipt identifiers fail closed. The hostile self-test covers 30 cases.

This is deliberately a structural handoff, not cryptographic verification.
Receipt fields are untrusted scenario input; Haven 42 has no admitted verifier
registry or trust root and does not parse or validate a real signature,
certificate, Sigstore bundle, transparency proof, or platform signature. Even
the valid fixture reports `CryptographicVerificationPerformed`,
`TrustEstablished`, `PackageEvidencePromoted`, `StagingAllowed`, and
`ActivationAllowed` as false. Network, download, writes, staging, activation,
trust-store, credential, and user-data effects also remain false. A pinned,
reviewed native verifier and real cross-platform evidence are still required.

## Verifier Registry And Trust-Root Transitions

`scripts/core-update-verifier-transition.py` models how a future verifier
registry could move from one immutable version to the next. The candidate must
use the exact next integer version, begin during the current registry's validity
window, extend that window, retain at least one exact verifier continuity
anchor, and retain at least one active current trust root. Authorization
descriptions must use a sorted unique set of current active root identifiers,
meet their stated threshold, contain only true bounded claim booleans, and use
an unreplayed transition identifier.

The 33-case hostile suite covers malformed or unsorted registries, unknown
profiles, verifier and root substitution, invalid validity windows, version
skips, backdating, missing overlap, missing continuity, non-current signers,
threshold mismatch, false or malformed claims, replay, and raw cryptographic or
path input. Claim booleans are deliberately non-authoritative: the model
verifies no signature, accepts no transition, establishes no trust, and changes
no registry, trust store, runtime verifier, package, credential, or file.

## Effect-Free Lifecycle Simulation

`scripts/core-update-lifecycle.py` and the Windows, Linux, and macOS wrappers
consume only a caller-selected local JSON scenario. The schema exposes no raw
path, URL, executable, argument, environment, approval, or renderer-evidence
field. It can model three operations:

- a healthy update plan through evidence, compatibility, staging, health,
  atomic-selection, and retention transitions;
- deterministic rollback planning after post-activation health failure or an
  interrupted activation journal;
- retention inspection that protects the active and previous known-good
  versions while identifying older versions that a future admitted runtime
  could remove.

Disabled mode returns no transitions and retains every version. Before a
staging plan is produced, the scenario must assert byte, manifest-signature,
asset-attestation, provenance, SBOM, notices, operating-system, schema, storage,
and reversible-migration preconditions. These booleans are untrusted simulation
inputs and do not verify or create evidence; only a future trusted native
verifier could supply authoritative results. Staged-health failure stops before
an activation transition. Post-activation failure always produces rollback
transitions.

All output is counterfactual: `WouldRetainVersions` and
`WouldRemoveVersions` are review data, not filesystem authority. The result
always denies activation and machine modification and reports network, writes,
download, staging, activation, rollback, cleanup, installation, elevation,
service, driver, firewall, process, and user-data effects as false. The hostile
self-test covers 45 healthy, failed-health, interrupted, disabled, retention,
candidate-digest replay, retained-version collision, downgrade, phase-specific
recovery, malformed-state, missing-evidence, and renderer-authority
cases without accessing a machine update directory.

The separate installation broker foundation accepts only `plan-install`,
`plan-upgrade`, or `plan-uninstall` with compatible absent/present simulated
state and exact boolean promotion-evidence fields. It rejects paths, commands,
arguments, unknown state, renderer approval, and extra fields. Even a complete
simulated evidence set remains `not-admitted`: authority, approval, execution,
installation, removal, process control, privilege, service, driver, firewall,
filesystem, and network effects are all false.

## Current Admission State

No updater, update service, Tauri plugin, manifest publisher, background task, runtime scaffold, or installer is admitted. The offline policies, structural verifier handoff and transition model, and lifecycle simulation are preparatory evidence only. Implementation still requires a pinned trusted native signature/attestation verifier, immutable authorized registry distribution, native package evidence, actual canonical-path and privilege tests, real side-by-side staging, atomic activation, health execution, rollback execution, cleanup execution, and exact-SHA hosted CI before any machine effect can be considered.
