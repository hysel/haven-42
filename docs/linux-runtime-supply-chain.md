# Linux runtime supply-chain review

Haven 42 downloads a local AI engine only after the user reviews and approves
the exact setup. The download stays inside `Haven42-Data`, beside the extracted
app. Haven 42 does not install a system package, service, or driver.

## What is currently approved

Alpha 2 still uses the separately registered Ollama 0.32.5 Linux core runtime.
This review does not change that version or the automatic model choice.

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
package therefore carries the exact Ollama MIT license text from the official
`v0.32.5` and `v0.32.9` source tags. Both tags point to the same reviewed Git
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

## Why 0.32.9 is not installed yet

Archive provenance and integrity are only part of admission. Native lifecycle,
distribution, startup, shutdown, recovery, and model-compatibility evidence is
still required. The machine-readable review therefore says both
`managedRuntimeChangeApproved: false` and
`automaticDefaultChangeAllowed: false`.

Developers can validate the committed record without downloading anything:

```text
python scripts/audit-linux-runtime-supply-chain.py
```

Supplying both locally downloaded archives additionally performs the complete
hash and archive-structure audit. The tool never downloads or installs them.
