# Conversation History Encryption And Key-Management Review

Status: architecture reviewed; Windows current-user DPAPI, temporary wrapped-
key persistence, and synthetic per-user ACL proofs passed. Linux Secret Service
and macOS Keychain candidates have operation-free availability boundaries only.
Storage dependency, production application-directory binding, application
persistence, and runtime activation are not admitted.

The checked-in activation-readiness policy converts the remaining work into
eight exact, evidence-linked gates. Its 31-check hostile suite rejects missing,
reordered, traversing, effect-bearing, or overstated policy states. All gates
remain open and the evaluator always preserves Private session; it has no
database, credential-store, filesystem-write, runtime, UI, provider, or
network authority. See
[Conversation History Activation Readiness](../examples/conversation-history-activation-readiness.md).

Haven 42's optional conversation history remains simulation-only. No database
is opened or created, and Private session remains the write-free default. This
review narrows the acceptable future design; it does not authorize storage,
add a dependency, or make a product-readiness claim.

On August 15, 2026, the Windows source proof wrapped and unwrapped one
synthetic 32-byte key with current-user DPAPI. Its 16 checks cover the forbidden
machine-scope flag, UI denial, required entropy, tamper refusal, mutable
plaintext buffers, explicit buffer wiping, and package exclusion. It performed no persistent
write and grants no database, runtime, UI, user-content, package, or production
authority. See
[Windows conversation-history key-protection validation](../examples/windows-conversation-history-dpapi-validation.md).

A second Windows proof writes only the wrapped synthetic key inside a fresh
test-owned temporary directory. Its 23 checks cover exclusive temporary-file
creation, flush-before-commit, a no-replace rename race, recovery, tamper and
missing-key refusal without reset, cleanup, and package exclusion. It does not
claim a production per-user ACL and never opens a database or handles user
content. See
[Windows wrapped-key temporary persistence validation](../examples/windows-conversation-history-wrapped-key-persistence-validation.md).

A third Windows proof validates the ACL primitive without using an application
data directory. Its 24 checks create a protected test-owned directory, permit
only the current user and Local System, verify the synthetic key file inherits
only those rules, and fail closed after deliberately adding the built-in Users
group. It still grants no production application-directory or persistence
authority. See
[Windows per-user ACL validation](../examples/windows-conversation-history-per-user-acl-validation.md).

The Linux candidate has a separate 27-check offline availability boundary. It
uses one fixed user-bus listing command and reports only whether a session bus
and already-active `org.freedesktop.secrets` name were observed. It cannot
activate the service or read/write a secret, and it is excluded from the
package. The exact probe also passed a residue-free native headless container
cell with a reachable user bus and inactive Secret Service; that is expected
fail-closed evidence, not desktop or key-storage certification. Native desktop
evidence remains open. See
[Linux credential-store availability boundary](../examples/linux-credential-store-availability-boundary.md).

The macOS candidate has a separate 30-check offline availability boundary. It
invokes only `/usr/bin/security help` through a reviewed absolute system path,
with disabled stdin, a fixed environment, bounded discarded output, and a
five-second timeout. It cannot list, open, or unlock a keychain or inspect,
read, write, or delete an item. Results are exact predeclared public shapes,
and the probe is excluded from the package. The exact source probe passed a
GitHub-hosted macOS 15 cell. Physical Mac evidence, packaged parity, actual
Keychain operations, and lifecycle evidence remain open. See
[macOS Keychain availability boundary](../examples/macos-keychain-availability-boundary.md).

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

SQLCipher Community Edition is a candidate, not a selected dependency. The
August 15, 2026 review records 4.17.0 as the current official core, but does not
admit it: GitHub reports the annotated tag signature as `unknown_key` and the
target commit as unsigned, and the Community release provides no official
prebuilt desktop packages. The cross-platform `sqlcipher3` 0.6.2 binding embeds
the older SQLCipher 4.12.0 core, its reviewed PyPI uploads did not use Trusted
Publishing, and its native/transitive provenance has not passed Haven 42's
package gates. The legacy `pysqlcipher3` project is explicitly unmaintained.
See
[Conversation-history encryption dependency review](../examples/conversation-history-encryption-dependency-review.md).

Zetetic documents full-database encryption and a BSD-style license whose copyright,
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
- Resolve the current core/binding version mismatch and obtain immutable,
  independently verifiable native provenance; do not use the rejected
  unmaintained binding.
- Complete dependency, license, vulnerability, provenance, SBOM, and notices
  review for all three operating systems.
- Bind the proved Windows ACL primitive to the production application data
  directory and complete atomic database-plus-key creation,
  locked/denied/key-loss handling, rotation,
  backup, and recovery without a fallback. Extend the Linux Secret Service and
  macOS Keychain availability boundaries into independently reviewed adapters
  and prove their locked, absent, denied, corrupted, and headless behavior.
- Prove per-user locations and permissions, atomic create/rekey/migration,
  bounded growth, backup/restore, complete deletion, and secure shutdown.
- Add source-versus-packaged parity plus unsigned native Windows, Linux, and
  macOS tests.
- Owner approval to advance development was received on August 15, 2026. Do
  not activate a route, UI control, database access, or filesystem write until
  the remaining technical, privacy, native, accessibility, and package gates
  above pass.
