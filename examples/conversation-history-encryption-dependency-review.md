# Conversation-history encryption dependency review

## What was reviewed

On 2026-08-15, Haven 42 reviewed the current SQLCipher Community Edition core
and two Python-binding paths without downloading or installing a dependency.

- The current official core is SQLCipher Community Edition 4.17.0 at commit
  `810db22f575ee7cf94ea96a3e91622b5fcece3dc`, released on July 8, 2026. It
  updates the SQLite baseline to 3.53.3.
- GitHub reports the annotated tag signature as `unknown_key` and its target
  commit as unsigned. The Community release publishes source through GitHub,
  not official prebuilt desktop Community packages.
- `sqlcipher3` 0.6.2 provides CPython 3.14 wheels for the three target desktop
  platforms, but it embeds SQLCipher 4.12.0 and SQLite 3.51.1. Its PyPI files
  were not uploaded using Trusted Publishing.
- `pysqlcipher3` is rejected because its own repository says it is no longer
  actively maintained and may contain security vulnerabilities.

The exact reviewed PyPI file sizes and SHA-256 values are recorded in
`config/conversation-history-encryption-dependency-review.json`. No artifact is
stored in the repository.

Primary sources:

- [SQLCipher 4.17.0 release](https://github.com/sqlcipher/sqlcipher/releases/tag/v4.17.0)
- [Zetetic 4.17.0 announcement](https://www.zetetic.net/blog/2026/07/08/sqlcipher-4-17-0-release/)
- [SQLCipher Community and attribution guidance](https://www.zetetic.net/sqlcipher/community/)
- [SQLCipher license information](https://www.zetetic.net/sqlcipher/license/)
- [`sqlcipher3` 0.6.2 on PyPI](https://pypi.org/project/sqlcipher3/0.6.2/)
- [`sqlcipher3` source](https://github.com/coleifer/sqlcipher3/tree/0.6.2)
- [`pysqlcipher3` maintenance warning](https://github.com/rigglemania/pysqlcipher3)

## Decision

No encryption dependency is admitted. The current binding is version-misaligned
with the reviewed core, and its native provenance and transitive cryptographic
dependencies have not passed Haven 42's package gates. Building a private fork
would add a maintenance and trademark burden and is not selected by this
review.

This record grants no installation, database, persistent-key, runtime, UI,
user-content, package, or production authority. Private session remains the
write-free default.

## Remaining gates

- Find or produce a maintained, version-aligned binding with immutable,
  verifiable provenance for every target platform.
- Verify every native binary and cryptographic dependency, then produce
  complete notices, SBOM, and vulnerability evidence.
- Pass encryption, wrong-key, tamper, migration, rekey, recovery, deletion,
  backup, and restore tests.
- Pass native source/package parity on Windows, Linux, and macOS before any
  runtime admission.
