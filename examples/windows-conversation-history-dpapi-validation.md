# Windows conversation-history key-protection validation

## What was tested

On 2026-08-15, a development-only Windows proof generated a synthetic 32-byte
database key in memory, wrapped it with the current user's Data Protection API
(DPAPI) scope, unwrapped it, verified its digest, and wiped the mutable
plaintext buffers. The native DPAPI output buffer was also wiped before it was
released.

The implementation passed 16 security checks covering current-user scope,
forbidden user-interface prompts, required application entropy, exact key
length, mutable plaintext handling, source-buffer wiping, tamper refusal,
unsafe-contract refusal, package exclusion, and the absence of a machine-scope
flag or plaintext fallback.

The proof wrote no wrapped key, database, message, prompt, response, path,
provider detail, account identifier, or machine identity to disk or evidence.

## What this proves

This proves that the reviewed Windows source implementation can wrap and
unwrap one synthetic key with current-user DPAPI without requesting UI or
using machine-wide scope. It also proves that the exercised plaintext buffers
are mutable and explicitly wiped.

It does **not** activate conversation history. It does not select or open an
encrypted database, persist a wrapped key, handle user content, expose a
runtime route or user-interface control, enter a package, prove key rotation or
loss recovery, or provide Linux or macOS key protection.

## Remaining gates

- Select and admit the exact encrypted SQLite-compatible engine and binding,
  including provenance, license, vulnerability, SBOM, and native packaging.
- Implement atomic wrapped-key persistence, database creation, rotation, key
  loss, recovery, backup, restore, deletion, and uninstall behavior.
- Implement and hostile-test Linux Secret Service and macOS Keychain adapters
  with no plaintext fallback.
- Add explicit accessible opt-in UI while keeping Private session write-free by
  default.
- Pass source/package parity and native Windows, Linux, and macOS testing before
  product admission.
