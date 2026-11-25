# ADR-0004: Read stage polls the database in phase 1; queue in phase 2

Status: accepted · 2026-11-25

## Context
A message queue is extra infrastructure that 300 documents a year do not need.

## Decision
The read stage polls for `status = received`. Phase 2 adds a `document.received` message.

## Consequences
+ No broker to run or secure.
− A few seconds of delay; revisit when volume or channels grow.
