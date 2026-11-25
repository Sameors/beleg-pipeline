# ADR-0006: Quarantine instead of failing the batch

Status: accepted · 2026-11-25

## Context
One broken or encrypted PDF must not stop fifty good ones, and must not disappear either.

## Decision
Store the original, set status `quarantined` with an error code, continue with the next file.

## Consequences
+ Nothing is lost and nothing blocks.
− Someone must review the quarantine list; tracked as a KPI (no item older than 7 days).
