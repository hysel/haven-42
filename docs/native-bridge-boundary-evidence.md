# Native Bridge Boundary Evidence

## Result

Evaluation date: 2026-07-22

Status: **policy model passed; native runtime remains blocked and unadmitted**.

The released Tauri dependency graph cannot yet enter the repository. The latest
official release and registries were rechecked before this work: Tauri `2.11.5`,
`tauri-utils 2.9.3`, and `@tauri-apps/cli 2.11.4` remain current. The reviewed
`urlpattern 0.6` remediation exists at upstream commit
`dd725f4b13c30a86b398ccc59eb498f151f461c5`, after the `2.11.5` release, and is
not a published dependency pin.

No `package.json`, npm lock, `Cargo.toml`, Cargo lock, Rust source, Tauri config,
frontend tree, native binary, sidecar, installer, service, startup entry, or
firewall change was added. No exception was granted for the five
Windows-reachable `rust-unic` advisories.

## Added Evidence

`config/native-bridge-boundary-contract.json` makes the future native-owned
authority explicit. `scripts/native-bridge-boundary-policy.py --self-test`
executes 55 hostile and allowed policy cases without touching a path, opening a
URL, spawning a process, minting a production token, or changing the machine.

The cases cover:

- native-dialog and application-owned path selection;
- absolute canonical roots, traversal, resolution mismatch, network paths,
  symlink or reparse escape signals, protected purposes, session binding,
  opaque identifiers, reuse, and bounded expiry;
- exact HTTPS host/path allowlisting, explicit user gestures, credentials,
  ports, schemes, and unrelated repositories;
- packaged-binary identity, target matching, renderer-supplied binary,
  arguments and working directories, private standard I/O, listening sockets,
  elevation, services, startup entries, firewall changes, single-sidecar state,
  crashes, reset, shutdown, and invalid transitions;
- environment allowlisting with credential-shaped variables removed;
- cancellation ownership with no renderer-selected PID or operating-system
  signal;
- approval shape, single use, session, lifetime, effects, grants, input digest,
  and changed-binding rejection.

## What This Does Not Prove

This is executable contract evidence, not native implementation evidence. It
does not prove Tauri command registration, Rust path canonicalization, Windows
reparse-point handling, Unix symlink race resistance, WebView navigation,
operating-system process-group ownership, standard-I/O framing under load,
installer privileges, package signing, shutdown during crashes, or behavior on
Windows, Linux, or macOS packages.

Those claims require actual admitted native code and exact-platform tests. The
contract therefore keeps `runtimeAdmitted` false and explicitly says that a
policy-model pass cannot promote the runtime.

## Admission Decision

The policy boundary is now concrete enough to drive a future Rust bridge, but
the next admission step remains blocked by the published dependency graph.
When an official Tauri release carries the reviewed remediation:

1. repeat exact npm and Cargo resolution for each target;
2. produce checksums, SBOMs, licenses, provenance, and controlled audits;
3. add the smallest nonvisual native bridge on a review branch;
4. translate all 55 policy cases plus the existing 46 engine-side cases into
   native integration tests;
5. run Windows x64 first, then bounded Linux targets, with macOS last;
6. admit runtime files only after every required target gate passes.
