# Conversation History Development Validation

The opt-in history database remains absent from the Haven 42 runtime and UI. The approved development validator exercises the Python standard library SQLite engine only with fixed synthetic records inside a newly created temporary directory. It verifies fixed schema creation, parameterized values, backup and read-only restore, foreign-key cascade deletion, and residue-free cleanup.

The validator accepts no user content or caller database path. It rejects pre-existing directory content, symlinks and reparse points, unsafe contract changes, and any runtime, UI, provider, network, package, production, or persistence authority. A passing development run is architecture evidence only; it does not admit saved conversations.

Before user history can be activated, the separate encryption, OS credential-store, key-loss, native packaging, backup/restore, migration, deletion, and visual product gates in `docs/conversation-history-encryption-review.md` still apply.
