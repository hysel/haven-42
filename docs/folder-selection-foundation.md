# Explicit Folder Selection Foundation

Folder context remains development-only and is not exposed through a runtime route or UI. The foundation inspects only a caller-selected test directory and defaults to non-recursive operation. Recursive inspection requires an explicit flag.

The manifest contains relative names, allowlisted extensions, byte counts, and SHA-256 digests. It contains no file content or absolute path. Inspection is bounded by depth, file count, per-file bytes, total bytes, and relative-path length. Links, reparse points, hidden entries, special files, unsupported extensions, non-UTF-8 content, binary content, executable signatures, and archive signatures fail the whole operation rather than being silently ignored.

This does not authorize automatic machine scanning, arbitrary path APIs, provider payloads, persistence, file changes, package inclusion, or UI activation. Semantic embeddings and persistent encrypted libraries remain separate future gates.
