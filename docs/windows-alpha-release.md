# Windows Alpha release record

Haven 42 `0.4.0-alpha.1` was published on 2026-08-05 as a public, unsigned
GitHub prerelease for invited Windows 11 x64 testing. The publication is a
test-distribution decision, not a stable or production promotion.

The fail-closed machine-readable record is
`config/windows-alpha-release-record.json`. It binds the publication to:

- tag `v0.4.0-alpha.1`;
- exact source commit `6624dfb967a58c67d2d5a9a01437cf3213eee289`;
- `haven42-0.4.0-alpha.1-windows-x64-unsigned.zip`;
- byte length `9650721`; and
- SHA-256
  `d1648667807dde37c645beb2199503b8a4852a585a2f62eb4ebe2c0b90465106`.

The record also fixes the official release, hosted-validation, issue-reporting,
and private-vulnerability-reporting URLs. Hostile tests reject a changed tag,
commit, artifact name, size, digest, evidence URL, reporting URL, platform, or
authority boundary.

Publication grants no signing, notarization, installer, automatic core-update,
driver, service, firewall, Tauri/Rust, bundled external-software, stable-release,
or production authority. Future candidates require their own exact artifact,
security, privacy, native, hosted, owner, and publication decisions.
