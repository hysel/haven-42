# Linux Credential Store Availability Boundary

Status: offline-tested availability probe only; no credential-store or package
admission.

Haven 42's Linux history design requires a user-scoped implementation of the
freedesktop.org credential-storage API. Headless systems and desktop sessions
without an available, unlocked service must remain in write-free Private
session rather than store a plaintext key.

The candidate probe uses a reviewed system `busctl` path and the fixed
`--user --no-pager --no-legend list` arguments to check whether
`org.freedesktop.secrets` is already registered on
the current user bus. It does not activate the service, invoke a method, open a
collection, read or write credential material, install a package, use the
network, or return a bus address, runtime directory, bus-name list, stderr, or
other raw host data. Results contain sanitized booleans and a fixed status only.

The 27 offline checks cover unsupported platforms, missing tools, missing user
sessions, reachable and unreachable buses, active and inactive services,
timeouts, hostile environment values, reviewed system executable paths, hostile
caller-selected executable refusal, fixed arguments, bounded output, sanitized
errors, all-false runtime authority, and package exclusion.

This does not prove that a Linux desktop credential-store implementation is
installed, unlocked, compatible, or safe to use. No binding is selected.
Native desktop, locked, denied, absent, corrupted, headless, source/package
parity, key-memory, and credential lifecycle evidence remain required before
admission.

## Native headless result

On August 15, 2026, the exact reviewed source probe and contract ran from a
validated temporary directory in a Linux headless container session. `busctl`
and the user session bus were available, but the required service was not
active. No service was activated and no credential operation occurred. The
temporary directory was removed and a residue check passed.

This is a narrow expected fail-closed headless cell. It is not evidence for a
desktop session, a locked or unlocked collection, key storage, a selected
binding, runtime integration, or a packaged application.

Reference: [freedesktop.org Secret Service API](https://specifications.freedesktop.org/secret-service/latest/).
