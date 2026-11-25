# Ingestion architecture (summary)

Ingestion accepts every document from every channel, stores the original unchanged and
registers it with a stable ID. It does no OCR, no AI and no business interpretation.

## Business rules

| ID | Rule |
| --- | --- |
| BR-01 | Every accepted document gets exactly one unique document ID. |
| BR-02 | The original file is never changed or overwritten. |
| BR-03 | An identical file is processed only once; repeats are logged, not re-registered. |
| BR-04 | Unsupported formats are rejected with a stated reason. |
| BR-05 | Corrupt or password-protected files go to quarantine and the owner is told. |
| BR-06 | Every document records its channel, original file name and time of receipt. |
| BR-07 | Originals are kept for the agreed retention period, then deleted with a log entry. |

## Components (ports and adapters)

```text
 Channels (adapters)          Core                               Stores (adapters)
 ───────────────────          ────                               ─────────────────
 FolderWatcher  ─┐
 EmailPoller    ─┼──►  IngestionService ──► BlobStore port ──►   LocalBlobStore / Azure Blob
 Upload API     ─┘          │           ──► Repository port ──►  SqliteRepository / Postgres
                            └──────────────► FileInspector port ► filetype + pikepdf + pillow-heif
```

`domain/` and `service/` never import from `adapters/`. Only `cli.py` wires them together.

## Processing sequence

1. Read bytes, check size (> 50 MB: quarantine `too_large`).
2. SHA-256. Known hash: log `DuplicateDetected`, return the existing `doc_id`.
3. Detect type from magic bytes. Unsupported: log `DocumentRejected`.
4. PDFs: check structure. Encrypted or corrupt: store original, quarantine.
5. HEIC: convert. Failure: quarantine `conversion_failed`.
6. Store the original: temp file, atomic rename, read-only.
7. Insert `Document` and `DocumentReceived` event in one transaction.
8. Return `IngestResult`.

## Statuses owned by ingestion

`received` → handed to the read stage · `rejected` → final · `quarantined` → owner acts ·
`deleted` → tombstone after retention.

## Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-01 | No document is ever lost, including on crash (orphan sweep). |
| NFR-02 | Re-running ingestion on the same files changes nothing. |
| NFR-03 | Stored original is byte-identical to the input (`ingest verify`). |
| NFR-04 | Every outcome has an audit event. |
| NFR-05 | < 2 seconds per document, excluding conversion. |
| NFR-08 | A new channel is one adapter; the core does not change. |

Decisions: see [`adr/`](adr/).
