PRAGMA foreign_keys = ON;
CREATE TABLE case_info (id INTEGER PRIMARY KEY CHECK(id=1), case_uuid TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'DEVELOPMENT BUILD', schema_version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE evidence (id TEXT PRIMARY KEY, kind TEXT NOT NULL, description TEXT NOT NULL, document_revision TEXT NOT NULL, location_ref TEXT NOT NULL, data_class TEXT NOT NULL CHECK(data_class IN ('SYNTHETIC','PROJECT_BASIS')));
CREATE TABLE detectors (id TEXT PRIMARY KEY, detector_type TEXT NOT NULL CHECK(detector_type IN ('FLAME','POINT_GAS','OPEN_PATH','ULTRASONIC')), x REAL NOT NULL, y REAL NOT NULL, z REAL NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), review_status TEXT NOT NULL DEFAULT 'CANDIDATE', CHECK(review_status IN ('CANDIDATE','REVIEWED','REJECTED')));
CREATE TABLE ledger (event_id INTEGER PRIMARY KEY AUTOINCREMENT, utc TEXT NOT NULL, actor TEXT NOT NULL, command TEXT NOT NULL, forward_json TEXT NOT NULL, inverse_json TEXT NOT NULL, is_compensation INTEGER NOT NULL DEFAULT 0);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX detectors_evidence ON detectors(evidence_id);
PRAGMA user_version = 1;
