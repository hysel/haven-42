# Conversation History Encryption And Key-Management Review

Status: architecture reviewed; storage dependency and runtime activation are
not admitted.

Haven 42's optional conversation history remains simulation-only. No database
is opened or created, and Private session remains the write-free default. This
review narrows the acceptable future design; it does not authorize storage,
add a dependency, or make a product-readiness claim.

## Decision boundary

Any future persistent history must encrypt the entire database at rest with an
admitted SQLite-compatible encryption implementation. The randomly generated
database key must be wrapped by a credential facility scoped to the current
operating-system user:

| Platform | Candidate user-scoped facility | Required behavior |
| --- | --- | --- |
| Windows | Data Protection API (DPAPI), without `CRYPTPROTECT_LOCAL_MACHINE` | Bind recovery to the same user and normally the same computer; treat unwrap or integrity failure as locked storage. |
| macOS | Keychain Services | Store only the small database key, use an application-specific service/account identity, and respect keychain lock and access-control failures. |
| Linux | Secret Service API through an independently admitted binding | Require an available, unlocked user secret service; headless or unavailable service fails closed. |

There is no common insecure fallback. Haven 42 must never place a plaintext
database key beside the database, silently derive one from a username or
machine identifier, embed one in the executable, log it, send it to a provider,
or downgrade to plaintext SQLite. If the platform facility is unavailable,
locked, corrupted, or denies access, Haven 42 must preserve the database and
continue in Private session without writing history.

SQLCipher Community Edition is a candidate, not a selected dependency. Zetetic
documents full-database encryption and a BSD-style license whose copyright,
conditions, disclaimer, and integrated dependency notices must be accessible
to users. Before admission, the exact core version, Python/native binding,
source and wheel provenance, hashes, signatures, vulnerability posture,
cryptographic provider, license obligations, SBOM entries, and portable
Windows/Linux/macOS behavior require a separate review. Haven 42 must not
represent Community Edition as a supported or FIPS-validated package.

Primary references:

- [Zetetic SQLCipher Community Edition and attribution requirements](https://www.zetetic.net/sqlcipher/community/)
- [Zetetic SQLCipher license information](https://www.zetetic.net/sqlcipher/license/)
- [Microsoft `CryptProtectData` documentation](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)
- [Apple Keychain Services documentation](https://developer.apple.com/documentation/security/keychain-services)
- [freedesktop.org Secret Service API](https://specifications.freedesktop.org/secret-service/latest/)

## Key lifecycle

A later implementation must prove the following before activation:

1. Generate a high-entropy database key locally and keep plaintext key material
   only in bounded process memory.
2. Create the encrypted database and wrapped key as one recoverable operation;
   an interrupted first run must not leave plaintext or an unusable partial
   database presented as healthy.
3. Zero or release plaintext key buffers on lock, task boundary where
   applicable, failure, and shutdown to the extent the admitted runtime permits.
4. Rotate by rekeying transactionally, verify the new key, replace the wrapped
   key atomically, and preserve a recoverable pre-rotation state until success.
5. Treat a missing or inaccessible wrapped key as key loss. Never reset,
   overwrite, delete, or recreate the database automatically.
6. Make backup and restore preserve encryption. A backup must never contain
   plaintext history or an unwrapped key.
7. Require explicit user choice for deletion on uninstall. Removing application
   files must not silently remove either history or its key.

Credential-store entries must contain only an opaque database identifier,
schema/key-format version, and wrapped database key. Conversation content,
provider endpoints, credentials, paths, prompts, and telemetry do not belong in
the credential store. Database filenames and locations remain engine-owned,
per-user, and outside renderer/model authority.

If attachment snapshots are later admitted, their exact validated bytes and
metadata must be covered by the same encryption, per-user access, retention,
backup, recovery, and deletion guarantees as messages. Original filesystem
paths and live references are forbidden. An unavailable, deleted, or
integrity-failed snapshot must fail closed and must not be reconstructed from
the original file without a new user selection.

## Recovery and migration

Wrong-key, tamper, corruption, locked-store, unavailable-store, disk-full, and
interrupted-migration states must be distinguishable without exposing secrets.
Recovery is read-only until the user selects a documented action. Schema
migration and encryption-format migration require atomic transactions,
integrity verification, rollback evidence, and native package tests. Downgrade
to an older schema or plaintext database is forbidden.

Export/import and user-supplied passphrases are separate future decisions. No
recovery phrase or password flow is implied by this architecture. A password
design would need explicit UX, KDF parameters, retry limits, secure-memory
review, recovery expectations, and new approval.

## Remaining admission gates

- Select and pin the database engine, binding, and cryptographic provider.
- Complete dependency, license, vulnerability, provenance, SBOM, and notices
  review for all three operating systems.
- Prototype each credential-store adapter without a fallback and prove locked,
  absent, denied, corrupted, and headless behavior.
- Prove per-user locations and permissions, atomic create/rekey/migration,
  bounded growth, backup/restore, complete deletion, and secure shutdown.
- Add source-versus-packaged parity plus unsigned native Windows, Linux, and
  macOS tests.
- Obtain separate approval before any route, UI control, database access, or
  filesystem write is activated.

