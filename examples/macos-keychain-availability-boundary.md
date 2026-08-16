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

Reference: [Apple Keychain Services documentation](https://developer.apple.com/documentation/security/keychain-services).
