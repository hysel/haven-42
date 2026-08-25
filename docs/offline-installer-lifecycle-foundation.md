# Offline installer lifecycle foundation

Haven 42 does not contain an installer. The offline lifecycle foundation uses a
standard-library simulation to reject unsafe plans before any future native
implementation is considered. It performs no network, filesystem, process,
service, scheduled-task, registry, driver, elevation, installation, update,
rollback, cleanup, uninstall, or user-data effect.

`config/install-component-registry.json` is the component inventory. It points
to `config/install-artifact-registry.json`, whose default decision is deny and
whose admitted artifact list is empty. The artifact schema requires immutable
filename, version, platform, architecture, byte length, SHA-256, source,
license-review, integrity-verification, and lifecycle evidence. Portable
development archives are not silently converted into installer inputs.

## Effect-free transaction model

`config/offline-installer-lifecycle-contract.json` and
`scripts/simulate-offline-installer-lifecycle.py` model install, update,
rollback, cleanup, uninstall, recovery, and interruption at every transaction
phase. Requests contain logical root kinds and relative path segments—not raw
host paths. The evaluator requires canonical containment, current-user
ownership, trusted writable permissions, destination and temporary space, and
negative proofs for links, junctions, reparse points, mount escapes, and
application, repository, or user-data overlap.

Versions are retained side by side with a limit of two. Update replay and
downgrade are rejected. Interrupted state requires a matching recovery request
and a canonical SHA-256 digest-chained journal. Uninstall accepts only a
bounded manifest of transaction-owned files with exact relative paths and
digests; broad directory deletion is not representable. User data is preserved
unless an uninstall request explicitly selects deletion, and the simulation
still reports `userDataDeleted: false`.

Run the synthetic example locally:

```powershell
python scripts/simulate-offline-installer-lifecycle.py --json
python scripts/test-offline-installer-lifecycle.py
```

The output includes Windows, Linux, or macOS future-native checklists. These
are review requirements, not claims that a native lifecycle passed. Admission
would still require an exact registered artifact, cryptographic trust,
platform-native path and permission enforcement, clean-host and interrupted
lifecycle evidence, package parity, and separate owner approval.

Future installation of Ollama for private-network use has an additional
fail-closed HTTPS lifecycle. Ollama remains loopback-bound behind a separately
acquired, reviewed TLS gateway. Locally generated certificates are permitted
only with an exact endpoint-IP SAN, explicit client trust, protected private
keys, negative TLS tests, rotation, rollback, and transaction-owned cleanup.
See [Ollama HTTPS installation foundation](ollama-https-installation-foundation.md).
