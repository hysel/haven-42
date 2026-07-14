---
name: SQL And Database Engineering
optional: true
globs: ["**/*.sql"]
---

## Scope

Use this optional rule pack only when project detection confirms SQL or database migration evidence.

Strong SQL evidence includes `*.sql`, migration folders, schema folders, seed data, database changelog files, ORM migration metadata, or inspected repository docs that describe database ownership.

If SQL evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark database engine, migration tool, schema ownership, and deployment assumptions as `unconfirmed`.

## Required Practices

- Identify the database engine and migration tool from inspected files before recommending syntax, locking behavior, or deployment commands.
- Preserve migration ordering, naming, idempotency style, and rollback strategy used by the repository.
- Treat data changes, destructive DDL, backfills, seed data, permissions, and long-running queries as high-risk operations.
- Prefer additive, reversible, and staged changes when production data may exist.
- Validate constraints, indexes, foreign keys, nullability, defaults, and query plans when the change affects data integrity or performance.
- Keep secrets, connection strings, credentials, and environment-specific endpoints out of committed SQL and docs.
- Match test recommendations to observed database tooling or provide manual validation steps when no harness exists.

## Avoid

- Assuming PostgreSQL, SQL Server, MySQL, SQLite, Oracle, Flyway, Liquibase, EF migrations, Prisma, Alembic, or Rails migrations without evidence.
- Recommending destructive migrations without backup, rollback, and data-validation guidance.
- Adding indexes without considering write impact, selectivity, and existing query patterns.
- Treating generated sample migrations as proof of production database readiness.
- Mixing schema, seed, and data-fix changes without documenting deployment order.

## Review Checklist

- Which files prove this is a SQL or database migration project?
- Which database engine, migration tool, and deployment order are confirmed versus `unconfirmed`?
- Are destructive, locking, data-integrity, and rollback risks called out?
- Are secrets and environment-specific values absent from committed artifacts?
- Do validation steps cover schema correctness, data safety, and performance impact?
