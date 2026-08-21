# macOS Keychain Availability Boundary

Status: offline-tested availability probe only; no Keychain or package
admission.

Haven 42's macOS history design requires a credential facility scoped to the
current operating-system user. If that facility is absent, locked, denied, or
otherwise unavailable, Haven 42 must preserve any existing encrypted database
and continue in write-free Private session. It must never store a plaintext
database key beside the database.

The candidate probe invokes only the reviewed `/usr/bin/security` system path
with the fixed `help` argument. This checks that the command-line facade is
present and responsive without listing, opening, or unlocking a keychain and
without looking up, reading, writing, or deleting an item. It disables stdin,
uses a fixed environment, sets a five-second timeout, bounds stdout and stderr,
and discards both streams. Its public result is selected from exact predeclared
boolean/status shapes; host output and paths cannot cross the boundary.

The 30 offline checks cover the exact contract, unsupported platforms, missing
tools, the reviewed system executable path, hostile caller-selected executable
refusal, fixed arguments and environment, bounded output, timeout and launch
failure, nonzero responses, invalid output types, sanitized errors, exact
public-result serialization, all-false runtime authority, and package
exclusion.

This does not open or validate a Keychain, select a native binding, store a
synthetic or real key, or prove locked, denied, corrupted, recovery, rotation,
source/package parity, or application lifecycle behavior. Runtime, UI, user
content, database, package, and production authority remain false.

## Native hosted-source result

On August 16, 2026, the exact source contract and probe ran in the
[PR #91 GitHub-hosted macOS 15 smoke job](https://github.com/hysel/haven-42/actions/runs/31923744789/job/95107840089).
The platform-gated test required `/usr/bin/security help` to return the exact
`tool-responsive` public result while retaining every Keychain-operation and
admission flag as false. The complete macOS script-smoke job passed.

This is native hosted-source availability evidence only. It does not prove a
physical Mac, packaged parity, Keychain access, a locked or unlocked Keychain,
item lifecycle behavior, or saved conversation history.

## Physical Apple M4 availability result

On August 20, 2026, the same operation-free source probe returned the exact
`tool-responsive` public result on a physical Apple M4 Mac running macOS
26.6.2. The probe did not list, open, or unlock a Keychain; read, create,
change, or delete an item; show a system prompt; open a database; or retain raw
command output.

This closes only the physical-host command-availability cell. Interactive
synthetic-item lifecycle, locked/denied behavior, application integration,
source-versus-package parity, encrypted-history lifecycle, and production
admission remain open.

## Unattended synthetic-item result

On August 20, 2026, the separately approved synthetic lifecycle runner tried
the fixed validation-only item from an unattended SSH session. The initial
collision check confirmed that no such item existed, but macOS denied item
creation. The runner retained no secret or raw system output, created no
production admission, and recorded the cell as `blocked` rather than passing
it. The sanitized result is
`config/alpha-2-apple-m4-keychain-lifecycle-result.json`.

This is useful fail-closed evidence: an unattended administrative connection
cannot stand in for the interactive application session an end user will use.
The create/read/update/delete/absence lifecycle, locked and denied recovery,
packaged parity, and encrypted-history integration still require an
interactive physical-Mac test.

Reference: [Apple Keychain Services documentation](https://developer.apple.com/documentation/security/keychain-services).
