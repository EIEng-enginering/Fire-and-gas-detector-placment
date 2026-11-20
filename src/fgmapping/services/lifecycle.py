"""Rev H (F12) result lifecycle: COMPUTED - UNREVIEWED -> ENGINEER REVIEWED -> INDEPENDENTLY
VERIFIED, from immutable ledger review records bound to the run input hash and result hash.
Kept separate from services.coverage so that zone-method fingerprints do not depend on study code."""
from __future__ import annotations
import hashlib,json
from fgmapping.errors import CaseError
from fgmapping.services import coverage as cov
from fgmapping.services import workspace as w
from fgmapping.services.case import utc_now

# ---------------- result lifecycle (F12) ----------------
def result_hash(run):return hashlib.sha256(run['result_json'].encode('utf8')).hexdigest()

def _review_events(session,run_id):
    out=[]
    for utc,actor,cmd,fwd in session.con.execute("SELECT utc,actor,command,forward_json FROM ledger WHERE command IN ('REVIEW_COVERAGE_RUN','VERIFY_COVERAGE_RUN') ORDER BY event_id"):
        f=json.loads(fwd)
        if f.get('run_id')==run_id:out.append(dict(f,command=cmd,ledger_utc=utc,ledger_actor=actor))
    return out

def record_review(session,run_id,reviewer,disposition,comment,actor,independent=False,evidence_id=None):
    """Append an immutable engineer review (or independent verification) record bound to the
    run's input hash and result hash. Any later change to either invalidates it."""
    run=next((r for r in cov.runs(session)+_study_rows(session) if r['id']==run_id),None)
    if run is None:raise CaseError('MISSING','Run not found')
    if not str(reviewer).strip():raise CaseError('REVIEWER','Named reviewer required')
    if disposition not in ('ACCEPTED','ACCEPTED WITH COMMENTS','REJECTED'):raise CaseError('DISPOSITION','Disposition ACCEPTED / ACCEPTED WITH COMMENTS / REJECTED required')
    cur=run_state(session,run)
    if cur['currency']!='CURRENT':raise CaseError('STALE','Stale runs cannot be reviewed; recompute first')
    if independent:
        if cur['lifecycle']!='ENGINEER REVIEWED':raise CaseError('ORDER','Independent verification requires a current engineer review')
        if any(e['reviewer'].strip().lower()==reviewer.strip().lower() for e in _review_events(session,run_id) if e['command']=='REVIEW_COVERAGE_RUN'):raise CaseError('INDEPENDENCE','Verifier must differ from the engineer reviewer')
        if not evidence_id or w.row(session,'evidence',evidence_id) is None:raise CaseError('EVIDENCE','Independent verification needs a registered evidence record')
    rec={'run_id':run_id,'reviewer':reviewer,'disposition':disposition,'comment':str(comment),'input_hash':run['input_hash'],'result_sha256':result_hash(run),'evidence_id':evidence_id,'utc':utc_now()}
    with session.con:session._log(actor,'VERIFY_COVERAGE_RUN' if independent else 'REVIEW_COVERAGE_RUN',rec,{'retain':'review records are immutable; a superseding review is a new record'})
    session._dirty=True
    return rec

def _study_rows(session):
    from fgmapping.services.scenario_coverage import study_runs
    return study_runs(session)

def run_state(session,run):
    """Lifecycle: COMPUTED - UNREVIEWED -> ENGINEER REVIEWED (current accepted review bound to
    input+result hash) -> INDEPENDENTLY VERIFIED (separate verifier, evidence). A review whose
    hashes no longer match, or a stale run, gives REVIEW INVALIDATED."""
    if run['method'] in ('SCENARIO_COVERAGE','LAYOUT_OPTIONS'):
        from fgmapping.services.scenario_coverage import study_run_currency
        currency=study_run_currency(session,run)
    else:currency=cov.run_currency(session,run)
    ev=_review_events(session,run['id']);rh=result_hash(run)
    valid=[e for e in ev if e['input_hash']==run['input_hash'] and e['result_sha256']==rh]
    state=cov.LIFECYCLE[0];review=None;verify=None
    if ev and (currency!='CURRENT' or not valid):state=cov.LIFECYCLE[3]
    else:
        rv=[e for e in valid if e['command']=='REVIEW_COVERAGE_RUN']
        if rv and rv[-1]['disposition']!='REJECTED':
            state=cov.LIFECYCLE[1];review=rv[-1]
            vf=[e for e in valid if e['command']=='VERIFY_COVERAGE_RUN' and e['disposition']!='REJECTED']
            if vf:state=cov.LIFECYCLE[2];verify=vf[-1]
        elif rv:state='REVIEW REJECTED';review=rv[-1]
    return {'currency':currency,'lifecycle':state,'review':review,'verification':verify,'label':state+(' | STALE' if currency!='CURRENT' else '')+' | development software - not independently verified' if state!=cov.LIFECYCLE[2] else state}
