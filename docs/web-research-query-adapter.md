# Controlled Web Research Query Adapter

The query adapter is a disabled development component. It defines a fixed HTTPS request to the English Wikipedia search API and permits only the reviewed bounded query and result limit to vary. Credentials, cookies, proxy-environment inheritance, redirects, page retrieval, browser automation, model tools, persistence, follow-up searches, UI controls, package admission, and runtime network activation remain disabled.

The implementation currently accepts only an explicitly injected fixture transport. It does not import or bind a native HTTP client and does not make a live request. Strict response validation permits only the expected metadata fields, derives inactive citation destinations from validated numeric page IDs, rejects model-supplied links and active markup, and enforces byte, depth, node, title, result-count, and identifier limits.

A future native transport must independently enforce the system trust store, fixed host and port, no redirects, no environment proxy inheritance, response content type and byte limits, timeout, DNS and resolved-IP revalidation, cancellation, and source/package parity. UI work remains held for explicit visual review.
