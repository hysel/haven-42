---
name: Performance And Scalability
---

## Scope

Apply these standards to performance-sensitive code, architecture, and reviews.

## Required Practices

- Identify the expected workload, latency target, and bottleneck before optimizing.
- Prefer simple measurement over speculation.
- Watch for repeated database calls, unbounded queries, excessive allocations, synchronous I/O, and lock contention.
- Use pagination or streaming for large result sets.
- Cache only when invalidation, consistency, and failure behavior are understood.
- Keep background work observable and bounded.
- Design retry policies with timeouts, backoff, and circuit-breaking where needed.

## Avoid

- Premature optimization that harms clarity.
- Loading unbounded data into memory.
- Retrying non-idempotent operations blindly.
- Hidden background work with no monitoring.
- Parallelism that overwhelms downstream systems.

## Review Checklist

- What is the measured or likely bottleneck?
- Does the design scale with data size and traffic?
- Are timeouts and resource limits explicit?
