# Post-quantum cryptography readiness

Reviewed on 2026-08-04. This page records the cryptographic inventory and migration
foundation. It does not enable encryption, select a production algorithm,
change TLS behavior, add a dependency, generate or read a key, verify a
signature, authorize a package, activate an update, or modify a machine.

## Why Haven 42 is preparing now

Future cryptographically relevant Haven 42 boundaries include HTTPS provider
connections, optional encrypted history, release authenticity, and update
authorization. NIST recommends identifying current public-key dependencies and
planning migration before attempting deployment. Haven 42 therefore records
its current boundaries and requires algorithm agility while the affected
runtime and platform ecosystems mature.

The standards used as candidates are:

- [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final): ML-KEM for key
  establishment;
- [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final): ML-DSA for digital
  signatures; and
- [FIPS 205](https://csrc.nist.gov/pubs/fips/205/final): SLH-DSA as an
  alternative hash-based signature family.

NIST's
[Migration to Post-Quantum Cryptography](https://www.nccoe.nist.gov/applied-cryptography/migration-to-pqc)
project emphasizes cryptographic inventory, interoperability, and planned
migration. A new algorithm is not assumed to be a drop-in replacement.

## Current inventory

`config/cryptographic-inventory.json` is the machine-readable inventory. The
important distinctions are:

| Boundary | Current position | PQC consequence |
| --- | --- | --- |
| Browser to local service | IPv4-loopback HTTP with session and CSRF authority | This is not a remote public-key boundary; PQC would not improve it. |
| Private provider over HTTP | Unencrypted and visibly warned | PQC cannot make HTTP secure. Use trusted HTTPS or a loopback tunnel. |
| Private provider over HTTPS | Python `ssl` and its bundled OpenSSL policy | The actual key-establishment group and certificate signature must be observed before making any quantum-resistant claim. |
| Package and resource integrity | SHA-256 digests without publisher authenticity | Retain the current digest while keeping the algorithm identifier versioned. A digest is not a signature. |
| Session and CSRF authority | Random tokens from Python `secrets` | Preserve strong entropy and bounded lifetime; no public-key migration is indicated. |
| Optional conversation history | Architecture-only AES-256 full-database encryption candidate with an OS-wrapped random key | PQC is not a replacement for symmetric bulk encryption or same-device OS key protection. |
| Update authorization | Structural contracts only; no verifier exists | Evaluate a dual classical and ML-DSA signature transition only after an exact verifier is admitted. |
| Platform code signing | Policy only; inactive | PQ evidence may supplement but cannot replace Authenticode, Apple code signing/notarization, or platform trust. |

There is currently no Haven 42 application-level content encryption or active
cryptographic updater verification. Conversation content remains memory-only.

## Candidate profiles

### Hybrid provider TLS

The initial research candidate is TLS 1.3 hybrid key establishment using
`X25519MLKEM768`. OpenSSL 3.5 added ML-KEM, ML-DSA, and SLH-DSA and documents
`X25519MLKEM768` as a hybrid TLS group in its
[TLS configuration documentation](https://docs.openssl.org/3.5/man3/SSL_CONF_cmd/).
The reviewed Windows Python 3.14.6 development runtime currently reports
OpenSSL 3.5.7, but that observation is not cross-platform or packaged evidence.

Haven 42 will not claim post-quantum TLS until the exact client and server,
negotiated group, certificate signature, native platform behavior, and
source-versus-package parity are measured. The provider or TLS terminator must
also support the profile. Hybrid negotiation is preferred when both peers
support it, but PQC is not required to establish an otherwise valid secure
connection. A secure classical fallback remains allowed and must be reported
as classical; it must never be silently described as post-quantum protection.

SSH remains an operating-environment transport rather than a Haven runtime
cryptographic boundary. The same compatibility principle applies to test
automation: a peer may offer a hybrid SSH key exchange, while an incompatible
client may use an admitted classical exchange without creating a PQC claim.

### Future update authorization

The candidate migration mode requires both the admitted classical signature
and a selected ML-DSA signature during transition. Neither a parameter set nor
a verifier is selected. Before activation, the project requires a canonical
signed envelope, immutable verifier identity, deterministic valid and hostile
vectors, rotation and compromise recovery, native package evidence, and an
independent security review.

SLH-DSA remains an alternative algorithm-family candidate. It is not a default
because its exact parameter set, signature size, performance, verifier, and use
case have not been selected or measured.

PQC evidence cannot replace Windows Authenticode, Apple platform signing and
notarization, or any required Linux distribution trust. Unsigned development
artifacts remain unsigned.

### Future encrypted history

The existing full-database AES-256 candidate remains appropriate for bulk
local encryption. The difficult boundary is safe same-user key storage,
availability, rotation, deletion, recovery, and native packaging. ML-KEM does
not solve those same-device operating-system key-management requirements.

## Fail-closed rules

`config/post-quantum-cryptography-contract.json` requires:

- standards-conformant maintained libraries rather than custom cryptography;
- versioned algorithm identifiers and envelopes;
- rejection of unknown algorithms and missing required signatures;
- retention of classical protection during the transition;
- rejection of silent downgrade and unobserved TLS claims;
- no private keys in the repository, logs, renderer, or model context; and
- exact security, dependency, native-platform, package-parity, performance,
  rollback, and owner-approval gates before activation.

The offline validator accepts no caller input or cryptographic material and
has no network, key, trust-store, package, update, or machine authority. Its
hostile suite tests contract drift, premature selection, downgrade, unsafe
claims, and effect escalation. Passing it proves only that the planning
foundation remains inactive.

## Remaining gates

1. Select no exact runtime profile until the relevant protocol and library
   integration can expose reliable negotiation and verification evidence.
2. Re-review NIST errata, library maintenance, licenses, vulnerabilities, and
   platform support at selection time.
3. Add deterministic cryptographic test vectors through an independently
   reviewed implementation; never implement the primitives in Haven 42.
4. Validate source and frozen packages on Windows, Linux, and macOS.
5. Complete key lifecycle, downgrade, compatibility, rollback, incident, and
   compromise-recovery exercises.
6. Obtain a separate owner decision before activating any profile.

Until every applicable gate passes, the project is PQC-ready only at the
inventory and crypto-agility planning layer and makes no quantum-resistant or
production-readiness claim.
