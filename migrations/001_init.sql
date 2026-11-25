-- Ingestion stage schema, phase 1 (SQLite).
-- Rule: this database never stores file content, only metadata and events.

CREATE TABLE IF NOT EXISTS source (
    source_id   TEXT PRIMARY KEY,
    channel     TEXT NOT NULL CHECK (channel IN ('folder', 'email', 'upload')),
    address     TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS document (
    doc_id            TEXT PRIMARY KEY,
    sha256            TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    source_id         TEXT NOT NULL REFERENCES source (source_id),
    received_at       TEXT NOT NULL,
    mime_type         TEXT NOT NULL,
    size_bytes        INTEGER NOT NULL,
    page_count        INTEGER,
    stored_path       TEXT,
    status            TEXT NOT NULL
        CHECK (status IN ('received', 'rejected', 'quarantined', 'deleted')),
    error_code        TEXT,
    error_detail      TEXT
);

-- Append-only audit trail. Never UPDATE or DELETE rows here.
CREATE TABLE IF NOT EXISTS ingestion_event (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      TEXT REFERENCES document (doc_id),
    event_type  TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    actor       TEXT NOT NULL,
    details     TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_status ON document (status);
CREATE INDEX IF NOT EXISTS idx_event_doc ON ingestion_event (doc_id);
