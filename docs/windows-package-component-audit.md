# Windows Package Component Audit

Audit date: 2026-07-27

This is a sanitized technical and license-readiness inventory for the unsigned
Windows x64 development package. It is not legal advice, redistribution
clearance, a signature, or a production-release approval.

## Rejected Local Build And Admitted Target Shape

The earlier 70-file local build is no longer an admitted candidate. PyInstaller
resolved 38 API-set/UCRT shim DLLs plus `ucrtbase.dll` from an unrelated
OpenLogic JDK directory found on the host `PATH`. Those 39 files are
host-derived contamination even if their code is otherwise redistributable.
The classifier now rejects them, and the builder removes `PYTHONHOME` and
`PYTHONPATH`, disables user-site discovery, and supplies PyInstaller a minimal
Windows path containing only the active Python directories and Windows system
directories.

The replacement clean local build contains 31 files. Its artifact verifier and
native parity, relocation, read-only, abrupt-exit recovery, repeated lifecycle,
port-collision, shutdown-authority, hostile-environment, and integrity tests
passed. The two retained Visual C++ runtime files match the official Python
3.14.6 64-bit embeddable distribution byte-for-byte:

| Group | Files | Candidate identity | Current disposition |
| --- | ---: | --- | --- |
| Haven 42 launcher | 1 | `haven42.exe`, Haven 42 0.3.0 | Project-owned MIT code; only proposed signing subject. |
| CPython core | 1 | CPython 3.14.6 `python314.dll` | Upstream runtime; never sign as Haven 42. Include authoritative PSF terms. |
| CPython extension modules | 12 | `.pyd` modules selected by PyInstaller | Upstream/bundled-library code; never sign as Haven 42. Map each module to CPython and bundled dependency notices. |
| CPython standard library | 1 | `base_library.zip` | Upstream PSF-licensed content; never sign as Haven 42. |
| OpenSSL | 2 | OpenSSL 3.5.7 `libcrypto-3.dll` and `libssl-3.dll` | Apache-2.0 upstream libraries; never sign as Haven 42. Version, source archive, source/binary dependency commits, and license evidence are recorded. |
| libffi | 1 | libffi 3.4.4 `libffi-8.dll` | MIT upstream library; never sign as Haven 42. Version, source archive, source/binary dependency commits, and exact license evidence are recorded. |
| Microsoft API-set/UCRT shims | 0 admitted | Any application-local `api-ms-win-*` or `ucrtbase.dll` | Rejected as host-derived input. The supported Windows baseline must supply its system UCRT/API sets. |
| Microsoft runtime libraries | 2 | Microsoft 14.42.34438.0 `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` | SHA-256 matches the official Python.org 3.14.6 x64 embeddable ZIP and both Authenticode signatures validate to Microsoft Windows Software Compatibility Publisher; applicable Microsoft redistribution terms still require review. |
| Haven 42 resources | 9 | allowlisted HTML, JavaScript, CSS, and JSON | Project-owned MIT data/code. |
| Integrity manifest | 1 | embedded resource hashes | Project-owned MIT evidence. |
| Development marker | 1 | unsigned-development warning | Project-owned MIT evidence. |

The 31-file total and every individual SHA-256 digest are recorded in the
local artifact evidence. GitHub Actions run `30297195387` reproduced and
verified the unsigned development package on a clean hosted Windows runner at
exact main commit `04baca39b26ec58c189a6ae21ea78b507444e9fa`; the component
classifier rejected the banned host-derived JDK/UCRT shape. Hashes remain in
generated evidence rather than this source document, so this page cannot be
mistaken for evidence for a later binary or redistribution clearance.

## Authoritative License References

- [Python 3.14 history and license](https://docs.python.org/3.14/license.html)
  contains the PSF license history and bundled-software notices, including
  bzip2 and libffi.
- [Python 3.14.6 release files](https://www.python.org/downloads/release/python-3146/)
  publish the official 64-bit Windows installer SHA-256, Sigstore bundle, and
  SPDX SBOM. The installer SHA-256 is
  `14b3e9a710a3fcf0bd9b55ab6b60412bd91227563f813fc49040cabc0209e0bd`.
- [The official 64-bit installer
  SBOM](https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe.spdx.json)
  identifies libffi 3.4.4 and OpenSSL 3.5.7 and publishes the SHA-256 of each
  source archive.
- [OpenSSL licensing](https://openssl-library.org/source/license/index.html)
  states that OpenSSL 3.0 and later use Apache License 2.0.
- [Microsoft Visual C++ redistribution
  guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)
  states that runtime redistribution is limited to licensed Visual Studio
  users and governed by Microsoft Software License Terms.
- [Microsoft's current distributable-code
  list](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution)
  permits specified unmodified runtime files subject to the applicable Visual
  Studio license and excludes debug/non-redistributable locations.

These references establish review inputs. The exact hash comparison below
proves origin for the two retained Visual C++ runtime files, but not the
applicable redistribution right.

## Gaps Found

The generated `runtime-component-inventory.json` binds every admitted file to the
project-owned group or one of four exact runtime groups, includes every file
digest and byte count, rejects unclassified paths, marks every upstream file
ineligible for Haven 42 signing, and keeps production promotion false. The
CycloneDX SBOM mirrors those exact runtime groups, versions where discoverable,
license expressions, file counts, and unresolved review states.

For the clean Windows evidence, CPython, OpenSSL, and libffi are labeled
`license-text-and-source-provenance-recorded-review-required`: their exact
license and source chain is recorded, but final package/license review remains
open. The Microsoft group remains
`file-origin-recorded-redistribution-review-required`; verified file origin is
not treated as redistribution clearance.

The current `THIRD-PARTY-NOTICES.txt` now covers the exact Python build-tool
allowlist and every runtime group, but it intentionally warns that runtime
redistribution is not cleared. Hash-verified evidence now includes CPython
3.14.6's full bundled-license file, the Apache 2.0 text for OpenSSL 3.5.7, and
the exact libffi 3.4.4 MIT license. The runtime inventory now records the
official installer/SBOM chain plus the immutable CPython and dependency
commits. Applicable Microsoft redistribution-license evidence remains
incomplete.

The two Visual C++ runtime DLLs are the highest-priority unresolved legal
group. Microsoft
recommends centrally deployed redistributables for serviceability and permits
application-local redistribution only under the applicable licensed source
and terms. Haven 42 must not infer redistribution rights merely because
PyInstaller copied a DLL from a build host.

The hosted Windows input is now narrowed to the official
`actions/python-versions` release `3.14.6-27283001424`, archive
`python-3.14.6-win32-x64.zip`, and SHA-256
`dc722964ab28f81f6a0c753ee960871f045d363568f4fb7626cc02c1e0caa1e9`.
The immutable release recipe downloads the official python.org
`python-3.14.6-amd64.exe`. CPython tag `v3.14.6` resolves to commit
`c63aec69bd59c55314c06c23f4c22c03de76fe45`. Its Windows build definition
selects libffi 3.4.4 and OpenSSL 3.5.7. The corresponding source tags resolve
to commits `73b247f34ef3ae1859b8c2c34d321d34ebc5db15` and
`6a6901fa60c604816acb50b4e167791e5339c8f8`; the binary tags resolve to
`94cb9a1c7feb608adf2b9f8fe2dbd6925ffbf90d` and
`3217be5a2a7e20dbc5f5b5160ef21a9c84de7138`.

This closes the source/version/license evidence gap for the Windows libffi and
OpenSSL groups. An independent comparison also proves that both admitted
Visual C++ runtime DLLs are unmodified files from the hash-verified official
Python.org x64 embeddable ZIP. Both report version 14.42.34438.0 and valid
Microsoft Windows Software Compatibility Publisher Authenticode signatures.
Microsoft's guidance allows application-local unmodified runtime files but
limits distribution to users covered by applicable Visual Studio license
terms. The technical audit cannot establish that license status for Haven 42;
that owner/legal check remains open.

## Promotion Requirements

Before a SignPath application or public binary Release:

1. acquire every build input from an immutable, reviewed, authorized source;
2. record the applicable Microsoft redistribution terms for the two retained
   Visual C++ runtime DLLs;
3. repeat the clean hosted Windows reproduction for the exact immutable
   release candidate and confirm the banned JDK/UCRT files remain absent
   (passed for unsigned development commit
   `04baca39b26ec58c189a6ae21ea78b507444e9fa`);
4. include the applicable Microsoft license/notice text with the candidate
   (complete for CPython, OpenSSL, and libffi);
5. repeat the component coverage and hostile verification for the exact
   immutable release candidate on hosted Windows (passed for the current
   unsigned development form);
6. repeat the classifier on native Linux and macOS release-candidate package
   outputs (passed for the current unsigned development form); and
7. have the final result reviewed for license compliance.

Until all seven steps pass, the exact packaged dependency/license gate remains
blocked. Unsigned local development testing may continue under the existing
development-only boundary.
