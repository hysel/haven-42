# Windows Desktop Dependency Resolution Evidence

## Result

Evaluation date: 2026-07-22

Status: **blocked; do not admit desktop runtime manifests or scaffolding**.

The npm and PyInstaller candidate graphs resolved cleanly in a disposable Windows workspace. The released Tauri `2.11.5` graph still contains five Windows-reachable unmaintained Rust crates. Tauri upstream commit `dd725f4b13c30a86b398ccc59eb498f151f461c5` upgrades `urlpattern` to `0.6.0`, removes that chain, and passed a controlled-source audit plus native Windows x64 compile/link probe. The fix is not yet in a published Tauri release, so it is evidence of an available upstream resolution—not a shippable dependency pin.

A second official publication recheck on 2026-07-22 found Tauri release/crate `2.11.5`, `@tauri-apps/cli 2.11.4`, `tauri-utils 2.9.3`, and `urlpattern 0.6.0` still current for this boundary. No newer published Tauri release carries the reviewed fix, so the blocker and no-runtime decision remain unchanged.

The universal lock graph still contains Linux-only unmaintained GTK3 crates and an unsound `glib` advisory. Those packages were absent from the Windows x64 target tree but remain a separate Linux promotion blocker. These findings do not invalidate the architecture choice, but no desktop runtime may enter the repository until an official release contains the Windows fix and each target's complete graph passes independently.

No evaluation manifest, lock file, package directory, virtual environment, Rust toolchain, audit binary, probe executable, or build output from this run is shipped in the repository.

## Patched-Source Windows Native Probe

The successful disposable probe is [GitHub Actions run 29934029322](https://github.com/hysel/haven-42/actions/runs/29934029322), built from temporary branch commit `0989f65d5dd423348b6094017c313aa472c2a24d`. The temporary workflow, manifests, locks, sources, generated icon, audit tools, SBOMs, executable, and build output are evaluation-only and are not merged into `main`.

| Check | Result |
| --- | --- |
| Runner | GitHub-hosted `windows-2025`, Windows x64 MSVC |
| Rust / Cargo | `1.97.1`; exact target `x86_64-pc-windows-msvc` |
| Tauri dependency | Released `tauri 2.11.5` with only `tauri-utils` patched to upstream commit `dd725f4b13c30a86b398ccc59eb498f151f461c5` |
| Patched graph | 438 lock packages; 256 packages in Windows-targeted Cargo metadata |
| Removed chain | `urlpattern 0.6.0` present; `unic-char-property`, `unic-char-range`, `unic-common`, `unic-ucd-ident`, and `unic-ucd-version` absent |
| Controlled audit tool | `cargo-audit 0.22.2`, compiled from its locked crate source on the runner |
| Cargo audit | Zero known vulnerabilities; 12 universal-lock warnings, none reachable in the Windows x64 target tree |
| npm audit | Zero known vulnerabilities for the minimal native probe's pinned Tauri CLI graph; the separate full frontend candidate graph remains recorded above |
| SBOM | CycloneDX Cargo SBOM with 255 components plus a minimal npm CycloneDX SBOM |
| License inventory | 413 records; the only missing license was the local disposable probe package, not a third-party package |
| Native checks | `cargo check --locked --target x86_64-pc-windows-msvc` and `tauri build --no-bundle` passed |
| PE inspection | Unsigned development PE, 11,139,584 bytes, SHA-256 `5fa79a6ff6e819c19ebd726056a6f655281d76aa032627c267853bbb00f0e55f` |
| Admission | `false`; no bundle, installer, sidecar, renderer, IPC bridge, lifecycle, signing, or product runtime evidence |

The runner's preinstalled Node `22.23.1` and npm `10.9.8` were sufficient only for the minimal `@tauri-apps/cli 2.11.4` native probe. They do not replace the previously resolved exact Node `24.18.0` / npm `11.16.0` full frontend candidate evidence, and a future admitted build must use one pinned toolchain consistently.

The two failed precursor runs are not promotion evidence. The first used an unsupported informational flag after all three audit tools compiled; the second omitted Tauri's required Windows icon resource. Both were corrected only on the disposable branch, and the final run repeated every preceding gate before passing.

## Scope And Method

The evaluation used exact direct candidates from `docs/desktop-runtime-dependency-evaluation.md` in a system-temporary workspace. Registry queries, downloads, caches, generated manifests, lock files, tools, and build output remained outside the repository.

The Windows target was `x86_64-pc-windows-msvc`. ARM64 remains a separate future graph and build gate. This run did not claim Linux, macOS, installer, WebView bootstrap, application lifecycle, actual engine-sidecar, or renderer security evidence.

## Verified Build Toolchain Inputs

| Input | Exact version | Verification |
| --- | --- | --- |
| Node.js | `24.18.0` | Official Windows x64 ZIP matched the Node-published SHA-256 `0ae68406b42d7725661da979b1403ec9926da205c6770827f33aac9d8f26e821`. |
| npm | `11.16.0` | Bundled with the verified Node 24.18.0 archive; this version generated the authoritative disposable lock. |
| Rust | `1.97.1` | Minimal isolated rustup toolchain, `rustc` commit `8bab26f4f68e0e26f0bb7960be334d5b520ea452`; rustup-init matched its official published SHA-256. |
| Cargo | `1.97.1` | Bundled with the isolated Rust toolchain. |
| Python | `3.14.6` | Existing Windows interpreter used only through isolated virtual environments. |
| PyInstaller | `6.21.0` | Exact Windows wheel installed offline from the hash-recorded wheelhouse. |

The official references are the [Node.js 24.18.0 release](https://nodejs.org/en/blog/release/v24.18.0), [Rust 1.97.1 release index](https://blog.rust-lang.org/releases/), [Tauri releases](https://github.com/tauri-apps/tauri/releases), and [PyInstaller 6.21 documentation](https://pyinstaller.org/en/stable/).

## npm Resolution

Direct runtime candidates:

- `@tauri-apps/api 2.11.1`
- `@tauri-apps/plugin-dialog 2.7.2`
- `@tauri-apps/plugin-shell 2.3.5`
- `react 19.2.8`
- `react-dom 19.2.8`

Direct build candidates:

- `@tauri-apps/cli 2.11.4`
- `@types/react 19.2.17`
- `@types/react-dom 19.2.3`
- `@vitejs/plugin-react 6.0.4`
- `typescript 7.0.2`
- `vite 8.1.5`

Resolution results:

| Check | Result |
| --- | --- |
| Lock format | npm lockfile version 3 |
| Resolved package records | 89, including target-specific optional packages |
| Exact registry integrity values | Present for all 89 package records |
| Declared license metadata | Present for all 89 package records |
| Strict peer dependency install | Passed |
| Complete dependency-tree check | Passed |
| npm audit | 0 total vulnerabilities |

License metadata was limited to 0BSD, Apache-2.0, BSD-3-Clause, ISC, MIT, MPL-2.0, and compatible dual-license expressions. The 12 MPL-2.0 records are `lightningcss` plus its target-specific optional binaries. MPL-2.0 requires notices and file-level source obligations if Haven 42 modifies/distributes covered source; it is not by itself an admission failure for an unmodified build-time dependency.

The official Node archive bundles npm 11.16.0. A preliminary graph generated by a newer npm was discarded and regenerated so the evidence reflects the exact pinned toolchain.

## Cargo Resolution

Direct candidates:

- `tauri 2.11.5`
- `tauri-build 2.6.3`
- `tauri-plugin-dialog 2.7.2`
- `tauri-plugin-shell 2.3.5`

Resolution results:

| Check | Result |
| --- | --- |
| Cargo package records | 444 total: one disposable workspace package and 443 third-party packages |
| Registry checksum records | 443 |
| Missing declared licenses | 0 |
| Windows x64 reachable packages | 247 |
| Known vulnerability advisories | 0 |
| Informational warnings | 17 universal; 5 Windows-reachable and 12 non-Windows |

The five Windows-reachable warnings are unmaintained `rust-unic` crates pulled through `tauri-utils 2.9.3 -> urlpattern 0.3.0`:

| Crate | Advisory |
| --- | --- |
| `unic-char-property 0.9.0` | [RUSTSEC-2025-0081](https://rustsec.org/advisories/RUSTSEC-2025-0081.html) |
| `unic-char-range 0.9.0` | [RUSTSEC-2025-0075](https://rustsec.org/advisories/RUSTSEC-2025-0075.html) |
| `unic-common 0.9.0` | [RUSTSEC-2025-0080](https://rustsec.org/advisories/RUSTSEC-2025-0080.html) |
| `unic-ucd-ident 0.9.0` | [RUSTSEC-2025-0100](https://rustsec.org/advisories/RUSTSEC-2025-0100.html) |
| `unic-ucd-version 0.9.0` | [RUSTSEC-2025-0098](https://rustsec.org/advisories/RUSTSEC-2025-0098.html) |

The non-Windows warnings include the archived GTK3 Rust bindings and `glib 0.18.5` [RUSTSEC-2024-0429](https://rustsec.org/advisories/RUSTSEC-2024-0429.html), an unsoundness fixed in `glib >=0.20.0`. Cargo's universal lock includes these Linux-target dependencies even though the Windows target closure does not compile them. They remain a Linux promotion blocker and cannot be waived by Windows evidence.

`tauri-plugin-dialog` also pulls `tauri-plugin-fs` as a Rust dependency. This does not grant renderer filesystem permission by itself, but it expands the reviewed supply-chain surface and reinforces the need for the explicit default-deny Tauri capability policy.

The RustSec `cargo-audit 0.22.2` Windows release archive was fetched from the official release and hashed, but GitHub reported no build attestation and its executable was not Authenticode-signed. Its zero-vulnerability result is therefore corroborating evidence only. Before promotion, repeat the audit using a tool built from locked reviewed source on a controlled runner or an independently attested artifact.

## Python And PyInstaller Resolution

The Haven 42 Python scripts currently use the standard library only. The application dependency graph is therefore Python itself; the following packages are build/packaging dependencies:

| Package | Resolved version | Wheel SHA-256 |
| --- | --- | --- |
| `altgraph` | `0.17.5` | `f3a22400bce1b0c701683820ac4f3b159cd301acab067c51c653e06961600597` |
| `packaging` | `26.2` | `5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e` |
| `pefile` | `2024.8.26` | `76f8b485dcd3b1bb8166f1128d395fa3d87af26360c2358fb75b80019b957c6f` |
| `pyinstaller-hooks-contrib` | `2026.6` | `fd13b8ac126b35361175edacd41a0d97080b75dd5f4b594ecefefff969509dd3` |
| `pyinstaller` | `6.21.0` | `7fae06c494ce0ebfe6bd3055c0e409def884f63af2e3705d06bd431ad9237fc7` |
| `pywin32-ctypes` | `0.2.3` | `8a1513379d709975552d202d942d9837758905c8d01eb82b8bcc30918929e7b8` |
| `setuptools` | `83.0.0` | `29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3` |

All wheels installed offline from the hash-pinned wheelhouse. PyPA `pip-audit 2.10.1` checked the complete eight-package environment, including pip, and reported zero known vulnerabilities.

License metadata is permissive except for PyInstaller and its hooks, which use GPL terms with PyInstaller's bootloader exception and some Apache-licensed files. The exception permits distributing generated bundles under the application's license, subject to the licenses of bundled dependencies. A future third-party notice must include the exact license files from every resolved wheel; classifier-only metadata is not sufficient.

A disposable standard-library probe built and launched successfully as a 64-bit one-file executable with `frozen: true`. It was intentionally unsigned and is not product evidence: the unified Haven 42 sidecar, IPC framing, resources, shutdown behavior, antivirus behavior, signing, and installer lifecycle were not built or tested.

## Admission Decision

Do not add `package.json`, npm lock files, `Cargo.toml`, Cargo lock files, Rust source, frontend source, Python packaging files, Tauri configuration, installers, or sidecar binaries to the repository yet.

The next admissible work is:

1. Wait for and review a published Tauri release containing the `urlpattern 0.6` change; do not ship the development-branch patch.
2. Repeat the complete Windows graph, controlled audit, SBOM, license, native build, and package inspection against that exact release.
3. Resolve and lock the full frontend, Python sidecar, WebView, native-library, and packaging graph under one pinned build image.
4. Keep Linux blocked until its GTK3 and `glib` findings are separately resolved or accepted through a Linux-specific review.
5. Translate the 55-case native-authority policy model and 46-case engine-side policy into required native bridge, sidecar, lifecycle, path/grant, approval, cancellation, remote-content, and privilege tests against actual admitted code.
6. Only after those gates pass, propose the smallest non-visual Tauri bridge scaffold for repository admission. The first-slice navigation and interaction checkpoint is complete; visual renderer implementation still follows native admission.
