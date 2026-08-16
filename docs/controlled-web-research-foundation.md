# Controlled Web Research

_Last reviewed: August 16, 2026._

## What is available

Haven 42 has two narrowly admitted in-app web-research paths. A person can
search the English Wikipedia metadata API, review returned source titles and
full destinations as inactive text, and separately approve reading one
selected page as inert plain text. A person can also approve one bounded
multi-source search that uses the fixed Brave Search API, retrieves at most
five returned public HTTPS pages, and asks the selected local Ollama model for
a strict citation-bound answer.

The interface also retains a separate wider-web browser handoff. After reviewing
the exact words and fixed Brave Search destination, the user may open that
search in their normal browser. Haven 42 does not fetch, parse, persist, cite,
or send those browser results to a model. This handoff is not evidence that
general in-app browsing or cited synthesis has been admitted.

This is not autonomous model browsing. The local model cannot start a search,
choose a provider, choose or alter a URL, approve a request, follow a result,
retrieve another page, or trigger a follow-up query. Haven 42 does not yet feed
Wikipedia text to a model. The multi-source path sends only bounded untrusted
source segments—not URLs, credentials, or tools—to the selected local model,
then rejects any claim without an engine-issued citation.

## User flow

1. Open **Research the web**, keep **Wikipedia** selected, and enter at most
   256 characters.
2. Review the exact search words and provider in a modal dialog. Nothing has
   been sent at this point.
3. Choose **Approve once** or cancel. Approval is held only in server memory,
   expires after five minutes, and can be used once.
4. Review the returned titles, source domain, retrieval time, and complete
   inactive destinations.
5. Choose **Review page request** for one result. A second modal shows the
   selected title and exact destination before any page request.
6. Approve once to retrieve a bounded plain-text extract. The content is shown
   as inert text; it cannot execute or create an active link.

Starting a New task clears pending approvals, results, page text, and citations
from both browser and server memory. Shutdown also clears server-held research
state. Haven 42 writes no query, result, page, cookie, cache, download,
temporary file, browser-storage record, or telemetry event for this feature.

For a wider-web search, choose **Wider web**, review the exact query and fixed
Brave Search URL, approve once, then use the newly revealed browser link. The
server never contacts Brave in that flow. The browser request and any retention
by the search provider are governed by the browser and provider, not Haven 42.

For a cited wider-web answer, choose **Wider web with a cited answer**, enter a
Brave Search API key for the current request, and review the exact query,
provider, and fixed API destination. After one approval, Haven 42 sends the key
only to Brave, clears it after use, cancellation, failure, or expiry, validates each result as public
HTTPS, retrieves at most five pages without redirects or active content, and
asks the selected local model for a strict JSON claim list. The renderer accepts
only claims whose citation identifiers were issued by the engine. Citations and
full destinations remain inactive text.

## Network boundary

The engine owns the complete network operation. The admitted transports use:

- the fixed host `en.wikipedia.org`, port 443, and path `/w/api.php`;
- the operating system trust store and the fixed Wikipedia TLS server name;
- two public-DNS checks and a selected public address pinned to the connection;
- fixed API parameters with only the reviewed query, result count, or validated
  numeric page identifier allowed to vary;
- identity encoding, redirect refusal, no proxy-environment inheritance, no
  credentials, and no cookies;
- strict content type, byte, time, JSON-depth, JSON-node, and result limits;
- a fresh metadata-query revalidation before a selected-page request; and
- strict response shapes, engine-derived citation identifiers, and exact digest
  binding before anything reaches the renderer.

The multi-source transport adds a fixed `api.search.brave.com` search endpoint,
session-only `X-Subscription-Token`, at most five validated public HTTPS result
destinations, 512 KiB per-page and 20,000-character aggregate context ceilings,
and a fresh public-DNS check plus connection pin for every page. It refuses
redirects, compression, cookies, proxy inheritance, credentials in URLs, active
markup, non-public addresses, model-supplied links, and automatic follow-up.

Loopback, private, link-local, reserved, multicast, unspecified, credentialed,
or custom-port destinations are rejected. Response fields remain untrusted.
The page transport accepts only the fixed API's plain-text extract and exposes
it as bounded `textContent`; HTML execution, remote media, scripts, styles,
frames, objects, embeds, downloads, and active navigation stay disabled.

## Approval and accessibility

Search and page retrieval each require a separate trusted user action. Scripts,
models, synthetic DOM clicks, expired tokens, reused tokens, wrong-kind tokens,
and altered selections cannot approve a request. Tokens are random, bounded,
single-use, server-owned, and never persisted.

The review dialog has an accessible name and description, moves focus inside,
traps keyboard focus, supports Cancel, close, and Escape, makes the background
inert, returns focus after dismissal, and announces status changes. Its actions
remain visible inside the scrollable dialog at small window heights. Controls
meet the 44-pixel target floor; long destinations wrap; forced colors and
reduced motion are supported. Retrieved source text and citations have labeled
regions and no interactive descendants.

Automated coverage does not replace manual assistive-technology testing. The
Accessibility Statement records the current screen-reader/browser limitation.

## Evidence currently recorded

- The query adapter passes 16 strict request/response checks, including stable
  citation identity when the provider changes result order.
- The fixed query transport passes 23 hostile offline security checks.
- The selected-page transport passes 41 hostile offline security checks.
- The product runtime passes 48 hostile offline and local-API checks, including
  token expiry/replay, wrong-kind consumption, malformed provider responses,
  CSRF refusal, and New task cleanup.
- The trusted citation renderer passes 40 checks.
- The explicit approval review passes 64 checks.
- The local-web server suite passes 479 security and behavior checks.
- The multi-source search, retrieval, synthesis, and lifecycle boundary passes
  21 dedicated hostile checks; the shared research runtime passes 48 checks.
- The Windows headless Chromium flow passes 654 checks, including the complete
  two-approval research flow, inert page rendering, focus behavior, a short
  viewport, New task cleanup, and no active result links.
- One Windows source-runtime live check completed a fixed English Wikipedia
  query and separately approved selected-page retrieval. The sanitized record
  and its remaining platform/package gates are in
  `examples/live-wikipedia-runtime-validation.md`.
- The integrity-verified exact unsigned Windows `0.4.0-alpha.2` package passed
  the same live query and selected-page path. Signing, Linux, macOS, and manual
  assistive-technology evidence remain open.
- Earlier sanitized source-only live queries and selected-page reads passed on
  Windows and native headless Linux with matching page-content digests.

These results establish source behavior on the named configurations. They do
not establish manual screen-reader coverage, signed-package status, release
promotion, macOS behavior, or native packaged parity on every supported
platform. Package parity must be repeated on the exact candidate before this
feature can be described as package-validated.

## Authority that remains denied

- unrestricted in-app web access or arbitrary user/model-selected URLs;
- model tools, model-initiated searches, or model approvals;
- automatic or page-derived follow-up queries;
- active citation links or browser navigation;
- page code, HTML rendering, remote assets, files, or downloads;
- query, result, citation, page, cookie, cache, log, or telemetry persistence;
- retrieval of repository content, attachments, hardware facts, provider
  endpoints, usernames, paths, conversation history, or model metadata; and
- uncited model synthesis or a correctness claim beyond source accounting.

The self-hosted-provider and bounded multi-query contracts remain independent,
inactive evaluations. They grant no runtime, provider, network, UI, model-tool,
or package authority.

## Foundation retained for later work

The repository keeps the earlier effect-free foundations and hostile fixtures:

- a 28-check offline query/result/citation boundary;
- a 25-check transport guard covering destination, DNS, redirect, encoding,
  content-type, time, and byte receipts without network access;
- a 17-check memory-only approval-state proof;
- a 27-check inert page-text parser that is packaged only through the fixed
  selected-page transport and has no network authority of its own; and
- a 26-check cited-synthesis validator that invokes no model.

Those components remain evidence for provider expansion and stricter future
quality gates. Only the separately reviewed multi-source route above invokes a
local model, and it does not expand model authority.

## Remaining promotion gates

1. Build an exact portable candidate with the research modules and protected
   resource contracts included.
2. Repeat source/package parity and native packaged browser smoke on Windows,
   Linux, and macOS. Physical macOS testing remains owner-parked.
3. Complete the documented manual keyboard, zoom, forced-color, and named
   screen-reader/browser matrix.
4. Repeat multi-source synthesis with the exact packaged candidate and record
   source-accounting, failure, and cleanup parity.
5. Keep self-hosted search, automatic multi-query research, and active navigation as
   separate owner-approved gates.
