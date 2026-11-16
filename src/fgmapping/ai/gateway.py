"""WP10 offline replay gateway. Live AI requests are intentionally unsupported.

Tests use an explicit local replay; this cannot authorise an external transfer.
Only closed-schema evidence-linked text suggestions are accepted; no numbers,
reviews, geometry, plant records or engineering acceptance are written.
"""
from dataclasses import dataclass
from decimal import Decimal
import hashlib,json
from fgmapping.domain.scene import canonical
from fgmapping.engine.scenarios import decimal
@dataclass(frozen=True)
class Preview:
    job_id:str
    provider:str
    endpoint:str
    model:str
    tier:str
    scope:str
    source_revision:str
    source_hash:str
    data_class:str
    outbound_text:str
    estimated_cost:str
    maximum_cost:str
    @property
    def sha256(self):return hashlib.sha256(canonical(self.__dict__).encode()).hexdigest()
@dataclass(frozen=True)
class ReplayConsent:
    preview_sha256:str
    actor:str
    purpose:str='OFFLINE SYNTHETIC REPLAY ONLY'

class OfflineReplayGateway:
    def __init__(self):self.used_jobs=set();self.audit=[]
    def execute(self,preview,consent,response,actual_cost='0',*,live=False):
        if live:raise ValueError('Live AI transport is not implemented or authorised')
        if preview.data_class!='SYNTHETIC':raise ValueError('Only synthetic replay permitted')
        if preview.provider!='OFFLINE_REPLAY' or preview.endpoint!='offline://replay':raise ValueError('No external endpoint is permitted by offline gateway')
        if not all(str(getattr(preview,k)).strip() for k in ('job_id','model','tier','scope','source_revision','source_hash')):raise ValueError('Exact replay model, tier, scope and source identity required')
        if len(preview.source_hash)!=64:raise ValueError('Source SHA256 required')
        if not consent.actor.strip() or consent.preview_sha256!=preview.sha256 or consent.purpose!='OFFLINE SYNTHETIC REPLAY ONLY':raise ValueError('Replay consent does not match exact preview')
        if preview.job_id in self.used_jobs:raise ValueError('Replay job already consumed')
        est=decimal(preview.estimated_cost);maximum=decimal(preview.maximum_cost);actual=decimal(actual_cost)
        if min(est,maximum,actual)<0 or max(est,actual)>maximum:raise ValueError('Replay cost exceeds explicit ceiling')
        # Consume on schema failure too; no hidden retry or provider fallback.
        self.used_jobs.add(preview.job_id)
        if not isinstance(response,dict) or set(response)!={'suggestions'} or not isinstance(response['suggestions'],list) or len(response['suggestions'])>100:raise ValueError('Closed replay response schema required')
        for s in response['suggestions']:
            if not isinstance(s,dict) or set(s)!={'text','source_hash','source_revision','status'}:raise ValueError('Unknown suggestion fields')
            if not isinstance(s['text'],str) or len(s['text'])>4000 or s['status']!='CANDIDATE':raise ValueError('Text-only CANDIDATE suggestions required')
            if s['source_hash']!=preview.source_hash or s['source_revision']!=preview.source_revision:raise ValueError('Suggestion source mismatch')
        self.audit.append({'job_id':preview.job_id,'preview_sha256':preview.sha256,'schema':'PASS','cost':str(actual),'mode':'OFFLINE_REPLAY'})
        return json.loads(canonical(response))
