-- Candidate schema; explicit upgrade only. Original migration remains unchanged.
CREATE TABLE geometry_scene (id INTEGER PRIMARY KEY CHECK(id=1), payload_json TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'UNVERIFIED');
CREATE TABLE engineering_record (id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('EQUIPMENT','FIRE_ZONE','GAS_ZONE','TARGET')), payload_json TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), review_status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE calculation_run (id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, method TEXT NOT NULL, result_json TEXT NOT NULL, calculation_status TEXT NOT NULL, qualification_status TEXT NOT NULL DEFAULT 'UNVERIFIED', review_status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TRIGGER ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'Immutable ledger'); END;
CREATE TRIGGER ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'Immutable ledger'); END;
UPDATE case_info SET schema_version=2 WHERE id=1;
PRAGMA user_version=2;
CREATE TABLE geometry_attachment (source_sha256 TEXT PRIMARY KEY, raw_bytes BLOB NOT NULL, format TEXT NOT NULL, frame_json TEXT NOT NULL, manifest_json TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id));
CREATE TABLE detector_details (detector_id TEXT PRIMARY KEY REFERENCES detectors(id), azimuth REAL NOT NULL, elevation REAL NOT NULL, roll REAL NOT NULL, manufacturer TEXT NOT NULL DEFAULT 'NOT SUPPLIED', model TEXT NOT NULL DEFAULT 'NOT SUPPLIED', sensitivity TEXT NOT NULL DEFAULT 'NOT SUPPLIED');
ALTER TABLE calculation_run ADD COLUMN input_json TEXT NOT NULL DEFAULT '{}';
