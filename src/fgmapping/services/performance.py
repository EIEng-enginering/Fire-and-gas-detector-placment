"""Immutable-by-ID performance preparation imports and explicit candidate links."""
import json
from fgmapping.domain.performance import parse_dataset,validate_dataset
from fgmapping.domain.scene import canonical,content_hash
from fgmapping.services import workspace as w
from fgmapping.services.study_schema import require_study
from fgmapping.services.case import utc_now
from fgmapping.errors import CaseError

def import_dataset(session,id,raw,actor):
 require_study(session)
 if not id.strip() or w.row(session,'performance_dataset',id):raise CaseError('DATASET_ID','Use a new explicit dataset/revision ID')
 proposal=parse_dataset(raw)
 after={'id':id,'payload_json':canonical(proposal['payload']),'import_sha256':proposal['import_sha256'],'raw_text':proposal['raw_text'],'status':'CANDIDATE'}
 w.execute(session,[w.change(session,'performance_dataset',id,after)],actor,'Import SYNTHETIC performance preparation '+id)
 return proposal

def link_dataset(session,detector_id,dataset_id,evidence_id,actor):
 require_study(session);dataset=w.row(session,'performance_dataset',dataset_id);details=w.row(session,'detector_details',detector_id)
 if w.row(session,'detectors',detector_id) is None or dataset is None:raise CaseError('MISSING','Detector/dataset not found')
 if w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Dataset assignment evidence required')
 payload=validate_dataset(json.loads(dataset['payload_json']))
 if not details or any(details[k]!=payload[k] for k in ('manufacturer','model','sensitivity')):raise CaseError('PERFORMANCE_MISMATCH','Detector manufacturer/model/sensitivity must exactly match the preparation dataset')
 after={'detector_id':detector_id,'dataset_id':dataset_id,'evidence_id':evidence_id,'status':'CANDIDATE'}
 w.execute(session,[w.change(session,'detector_performance_link',detector_id,after)],actor,'Link preparation dataset only / NOT coverage '+detector_id)

def review_draft(session,id,kind,subject_id,decision,reviewer,rationale,evidence_id):
 require_study(session)
 table={'PERFORMANCE':'performance_dataset','BASIS':'study_basis','MOUNT':'detector_mount'}.get(kind)
 if table is None or decision not in ('DRAFT_REVIEW','NEEDS_INFORMATION','REJECTED'):raise CaseError('REVIEW','Only draft preparation review decisions are supported; no approval/promotion')
 subject=w.row(session,table,subject_id)
 if subject is None or w.row(session,'evidence',evidence_id) is None:raise CaseError('MISSING','Review subject or evidence missing')
 if not reviewer.strip() or not rationale.strip() or not id.strip() or w.row(session,'preparation_review',id):raise CaseError('REVIEW','New review ID, named reviewer and rationale required')
 record={'id':id,'subject_kind':kind,'subject_id':subject_id,'subject_hash':content_hash(subject),'decision':decision,'reviewer':reviewer,'rationale':rationale,'evidence_id':evidence_id,'utc':utc_now()}
 # Reviews are append-only evidence; separate from reversible draft entity edits.
 with session.con:
  columns=w.TABLES['preparation_review'];session.con.execute('INSERT INTO preparation_review('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',tuple(record[k] for k in columns))
  session._log(reviewer,'DRAFT_PREPARATION_REVIEW',record,{'retain':'Review evidence is not erased or promoted'})
 session._dirty=True
