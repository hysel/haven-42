# Linux runtime supply-chain review

After the user reviews and approves the exact setup, Haven 42 downloads the local
AI engine. The download stays inside `Haven42-Data`, beside the extracted app.
Haven 42 does not install a system package, service, or driver.

## What is currently approved

New Alpha 2 managed installations use the separately registered Ollama
0.32.14 Linux x64 core runtime. The exact archive is 1,421,191,399 bytes with
SHA-256 `c620917a71e146ab3a7f893084f066069c4c65d144ef8379a91c3cbe8b27de8f`.
It contains 34 regular files, 3 directories, 17 internal links, and
2,247,201,888 expanded bytes. Those values were rechecked against the official
release archive on August 18, 2026. Historical model and lifecycle evidence
continues to identify the exact older runtime used by each test; this change
does not relabel those records.

## What was reviewed next

Ollama 0.32.9 is recorded as a candidate for later approval. Haven 42 checked
the official release metadata and the downloaded archives against these fixed
records:

| Component | Purpose | Download size | SHA-256 |
|---|---|---:|---|
| Linux x64 core | Runs the local AI model | 1,421,653,242 bytes | `5d747a43369f61e38f20b5a39fcc5c90647e562cdc61e2e56034f1c5b113d540` |
| Linux x64 ROCm supplement | Adds AMD acceleration files when separately approved | 1,047,461,645 bytes | `ab93c931df3ea570827f57fa752b3bea7bbc961af71412fc0d4cdaf5c48a356a` |

The core archive contains 34 regular files, 3 directories, and 17 internal
links. The ROCm supplement contains 1,808 regular files, 3 directories, and 14
internal links. Haven 42 validates those counts and the expanded byte totals;
an extra, missing, renamed, or changed entry is rejected.

The upstream archives do not contain a license notice. The portable Haven 42
package therefore carries the exact Ollama MIT license text. The official
`v0.32.5`, `v0.32.9`, and `v0.32.14` tags point to the same reviewed Git
license blob.

## What Haven 42 rejects

Before extraction, Haven 42 requires the registered HTTPS source, exact byte
length, and exact SHA-256. It rejects an unapproved redirect, traversal or
absolute paths, name collisions, hard links, devices, sockets, pipes,
unsupported entry types, missing link targets, link cycles, excessive archive
members, and expanded-size drift. Valid internal symbolic links are copied as
ordinary files so the installed runtime contains no links.

Downloads, staging, the runtime, model data, the runtime home, and temporary
files use fixed locations beneath `Haven42-Data`. Failed or cancelled work does
not become an installed runtime, and a completed runtime is rechecked against
its saved file inventory before reuse.

## Model files

The Alpha 2 Qwen 3.5 ladder uses only registry-provided prequantized artifacts.
Each model record pins the complete manifest plus its config, model, license,
and parameter layer digest and byte length. It also records the quantization,
minimum system memory, minimum usable graphics memory, and the tasks for which
evidence is required. A manifest or layer mismatch is not treated as the same
model. Adding this evidence did not change the order or default of the model
ladder.

## What remains before release promotion

Archive provenance and integrity are only part of admission. The Windows and
Linux review packages must still pass native download, startup, shutdown,
recovery, rollback, accessibility, and source-versus-package parity checks with
0.32.14 before release promotion. Setup also performs a bounded inference check
with the selected model and fails closed if the newer runtime does not work on
that device.

Developers can validate the committed record without downloading anything:

```text
python scripts/audit-linux-runtime-supply-chain.py
```

Supplying both locally downloaded archives additionally performs the complete
hash and archive-structure audit. The tool never downloads or installs them.
