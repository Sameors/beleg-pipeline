# ADR-0002: Ingestion does no OCR or AI

Status: accepted · 2026-11-25

## Context
OCR and model calls fail more often than file handling. A failure there must never lose a document.

## Decision
Ingestion only accepts, stores and registers. Reading starts in the next stage.

## Consequences
+ Stages fail independently; ingestion stays simple and reliable.
− One extra hand-off; documents wait briefly with status `received`.
