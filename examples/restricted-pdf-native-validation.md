# Restricted PDF Native Validation

Date: 2026-07-30

This page records only sanitized source-form review evidence. It does not admit
a parser dependency, packaged worker, user document, runtime route, or release.

## Windows source cell

- Platform: Windows x86_64
- Python: 3.14.6
- Exact wheel SHA-256:
  `3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946`
- Artifact-lock checks: 33
- Synthetic-corpus checks: 78
- Restricted-worker checks: 61
- Static contract checks: 64
- Contract-parity/package-exclusion checks: 40
- Prospective evidence checks: 10
- Result: passed
- Package tested: no
- Runtime admission: no

The generated ignored evidence contains no hostname, username, network address,
absolute path, or raw document content.

## Linux source cell

Status: passed native execution.

- Platform: Ubuntu Linux x86_64
- Python: 3.14.4
- Exact wheel SHA-256:
  `3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946`
- Artifact-lock checks: 33
- Synthetic-corpus checks: 78
- Restricted-worker checks: 61
- Static contract checks: 64
- Contract-parity/package-exclusion checks: 40
- Prospective evidence checks: 10
- Result: passed
- Package tested: no
- Runtime admission: no

The exact ignored wheel was not installed. From the isolated source snapshot
on the Linux desktop, the native command was:

```bash
./scripts/validate-restricted-pdf-worker.linux.sh
```

The command verified Linux identity, exact artifact identity, availability of
the required POSIX resource limits, all 14 synthetic fixture digests, worker
timeout/crash/output/resource containment, contract parity, package exclusion,
and prospective compliance evidence. It writes only a sanitized ignored JSON
record under `dist/local-review/pdf-native-validation/`.

The resulting ignored evidence contains no hostname, username, network address,
absolute path, or raw document content. The result was not inferred from a
container, WSL session, synthetic platform override, copied Windows result, or
static contract output.

## Remaining parity boundary

Linux source evidence does not test a portable package. The current package
intentionally excludes `pypdf` and all restricted-worker scripts. A future
package-parity decision requires explicit parser/package admission first,
followed by exact packaged-component inventory and native execution on Windows,
Linux, and macOS. macOS remains pending physical hardware.

## Non-synthetic corpus intake

`config/pdf-hostile-corpus-intake-policy.json` requires immutable HTTPS source
identity, SHA-256 before opening, explicit redistribution permission, privacy
and malware review, a bounded category, and a manual retention decision. It
allows no automatic download or repository retention and currently accepts
zero external artifacts.
