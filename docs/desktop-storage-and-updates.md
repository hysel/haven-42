# Desktop Storage, Updates, And Rollback

## Purpose

`config/desktop-storage-contract.json` defines where each class of Haven 42 data belongs on Windows, Linux, and macOS. `config/core-update-manifest-contract.json` defines the future immutable core-engine update boundary. These are architecture contracts, not an admitted updater or desktop runtime.

The central rule is simple: an application update may replace the versioned engine, but it must not own or silently change the user's configuration, repositories, generated artifacts, models, provider data, or credentials.

## Native Path Resolution

The application must resolve paths through native platform APIs at runtime. It must not persist unresolved environment-variable strings or assume that a home, Documents, or application-data directory has its default location.

- Windows uses Known Folder resolution, including `FOLDERID_UserProgramFiles`, `FOLDERID_RoamingAppData`, `FOLDERID_LocalAppData`, and `FOLDERID_Documents`. See Microsoft's [KNOWNFOLDERID reference](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid).
- Linux follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/) and requires an explicit user choice when a documents directory cannot be resolved safely.
- macOS uses Foundation directory resolution for Application Support, Caches, Documents, and the selected Applications directory. See Apple's [File System Programming Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html).
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
| Secrets | Provider tokens or credentials | Use Windows Credential Manager, a Linux Secret Service keyring, or macOS Keychain; never ordinary JSON configuration. |

Repositories remain where the user selected them. Desktop access uses the opaque path-grant rules in `config/desktop-ipc-contract.json`; the renderer never gains a raw-path execution surface.

## Platform Shape

The machine-readable contract records native identifiers rather than hard-coded absolute paths. Packaging can choose an installer-managed immutable application location, but mutable data always remains outside it.

Windows keeps roaming configuration separate from local state, caches, models, update downloads, and staged versions. Linux separates XDG config, state, cache, and data roots. macOS separates Application Support and Caches from the signed application bundle. Generated artifacts default to the user's native Documents location only when it can be resolved and disclosed; otherwise the user selects a directory.

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

## Current Admission State

No updater, update service, Tauri plugin, manifest publisher, background task, runtime scaffold, or installer is admitted by these contracts. Implementation still requires negative tests, native package evidence, signatures or attestations, offline behavior, disabled-update behavior, lifecycle checks, and exact-SHA hosted CI.
