# ADR-0003: SQLite first, PostgreSQL later, behind a repository port

Status: accepted · 2026-11-25

## Context
Phase 1 has one user and a few hundred documents a year. Client pilots may need more.

## Decision
Use SQLite (WAL mode) now. All access goes through the `DocumentRepository` port.

## Consequences
+ Zero setup today; a proven path to scale.
− Avoid SQLite-only SQL features so a `PostgresRepository` adapter stays a drop-in.
