# Live Wikipedia runtime validation

Last reviewed: August 16, 2026

## Result

The Haven 42 source runtime completed one fixed-provider English Wikipedia
query and one separately approved selected-page retrieval on Windows. This is
a narrow development validation, not a release certification or evidence for
Linux, macOS, or a packaged application.

The run returned three engine-accounted citations and extracted 1,307
characters of inert text from the selected page. Both approval tokens were
single-use. The runtime reported that active navigation, page execution,
model-tool access, automatic follow-up, and content persistence were disabled.

## Issue found and corrected

The first live attempt failed closed because citation IDs included the search
result's rank. Wikipedia may return the same pages in a different order on a
fresh query, so the selected source could not be rebound reliably. Citation
IDs now use the normalized query and provider page ID, which are stable across
ranking changes. A regression test confirms that reordered results retain the
same citation identity.

## Sanitized receipt

```json
{"activeNavigationAllowed":false,"automaticFollowUpAllowed":false,"contentCharacters":1307,"contentDigest":"e620f22b0f92149c5e234f81a901d62e0065dce2915523315d44b3b79ee71e91","contentPersisted":false,"kind":"haven42-sanitized-live-wikipedia-runtime-validation","modelToolAllowed":false,"pageApprovalSingleUse":true,"pageExecutionAllowed":false,"provider":"fixed-English-Wikipedia","queryApprovalSingleUse":true,"queryDigest":"da5e49a9426e1206fc56890948355b6c5009f5f23ee6b491bc4fe44f257884f9","resultCount":3,"schemaVersion":1,"selectedDisplayDomain":"en.wikipedia.org"}
```

The receipt contains hashes and counts only. It contains no lab address,
hostname, account name, credential, key, or retrieved page text.

## Exact Alpha 2 package result

The same flow then completed through the exact unsigned Windows
`0.4.0-alpha.2` portable candidate with protected-resource integrity
verification enabled. That run returned three citations and 444 characters of
inert text.

```json
{"activeNavigationAllowed":false,"appVersion":"0.4.0-alpha.2","automaticFollowUpAllowed":false,"contentCharacters":444,"contentDigest":"9cc9f3b1b4818ec5b21eeef49e6512f66417aed8e09ec822526b3e0451af29d0","contentPersisted":false,"kind":"haven42-sanitized-packaged-live-wikipedia-validation","modelToolAllowed":false,"packageIntegrityVerified":true,"pageApprovalSingleUse":true,"pageExecutionAllowed":false,"provider":"fixed-English-Wikipedia","queryApprovalSingleUse":true,"queryDigest":"da5e49a9426e1206fc56890948355b6c5009f5f23ee6b491bc4fe44f257884f9","resultCount":3,"schemaVersion":1,"selectedDisplayDomain":"en.wikipedia.org"}
```

## Remaining gates

- Repeat the live validation from native Linux and macOS.
- Complete the documented manual keyboard, screen-reader, zoom, and packaged
  application review before promotion.
