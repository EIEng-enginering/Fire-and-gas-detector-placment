"""WP09 exhaustive synthetic layout optioneering benchmark, not engineering solver.

Candidates and incidence are supplied, not derived from qualified detector physics.
Returns proposals only; contains no persistence or baseline mutation.
"""
from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from fgmapping.engine.scenarios import decimal
@dataclass(frozen=True)
class SyntheticMount:
    id:str
    visible_sample_ids:frozenset
    cost:str
    feasible:bool
    maintainable:bool

def enumerate_layouts(mounts,sample_weights,max_detectors,required_votes,base_votes=None):
    """base_votes (Rev G, optional): {sample_id: votes from the fixed existing layout}; default none."""
    mounts=tuple(mounts);base=dict(base_votes or {})
    if any(type(v) is not int or v<0 for v in base.values()) or not set(base)<=set(sample_weights):raise ValueError('Base votes must be nonnegative integers for known sample IDs')
    if len(mounts)>16:raise ValueError('Exhaustive development solver limited to 16 candidates')
    if len({m.id for m in mounts})!=len(mounts) or any(not m.id.strip() for m in mounts):raise ValueError('Unique mount IDs required')
    if type(required_votes) is not int or required_votes<1 or type(max_detectors) is not int or max_detectors<0:raise ValueError('Explicit voting and detector count required')
    weights={id:decimal(w) for id,w in sample_weights.items()}
    if not weights or any(w<=0 for w in weights.values()):raise ValueError('Positive explicit sample weights required')
    for m in mounts:
        if decimal(m.cost)<0 or not m.visible_sample_ids<=weights.keys():raise ValueError('Nonnegative supplied costs and known sample IDs required')
        if type(m.feasible) is not bool or type(m.maintainable) is not bool:raise ValueError('Explicit mount feasibility required')
    valid=sorted((m for m in mounts if m.feasible and m.maintainable),key=lambda m:m.id);answers=[];den=sum(weights.values())
    for n in range(min(max_detectors,len(valid))+1):
        for combo in combinations(valid,n):
            numerator=sum((w for id,w in weights.items() if base.get(id,0)+sum(id in m.visible_sample_ids for m in combo)>=required_votes),Decimal(0))
            answers.append({'mount_ids':[m.id for m in combo],'fraction':numerator/den,'cost':sum((decimal(m.cost) for m in combo),Decimal(0))})
    pareto=[a for a in answers if not any(b['fraction']>=a['fraction'] and b['cost']<=a['cost'] and (b['fraction']>a['fraction'] or b['cost']<a['cost']) for b in answers)]
    return {'status':'CANDIDATE SYNTHETIC PROPOSALS','qualification':'UNVERIFIED','enumerated':len(answers),
            'pareto':[dict(a,fraction=str(a['fraction']),cost=str(a['cost'])) for a in sorted(pareto,key=lambda a:(-a['fraction'],a['cost'],a['mount_ids']))]}
