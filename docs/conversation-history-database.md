# Conversation History Database Foundation

Haven 42 does not currently save conversations. The local web application and
portable development package keep prompts, responses, prompt recall, selected
context, and provider details in memory and discard them at a task boundary or
shutdown according to the existing lifecycle policy.

This document defines the offline foundation for an optional local conversation
database. It is architecture and development-test evidence, not an active
storage feature.

`config/conversation-history-development-contract.json` and
`scripts/validate-conversation-history-development.py` add a self-contained
SQLite development exercise. It creates only fixed synthetic records inside a
fresh temporary directory, uses fixed DDL and parameterized writes, verifies a
read-only backup/restore path and cascade deletion, and removes the database,
journal, WAL, shared-memory, and backup files. It accepts no caller database
path or user content and exposes no route, UI, provider, package, or persistent
application behavior.

## Current boundary

`config/conversation-history-contract.json` is default-deny:

- **Private session** is the default and is provably write-free.
- No runtime route or UI control exists.
- No application or user database is opened or created; the separate
  development validator uses only its own temporary synthetic database.
- No file, browser storage, network request, child process, provider call, or
  machine modification is allowed.
- The renderer and model cannot supply SQL, a query, database path, filename,
  command, URL, endpoint, credential, or environment value.
- Standard SQLite is explicitly treated as unencrypted at rest. The
  cross-platform encryption and key-management architecture has been reviewed,
  and Windows current-user DPAPI, test-owned temporary wrapped-key, and
  synthetic per-user ACL proofs passed. The ACL proof limits a protected test
  directory and inherited key file to the current user and Local System and
  rejects a deliberately added Users-group rule. These proofs do not cover the
  production application directory or application persistence. No database
  dependency or storage activation is admitted.
  See
  [Conversation History Encryption And Key-Management Review](conversation-history-encryption-review.md).
- The Linux Secret Service candidate has an offline-tested, non-activating
  availability probe that returns sanitized booleans only. It does not select a
  binding or grant credential-store authority; native desktop and headless
  behavior remain unproved.

`config/conversation-history-schema.json` describes a bounded logical schema
for conversations, ordered messages, validated local summaries, sanitized
provider metrics, and attachment references. It contains no executable SQL.
Attachment bytes, credentials, provider endpoints, machine paths, environment
values, raw security logs, and model-generated commands are forbidden.

Attachment persistence is deliberately a separate future admission. History
must never retain a live filesystem path or silently reopen an original file.
The safe candidate is an explicit per-conversation opt-in that creates an
encrypted, conversation-owned snapshot of the exact admitted content. Each
snapshot must bind a safe filename, media type, digest, byte count, validation
version, message, retention policy, and deletion state. Text, CSV, and JSON can
use normalized validated UTF-8 bytes; an image can only be restored as context
when its exact admitted canonical bytes are retained. A thumbnail is a preview,
not restorable model context.

On reopen, the UI must distinguish available, deleted, unavailable, and
integrity-failed snapshots, and show which ones will be sent before a provider
request. Missing bytes fail closed: Haven 42 must not imply that the model saw
them. Attachment rows, encrypted blobs, indexes, free pages, journals/WAL,
temporary files, and backups all fall under retention and deletion behavior.

## Effect-free planner

`scripts/simulate-conversation-history.py` validates typed requests and returns
plans only. It supports:

- schema inspection without executable DDL;
- version 0-to-1 migration and interrupted-migration rollback planning;
- Private session, 30-day, 90-day, and forever retention planning;
- bounded recent-message and separately validated summary selection by metadata
  only, without including message content or invoking a provider;
- scoped conversation deletion or clear-all planning, including indexes,
  journal/WAL state, and optionally backups;
- busy/locked, interrupted-write, corruption, and disk-full recovery planning;
- bounded backup and restore validation with deferred filesystem grants,
  integrity verification, active-content rejection, and no attachment bytes.

Every successful result declares all effects false. The command-line entry point
prints only a generic acceptance message, so request-derived identifiers or
private content are not logged.

## Threat cases

The hostile fixture set rejects renderer SQL, traversal-like database paths,
credentials, unknown operations, schema downgrades, forged migration
conditions, future retention timestamps, cross-conversation context,
unsupported roles, message reordering, unvalidated summaries, ambiguous
clear-all targets, attachment bytes, unverified or active-content restores, and
oversized backup counts.

The tests also enforce exact request fields, bounded identifiers and token
budgets, bounded nesting and container complexity, no caller filesystem grant,
no executable SQL, all-false effects, and the unencrypted/unadmitted storage
state.

## Promotion gates

No development database may be activated until separately approved work
completes all of these gates:

1. Select and admit a maintained SQLite-compatible encryption dependency. The
   current SQLCipher 4.17.0 and Python-binding review admits nothing because the
   reviewed cross-platform binding embeds 4.12.0 and its provenance gates are
   incomplete. A future candidate still requires an exact version-aligned
   binding, license, hashes, vulnerability posture, SBOM, third-party notices,
   and native packaging.
2. Finish the reviewed fail-closed operating-system credential-store key
   handling for Windows, Linux, and macOS. The Windows current-user DPAPI
   synthetic round trip, temporary wrapped-key no-replace commit, and the
   underlying protected per-user ACL primitive are proved; production
   application-directory binding, atomic database-plus-key creation, lock state, missing
   service, key loss, rotation, recovery, uninstall, Linux Secret Service, and
   macOS Keychain evidence remain open.
3. Prove least-privilege per-user locations and permissions without accepting a
   renderer/model path.
4. Implement parameterized typed operations, atomic transactions, deterministic
   migrations, rollback, busy handling, corruption detection, disk-full
   recovery, bounded growth, and secure shutdown.
5. Prove permanent delete, clear-all, backup, restore, export/import, uninstall,
   WAL/journal/free-page handling, and interrupted-operation recovery.
6. Add explicit UI disclosure and opt-in while preserving Private session as
   the default.
7. Pass source-versus-packaged parity and native unsigned Windows, Linux, and
   macOS package tests before any later production-readiness decision.

Cloud synchronization, remote databases, shared/multi-user history, online
backup, telemetry, and a persistent document library remain separate,
unapproved security boundaries.
