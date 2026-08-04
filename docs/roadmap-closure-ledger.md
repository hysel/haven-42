# Roadmap closure ledger

The machine-readable ledger at `config/roadmap-closure-ledger.json` prevents unfinished work from being lost when implementation moves between milestones. It classifies every unchecked item in `TODO.md` exactly once.

The categories distinguish work that genuinely depends on new evidence, an
external machine or platform, a suitable repository, an upstream release,
signing or release authority, successful admission of an earlier gate, or a
runtime/external gate whose local foundation is now complete. Classification
does not mark an item complete and grants no runtime, network, package,
machine-change, signing, or release authority.

The local closure batch leaves no known preparation-only item unclassified.
The remaining unchecked items require external evidence, owner or repository
input, upstream change, product/runtime admission, or release-policy authority.

`scripts/test-roadmap-closure-ledger.py` hashes normalized checkbox text and fails if an item is added, removed, edited, duplicated, or omitted without updating the ledger. This makes roadmap drift visible before a commit instead of after a merge.
