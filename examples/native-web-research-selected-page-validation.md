# Native selected-page web-research validation

## What was tested

On August 16, 2026, the development-only selected-page transport ran from the
Windows source tree and from a native headless Linux environment. Both runs
used the exact normalized query `Distributed artificial intelligence`, a
single engine-derived citation, and its exact disclosed English Wikipedia
destination. Before fetching content, the command repeated the fixed metadata
query and required the citation identifier and destination to match the fresh
engine result.

The first Windows attempt refused safely when Wikipedia changed the ordering
of a broader three-result query between selection and revalidation. No page was
retrieved from that stale selection. The narrower stable selection then passed
on Windows and Linux with the same public content digest:

| Measurement | Result |
| --- | --- |
| Query SHA-256 | `dcd66815030d1eea6a9602e944d5f6924ccc91ad50594157222d0e1fcd168784` |
| Extracted-content SHA-256 | `7d4d58f6d9d2e4e7712020eaafc5860a9adf90c4247b1014b4231766f0045f04` |
| Inert text segments | 9 |
| Extracted characters | 1,211 |
| Windows source result | Passed |
| Native Linux source result | Passed |
| Linux temporary residue | None found |

The transport used the system trust store, performed two public-DNS passes,
pinned the connection to an address present in both results, preserved the
fixed TLS name and Host header, requested identity encoding, and followed no
redirects. It sent no credentials or cookies and ignored proxy environment
settings. The response was accepted only as bounded JSON from the fixed API;
the returned extract was processed by the existing UTF-8 plain-text boundary
and labeled untrusted inert text.

The exact source also passed 41 selected-page hostile checks, 21 query-
transport checks, and 26 inert page-text checks on both platforms. The Linux
run used a SHA-256-listed disposable bundle and the exact temporary directory
was removed afterward. This record contains no private address, hostname,
username, local path, credential, conversation, document, prompt, or model
response.

## What this proves

This proves a narrow development capability: an owner-invoked source command
can retrieve one explicitly selected page from one fixed provider while
binding the request to a fresh engine citation and applying the reviewed
transport, response, extraction, and cleanup boundaries on Windows and native
Linux.

It does **not** make web research available in Haven 42. There is no runtime
route, user-interface control, model tool, active citation navigation,
automatic follow-up, persistence, download path, page execution, or package
admission. The extracted material remains untrusted and this transport does
not establish factual correctness, cited-answer quality, or accessibility of a
future product flow.

## Remaining gates

- Add an accessible, keyboard-operable per-query and per-page review flow with
  clear provider, destination, privacy, progress, cancellation, error, and
  focus behavior.
- Render trusted citations from engine data without accepting model-supplied
  active links.
- Bind memory-only cancellation and lifecycle cleanup to a reviewed runtime
  route without granting autonomous search or follow-up authority.
- Add hostile local-server tests, macOS source evidence, and native package
  parity before considering promotion.
