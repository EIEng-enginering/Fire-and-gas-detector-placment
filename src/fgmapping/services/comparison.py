"""Stable-ID snapshot comparison; never compares different study identities."""
from fgmapping.domain.scene import content_hash,canonical

def compare_snapshots(previous,current):
 for p in (previous,current):
  if p.get('data_class')!='SYNTHETIC' or p.get('snapshot_version') not in ('fg-report/1','fg-report/2'):raise ValueError('Known synthetic snapshot required')
 if previous['case']['case_uuid']!=current['case']['case_uuid']:raise ValueError('Snapshots belong to different cases')
 changes=[]
 for dataset in sorted(set(previous['datasets'])|set(current['datasets'])):
  if dataset=='findings':continue
  def indexed(snapshot):return {str(r.get('id',r.get('detector_id',r.get('source_sha256')))):r for r in snapshot['datasets'].get(dataset,[])}
  before,after=indexed(previous),indexed(current)
  for id in sorted(set(before)|set(after)):
   if id not in before or id not in after:
    changes.append({'id':f'CHANGE-{len(changes)+1:05d}','dataset':dataset,'object_id':id,'kind':'ADDED' if id not in before else 'REMOVED','field':'RECORD','before':before.get(id),'after':after.get(id)});continue
   for field in sorted(set(before[id])|set(after[id])):
    if canonical(before[id].get(field))!=canonical(after[id].get(field)):changes.append({'id':f'CHANGE-{len(changes)+1:05d}','dataset':dataset,'object_id':id,'kind':'CHANGED','field':field,'before':before[id].get(field),'after':after[id].get(field)})
 return {'label':'SYNTHETIC study revision comparison / no engineering acceptance','previous_snapshot_hash':content_hash(previous),'current_snapshot_hash':content_hash(current),'case_uuid':current['case']['case_uuid'],'changes':changes,'qualification':'UNVERIFIED'}


def attach_comparison(snapshot,comparison):
    import json
    if comparison['current_snapshot_hash']!=content_hash(snapshot) or comparison['case_uuid']!=snapshot['case']['case_uuid']:raise ValueError('Comparison is stale or belongs to a different case')
    result=json.loads(canonical(snapshot));result['comparison']=comparison
    rows=[]
    for change in comparison['changes']:
        item=dict(change)
        for key in ('before','after'):
            value=item[key]
            if len(canonical(value))>500:item[key]={'full_value_reference':'comparison/changes/'+item['id']+'/'+key,'sha256':content_hash(value),'summary':'Complete value retained in normalized JSON comparison; not truncated or discarded'}
        rows.append(item)
    result['datasets']['revision_changes']=rows
    return result
