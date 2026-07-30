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

An additional 26-check page-text foundation accepts only caller-supplied
bounded UTF-8 bytes labeled `text/plain` or `text/html`. Its strict HTML parser
keeps no attributes or remote references, rejects non-allowlisted elements,
doctypes, processing instructions, malformed nesting, NULs, invalid UTF-8, and
resource-budget violations, and returns only inert untrusted text segments.
It imports no network library, cannot fetch a URL, executes no page content,
writes no file, and remains absent from the application and package. This
tests extraction behavior without implementing selected-page retrieval.

Future live work still requires a separately reviewed fixed provider, explicit
per-query user action, DNS and resolved-IP revalidation, redirect revalidation,
response content and time budgets, transport-to-extractor binding, cancellation,
residue-free cleanup, source/package parity, and native evidence on each
supported platform. Citation navigation also remains a user-reviewed UI
decision.
