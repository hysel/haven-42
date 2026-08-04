# Controlled Web Research Foundation

Milestone 28 remains runtime-unadmitted. Haven 42 has no general internet model
tool, research UI route, DNS authority, URL fetcher, browser automation, page
renderer, download path, or autonomous follow-up search.

The offline adapter foundation validates caller-supplied fixtures only. It:

- accepts one explicit bounded query for a fixed offline fixture provider;
- rejects credential-like queries and control characters;
- accepts strict result metadata only from public HTTPS destinations;
- rejects credentials, custom ports, fragments, URL queries, local hostnames,
  and non-global IP literals;
- rejects active markup, duplicate URLs, malformed timestamps, unknown fields,
  oversized result sets, and response-budget overflow;
- derives citation identifiers inside the engine boundary;
- keeps URLs inactive and requires future destination disclosure;
- accounts for every cited source exactly and rejects unknown, duplicate, or
  model-invented citation identifiers.

This foundation imports no socket, HTTP client, browser, or child-process
library. It makes no DNS request, opens no connection, writes no file, and is
absent from the application and portable package. Passing fixture validation
does not admit a live search provider or page retrieval.

The separately disabled query-adapter prototype fixes the destination to the
English Wikipedia metadata search API and permits only a bounded query and
result count to vary. Tests inject a fixture transport; the implementation has
no HTTP client and revalidates the complete request and strict response shape
before producing inactive engine-derived destination metadata. It cannot run
from the product, accept a model-selected destination, retrieve a page, or
persist a result.

An additional 26-check page-text foundation accepts only caller-supplied
bounded UTF-8 bytes labeled `text/plain` or `text/html`. Its strict HTML parser
keeps no attributes or remote references, rejects non-allowlisted elements,
doctypes, processing instructions, malformed nesting, NULs, invalid UTF-8, and
resource-budget violations, and returns only inert untrusted text segments.
It imports no network library, cannot fetch a URL, executes no page content,
writes no file, and remains absent from the application and package. This
tests extraction behavior without implementing selected-page retrieval.

A separate 26-check cited-synthesis foundation accepts only the validated
result bundle and optional inert page segments from those two boundaries. It
builds a bounded, digest-accounted, URL-free source envelope and validates
caller-supplied candidate claims only when every claim names one or more exact
engine-derived citation identifiers. It rejects unknown or duplicate
citations, uncited claims, active links, markup, control characters,
unaccounted pages, altered trust or authority fields, oversized claims, and
follow-up fields. Its output discloses used and unused sources while keeping
model invocation, tool execution, network access, files, persistence, runtime,
UI, and automatic follow-up authority false. It does not call a model or prove
answer correctness.

The 26-check suite passes from the same sanitized, SHA-256-verified source
bundle on native Windows and Ubuntu Linux. The Ubuntu run first rejected an
incomplete bundle at import because two required contracts were absent; a fresh
self-contained bundle then passed. This establishes source-test parity only.
The boundary remains deliberately absent from the product runtime and portable
package, and macOS source evidence plus all native package smoke remain open.

Future live work still requires a separately reviewed fixed provider, explicit
per-query user action, DNS and resolved-IP revalidation, redirect revalidation,
response content and time budgets, transport-to-extractor binding, cancellation,
residue-free cleanup, source/package parity, and native evidence on each
supported platform. Citation navigation also remains a user-reviewed UI
decision.

`config/web-research-expansion-evaluation.json` records two later gates without
activating either: a self-hosted provider must meet the same public-destination
and transport controls, and multi-query research is capped at four visible
queries with separate approval and cancellation. No autonomous or page-derived
follow-up is allowed.
