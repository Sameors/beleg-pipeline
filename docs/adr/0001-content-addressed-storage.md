# ADR-0001: Store originals content-addressed by SHA-256

Status: accepted · 2026-11-25

## Context
Phone scans reuse file names (`scan001.pdf`). Originals must be provably unchanged for audit.

## Decision
Store each original at `store/<sha[0:2]>/<sha[2:4]>/<sha256>.<ext>`, written once, read-only.

## Consequences
+ No name collisions; integrity is checkable by re-hashing; exact duplicates are free to detect.
− Paths are not human-readable; the UI must show `original_filename` from the database.
