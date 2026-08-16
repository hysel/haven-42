# Windows Wrapped-Key Temporary Persistence Validation

Status: development-only synthetic proof; no application persistence or
package admission.

On August 15, 2026, Haven 42 generated a synthetic 32-byte database-key
candidate, wrapped it with current-user Windows DPAPI, wrote only the wrapped
bytes into a fresh test-owned temporary directory, recovered the key, and
removed all test files and the directory.

The 23 security checks prove the currently narrow boundary:

- the temporary file is created exclusively, flushed, and committed with a
  Windows no-replace rename;
- a destination created during the commit race is preserved and the temporary
  file is removed;
- an existing directory entry, missing key, empty or oversized blob, and
  tampered DPAPI blob fail closed;
- tamper and missing-key failures neither reset nor regenerate the key;
- recovered plaintext remains a mutable buffer and is wiped by the underlying
  DPAPI adapter;
- only fixed filenames inside a fresh test-owned temporary directory are used;
- the proof leaves no temporary residue and is excluded from the package.

This does **not** prove a production per-user directory or Windows ACL. It does
not persist a database, conversation, prompt, response, attachment, provider
detail, or user-selected path. It grants no runtime route, UI control, package,
or production authority. Atomic database-plus-key creation, key rotation,
locked or denied credential-store behavior, backup/restore, uninstall, Linux
Secret Service, macOS Keychain, and native packaged parity remain open gates.

Reproduce on Windows from the repository root:

```powershell
python scripts/test-conversation-history-windows-wrapped-key-persistence.py
python scripts/conversation-history-windows-wrapped-key-persistence.py
```

Expected test summary:

```text
Windows wrapped-key temporary persistence passed 23 security checks.
```
