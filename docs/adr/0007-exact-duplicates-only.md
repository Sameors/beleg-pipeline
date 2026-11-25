# ADR-0007: Exact duplicates only at ingestion; content duplicates later

Status: accepted · 2026-11-25

## Context
The same invoice scanned twice has a different hash. Recognizing it needs extracted fields.

## Decision
Ingestion detects identical files only. The validate stage checks issuer + amount + date.

## Consequences
+ Ingestion makes no claim it cannot prove.
− Re-scans pass ingestion and are caught one stage later.
