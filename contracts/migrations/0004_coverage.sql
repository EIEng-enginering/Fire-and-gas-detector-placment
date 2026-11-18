-- Rev G coverage schema (owner-approved 18 Nov 2026). Explicit upgrade with backup.
-- Engineer-reviewed results only; not independent certification.
CREATE TABLE detector_library (id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, content_sha256 TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE detector_library_assignment (detector_id TEXT PRIMARY KEY REFERENCES detectors(id), library_id TEXT NOT NULL REFERENCES detector_library(id), receiver_json TEXT NOT NULL DEFAULT 'null', evidence_id TEXT NOT NULL REFERENCES evidence(id), status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE coverage_setup (zone_id TEXT PRIMARY KEY REFERENCES engineering_record(id), payload_json TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id), status TEXT NOT NULL DEFAULT 'CANDIDATE');
CREATE TABLE coverage_run (id TEXT PRIMARY KEY, kind TEXT NOT NULL, zone_id TEXT NOT NULL, method TEXT NOT NULL, method_version TEXT NOT NULL, input_hash TEXT NOT NULL, input_json TEXT NOT NULL, result_json TEXT NOT NULL, samples_json TEXT NOT NULL, actor TEXT NOT NULL, utc TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CURRENT', label TEXT NOT NULL DEFAULT 'Engineer-reviewed results - not independently certified');
UPDATE case_info SET schema_version=4 WHERE id=1;
PRAGMA user_version=4;
