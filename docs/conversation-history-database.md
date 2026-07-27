# Conversation History Database Foundation

Haven 42 does not currently save conversations. The local web application and
portable development package keep prompts, responses, prompt recall, selected
context, and provider details in memory and discard them at a task boundary or
shutdown according to the existing lifecycle policy.

This document defines the first offline, simulation-only foundation for an
optional local conversation database. It is architecture and test evidence, not
an active storage feature.

## Current boundary

`config/conversation-history-contract.json` is default-deny:

- **Private session** is the default and is provably write-free.
- No runtime route or UI control exists.
- No database is opened or created.
- No file, browser storage, network request, child process, provider call, or
  machine modification is allowed.
- The renderer and model cannot supply SQL, a query, database path, filename,
  command, URL, endpoint, credential, or environment value.
- Standard SQLite is explicitly treated as unencrypted at rest. The
  cross-platform encryption and key-management architecture has been reviewed,
  but no dependency or storage activation is admitted. See
  [Conversation History Encryption And Key-Management Review](conversation-history-encryption-review.md).

`config/conversation-history-schema.json` describes a bounded logical schema
for conversations, ordered messages, validated local summaries, sanitized
provider metrics, and attachment references. It contains no executable SQL.
Attachment bytes, credentials, provider endpoints, machine paths, environment
values, raw security logs, and model-generated commands are forbidden.

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

1. Select and admit a maintained SQLite-compatible encryption dependency such
   as SQLCipher, including exact binding, license, hashes, vulnerability
   posture, SBOM, third-party notices, and native packaging.
2. Implement and prove the reviewed fail-closed operating-system
   credential-store key handling for Windows, Linux, and macOS, including lock
   state, missing service, key loss, rotation, recovery, and uninstall.
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
