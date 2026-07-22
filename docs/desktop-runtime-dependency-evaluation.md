# Desktop Runtime Dependency Evaluation

## Decision Status

Evaluation date: 2026-07-22

The Milestone 22 desktop stack is **architecture-approved but not admitted for shipment**. This review pins the smallest candidate set so reproducible implementation and platform testing can begin later. It does not add a package manifest, lock file, Rust crate, frontend source tree, installer, or executable runtime. The disposable Windows evidence is recorded in `docs/desktop-dependency-resolution-evidence.md`. A pinned upstream Tauri source commit removes the Windows `rust-unic` chain and passes a native probe, but the fix is not in a published Tauri release, so runtime admission remains blocked.

Haven 42's pass-before-ship rule applies to the complete resolved dependency graph, not just the direct packages in this document. Exact lock files, checksums, vulnerability reports, license output, and native test evidence are required before a package can be promoted.

## Reviewed Candidate Set

| Component | Exact candidate | Role | License position | Admission state |
| --- | --- | --- | --- | --- |
| Tauri Rust workspace | `2.11.5` | Desktop shell, native bridge, bundling | Apache-2.0 OR MIT | Architecture-approved; not installed or shipped |
| `tauri-build` | `2.6.3` | Rust build-time configuration and code generation | Apache-2.0 OR MIT | Build-time candidate |
| `@tauri-apps/cli` | `2.11.4` | Build-time CLI | Apache-2.0 OR MIT | Build-time candidate |
| `@tauri-apps/api` | `2.11.1` | Typed frontend IPC client | Apache-2.0 OR MIT | Runtime candidate |
| `@tauri-apps/plugin-dialog` | `2.7.2` | User-driven native file and directory selection | MIT OR Apache-2.0 | Candidate with narrow permission scope |
| `@tauri-apps/plugin-shell` | `2.3.5` | Packaged engine sidecar lifecycle only | MIT OR Apache-2.0 | Held behind native-only spawn policy; no renderer shell API |
| React and React DOM | `19.2.8` | Local UI rendering | MIT | Runtime candidate |
| Vite | `8.1.5` | Build bundled local web assets | MIT | Build-time candidate |
| `@vitejs/plugin-react` | `6.0.4` | React build integration | MIT | Build-time candidate |
| TypeScript | `7.0.2` | Compile-time type checking | Apache-2.0 | Build-time candidate |
| `@types/react` / `@types/react-dom` | `19.2.17` / `19.2.3` | Compile-time React types | MIT | Build-time candidates discovered during exact resolution |
| Node.js | `24.18.0` LTS | Frontend build toolchain | MIT with bundled third-party notices | Build-host only; never installed globally for users |
| Rust | `1.97.1` stable | Native build toolchain | Apache-2.0 OR MIT | Build-host only; Tauri's lower MSRV does not replace the pinned build image |
| PyInstaller | `6.21.0` | Package the existing Python engine as a platform-specific sidecar | GPL-2.0 with bootloader exception; selected files Apache-2.0 | Build-time candidate; generated bundles may use the project license subject to bundled dependency licenses |

Primary version and license references are the [Tauri releases](https://github.com/tauri-apps/tauri/releases), [Tauri repository](https://github.com/tauri-apps/tauri), [React releases](https://github.com/facebook/react/releases), [Vite package](https://www.npmjs.com/package/vite), [TypeScript package](https://www.npmjs.com/package/typescript), [Node.js 24.18.0 LTS release](https://nodejs.org/en/blog/release/v24.18.0), [Rust releases](https://blog.rust-lang.org/releases/), and [PyInstaller 6.21 license](https://pyinstaller.org/en/stable/license.html). Before scaffolding, the maintainer must query the official registries again and either retain these exact pins or repeat this evaluation for replacements.

## Minimal Dependency Boundary

The first vertical slice should use only the packages above plus their locked transitive dependencies. It must not add:

- Electron, a bundled Chromium runtime, or a local production web server;
- remote JavaScript, stylesheets, fonts, frames, CDN assets, or remotely hosted application pages;
- a UI component framework before the interaction and accessibility design is agreed with the user;
- a generic filesystem plugin, unrestricted shell/process bridge, arbitrary URL opener, telemetry SDK, analytics service, or crash-upload service;
- Tauri's updater plugin until the separate immutable-release manifest, verification, rollback, and consent contract is implemented and tested;
- image, music, or video libraries merely because those capabilities appear on the roadmap.

The renderer can request only the commands defined by `config/desktop-ipc-contract.json`. The native layer owns sidecar startup, shutdown, canonical path grants, external-link validation, and message-size enforcement. Even if the shell plugin is used internally, no shell command or argument surface is exposed to JavaScript.

## Platform Prerequisites And Package Matrix

| Target | Build prerequisites | User runtime | Initial package evidence |
| --- | --- | --- | --- |
| Windows x64/ARM64 | Matching Windows runner, Microsoft C++ Build Tools, Rust, Node.js, Python/PyInstaller, WebView2 build support; VBSCRIPT only if MSI is later evaluated | Edge WebView2; use the evergreen runtime already present on supported modern Windows or bootstrap it explicitly | Per-user NSIS EXE and portable ZIP first; MSI is separate evidence |
| Linux x64/ARM64 | Native target runner, WebKitGTK 4.1 development packages, compiler toolchain, Rust, Node.js, Python/PyInstaller, distro packaging tools | Compatible WebKitGTK and system libraries | AppImage first; each DEB/RPM distribution and architecture is separately promoted |
| macOS Apple Silicon/Intel | Matching macOS runner, Xcode Command Line Tools, Rust, Node.js, Python/PyInstaller | WKWebView supplied by macOS | DMG/app bundle per architecture; signed/notarized public build and final physical-Mac check remain last |

Tauri's [prerequisites](https://v2.tauri.app/start/prerequisites/) and [distribution guidance](https://v2.tauri.app/distribute/) are the source for native build requirements. PyInstaller is not a cross-compiler, so the engine sidecar must be built and tested on each target operating system. Cross-compiling Windows from another host is a last resort, consistent with Tauri's [Windows installer guidance](https://v2.tauri.app/distribute/windows-installer/).

End users must not receive global Node.js, Rust, Python, package managers, build tools, GPU drivers, Ollama, ComfyUI, models, agent software, services, firewall changes, or startup entries as an undisclosed side effect of the Haven 42 desktop package.

## Supply-Chain And License Gates

Before any desktop runtime files are admitted:

1. Generate immutable npm and Cargo lock files on a review branch and reject floating dependency ranges in release builds.
2. Produce the resolved npm, Cargo, Python, native-library, WebView, and packaging-tool inventory, including checksums and provenance.
3. Run supported vulnerability and abandoned-package checks. Every exception needs a dated decision, scope, compensating control, and review date.
4. Generate a bundled third-party notice and license report. Vite's build license report may assist with frontend bundles, but it does not replace Cargo, Python, native-library, or installer notices.
5. Build the Python sidecar independently on Windows, Linux, and macOS; verify no interpreter or unplanned runtime is required on the destination machine.
6. Run the fail-closed IPC/security suite, package lifecycle suite, artifact/state-preservation checks, and exact-SHA hosted CI before promotion.
7. Sign only release candidates. Unsigned development packages must be labeled as development artifacts and must not be promoted as stable downloads.

## Re-evaluation Triggers

Repeat this review when any direct version changes, a lock file materially changes, a new Tauri plugin or native library is proposed, a supported OS/architecture is added, a WebView prerequisite changes, PyInstaller packaging is replaced, or a vulnerability/license finding changes the risk decision.
