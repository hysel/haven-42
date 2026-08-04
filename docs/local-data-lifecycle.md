# Local Data Lifecycle

Haven 42 separates product-owned engine files from user-owned configuration, models, artifacts, and logs. Uninstall may remove the selected engine version and session temporary files; it does not remove user configuration, models, provider data, or generated artifacts by default.

Raw prompts, raw responses, endpoints, and secrets are not persisted by default. Credentials, if a future provider needs them, belong in the operating system credential store rather than repository or configuration files. Logs are local, bounded, and sanitized.
The local-web application holds its readiness snapshot, zero-effect setup plan,
provider endpoint, discovered model names, per-capability model guidance, active
conversation model, request token, cleanup preference, prompt-recall limit,
bounded prompt-recall entries, explicitly selected `.txt`/`.md`/`.csv`/`.json`
or admitted source-text `.cs`/`.py`/`.js`/`.jsx`/`.ts`/`.tsx`/`.java`/`.go`/`.rs`/`.sql`/`.tf` context,
browsed or pasted PNG screenshots, and one continuous text conversation in
process and browser memory only. Prompt recall defaults to 20 entries and may
be changed to 50 or 100 for the current process; consecutive duplicates are
suppressed. One type-restricted picker accepts text and PNG together atomically.
Attached text is capped at five files, 64 KiB each, and 128 KiB total. CSV and
JSON receive bounded syntax/resource validation and inert format-aware previews;
neither JSON values nor CSV formulas are evaluated.
Attachment names and browser MIME values are untrusted. Known binary/container
signatures, forbidden control bytes, and high-confidence PowerShell, shell, or
batch masquerading are rejected before content enters task memory and are
revalidated by the loopback service. No scan result or rejected file is
persisted.
Screenshots are explicit file-picker or clipboard PNGs. The per-task browser
choice defaults to two and may be set from one through four; the engine retains
an absolute four-image cap, 4 MiB each, 8 MiB total, 4096 pixels per dimension,
16.7 million pixels per image, and 33.5 million combined decoded pixels.
No path is sent and no temporary file is created. For a private-network
provider, a prominent warning states that attached content will leave the
current machine; deliberate Send confirms that transfer without a separate
checkbox. Changing text-task intent does not clear the conversation. Direct
model/provider changes, request failure, and New task clear prompt recall and
attached context as documented; New task also clears the visible conversation
and unloads the active model. A confirmed task-specific model switch retains
only the context already selected for that pending request, and nothing is sent
before the explicit decision. Closing the process discards all runtime state
and triggers cleanup. A readiness snapshot expires for planning and is never
written automatically. Browser assets and API responses use
`Cache-Control: no-store`; the application adds no service worker, local
storage, session storage, IndexedDB, cookies, analytics, or crash upload.

The offline lexical-retrieval engine, restricted parser-worker foundation,
inactive web-research foundation, and conversation-history foundation retain
no application runtime state because none exposes a route. The parser
foundation opens no document and starts no worker. Lexical test state is caller-owned memory and is cleared
on removal, failure, and shutdown; it has no persistence API. The history
foundation contains a logical schema and pure planners. A separate development
validator opens only a fresh temporary SQLite database containing fixed
synthetic records, verifies backup/restore and deletion, and removes every
sidecar; it cannot accept a caller path or user content and is absent from the
runtime and package. Private session remains the default and write-free. See
[Conversation History Database Foundation](conversation-history-database.md)
and [Conversation History Encryption Review](conversation-history-encryption-review.md).

The folder-selection foundation is also a command-line development validator,
not an application scanner. It requires one explicit absolute root, defaults to
non-recursive inspection, enforces depth/file/byte budgets and the existing
text/source allowlist, rejects links, reparse points, hidden/special files,
archives, binary signatures, NULs, non-UTF-8 data, and files that change during
the read, and returns only relative names, sizes, extensions, and digests. It
stores no content or path and grants no browser, provider, watcher, index, or
background authority.

Restricted PDF and complex-document review fixtures, candidate artifacts, and
native evidence exist only beneath ignored `dist/local-review` during explicit
development tests. They are not application data, are never searched or sent
to a provider, and are excluded from packages and repository history. Native
evidence contains only normalized platform, architecture, Python version,
fixed check counts, and false admission fields; it records no hostname,
username, endpoint, absolute path, or document content. External PDF corpus
research retains metadata only and currently selects or downloads no document.


Deletion is always previewed and scoped by data class. Cleanup after a test or failed operation may remove only data created by that run. Preexisting models and provider-owned data require explicit provider-specific confirmation. The result must say what was removed and whether recovery is possible.

Export is opt-in. It includes a manifest and integrity hashes, excludes secrets, and sanitizes machine-specific paths by default. The normative rules are in `config/local-data-lifecycle-contract.json`.
