-- Candidate only, explicit upgrade with backup. Does not qualify any method.
CREATE TABLE detector_mount (detector_id TEXT PRIMARY KEY REFERENCES detectors(id), component_id TEXT NOT NULL, anchor_local_json TEXT NOT NULL, offset_m_json TEXT NOT NULL, orientation_local_json TEXT NOT NULL, component_fingerprint TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE study_basis (id TEXT PRIMARY KEY CHECK(id='STUDY'), payload_json TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE performance_dataset (id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, import_sha256 TEXT NOT NULL, raw_text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE detector_performance_link (detector_id TEXT PRIMARY KEY REFERENCES detectors(id), dataset_id TEXT NOT NULL REFERENCES performance_dataset(id), evidence_id TEXT NOT NULL REFERENCES evidence(id), status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE preparation_review (id TEXT PRIMARY KEY, subject_kind TEXT NOT NULL, subject_id TEXT NOT NULL, subject_hash TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('DRAFT_REVIEW','NEEDS_INFORMATION','REJECTED')), reviewer TEXT NOT NULL, rationale TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), utc TEXT NOT NULL);
UPDATE case_info SET schema_version=3 WHERE id=1;
PRAGMA user_version=3;
