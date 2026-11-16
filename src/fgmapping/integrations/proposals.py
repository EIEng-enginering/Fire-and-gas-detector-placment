"""WP11 closed-schema synthetic P&ID crosswalk, read-only proposal interface.

This parser does not open or write P&ID Reader, Worksheet, SIL, HAZOP or QRA files.
Connectivity never creates physical locations or modifies engineering conclusions.
"""
from fgmapping.domain.scene import canonical,content_hash

def parse_synthetic_pid(payload):
    if not isinstance(payload,dict) or set(payload)!={'schema_version','data_class','source_hash','source_revision','equipment','connections'}:raise ValueError('Closed P&ID proposal contract required')
    if payload['schema_version']!='fg-pid-proposal/1' or payload['data_class']!='SYNTHETIC':raise ValueError('Only v1 synthetic contract supported')
    source=payload['source_hash']
    if not isinstance(source,str) or len(source)!=64 or any(c not in '0123456789abcdef' for c in source) or not payload['source_revision'].strip():raise ValueError('Source hash/revision required')
    eq=payload['equipment'];conn=payload['connections']
    if not isinstance(eq,list) or len(eq)>10000 or not isinstance(conn,list) or len(conn)>20000:raise ValueError('Proposal resource budget exceeded')
    ids=set();proposals=[]
    for e in eq:
        if not isinstance(e,dict) or set(e)!={'tag','class','evidence_locator'}:raise ValueError('P&ID supplies tags/classes only; coordinates and safety conclusions forbidden')
        if any(not isinstance(v,str) or not v.strip() for v in e.values()) or e['tag'] in ids:raise ValueError('Unique tags and evidence locators required')
        ids.add(e['tag']);proposals.append({**e,'position':'NOT SUPPLIED','status':'CANDIDATE','source_hash':source})
    for c in conn:
        if not isinstance(c,dict) or set(c)!={'from','to','evidence_locator'} or c['from'] not in ids or c['to'] not in ids or not c['evidence_locator'].strip():raise ValueError('Connection endpoint or provenance missing')
    return {'contract':'fg-pid-proposal/1','input_hash':content_hash(payload),'status':'CANDIDATE','equipment_proposals':proposals,'connections':conn,'external_writes':False}
