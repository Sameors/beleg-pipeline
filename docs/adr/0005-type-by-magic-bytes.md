# ADR-0005: Detect file type by magic bytes, not extension

Status: accepted · 2026-11-25

## Context
Renamed and mislabelled files are common (a JPG saved as `.pdf`, HEIC from iPhones).

## Decision
Use the `filetype` library on the file's first bytes. The extension is ignored.

## Consequences
+ Correct routing to the right reader; fewer false rejects.
− One small dependency.
