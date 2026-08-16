# Native Linux web-research query transport validation

## What was tested

On August 15, 2026, the development-only fixed-Wikipedia query transport ran
from a native headless Linux environment. The four required source and contract
files were transferred as one SHA-256-verified bundle, extracted beneath a
fresh `/tmp` directory, and invoked for one explicit three-result metadata
query.

The sanitized result recorded three accepted results and reported that more
provider results were available. It also confirmed system TLS trust, two-pass
public DNS validation, connection pinning to an address present in both DNS
passes, and denial of redirects, credentials, cookies, response compression,
and proxy-environment inheritance. A separate post-run check found no matching
temporary directory.

No query, title, result text, destination, private address, hostname, username,
path, account information, prompt, or response was retained in the evidence.

## What this proves

The exact source transport can perform its narrow fixed-provider metadata query
under native Linux as well as Windows while preserving its reviewed transport
boundary. The bundle integrity and residue checks also show that this one
development run did not depend on a persistent installation.

It does **not** make web research available in Haven 42. The app still has no
research route, UI control, model tool, page retrieval, active navigation,
automatic follow-up, persistence, or package admission. Result metadata remains
untrusted and this test does not prove answer correctness.

## Remaining gates

- Add an explicit, keyboard-accessible per-query review and cancellation flow.
- Add trusted citation rendering with destination disclosure and no
  model-supplied active links.
- Keep page retrieval separate until its SSRF, extraction, approval, and
  cleanup gates pass.
- Complete native package parity and macOS source evidence before promotion.
