"""WP09 exhaustive synthetic layout optioneering benchmark, not engineering solver.

Candidates and incidence are supplied, not derived from qualified detector physics.
Returns proposals only; contains no persistence or baseline mutation.
"""
from dataclasses import dataclass
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from itertools import combinations
from fgmapping.engine.scenarios import decimal
@dataclass(frozen=True)
class SyntheticMount:
    id:str
    visible_sample_ids:frozenset
    cost:str
    feasible:bool
    maintainable:bool

DECIMAL_PREC=34  # F23: explicit local context, independent of the caller's decimal context

def pareto_frontier(answers):
    """Non-dominated answers (maximise fraction, minimise cost) by a sorted sweep, O(n log n).
    Equivalent to the pairwise dominance definition: ties in both cost and fraction are all kept."""
    order=sorted(range(len(answers)),key=lambda i:(answers[i]['cost'],-answers[i]['fraction']))
    keep=[];best=None;i=0
    while i<len(order):
        j=i;c=answers[order[i]]['cost']
        while j<len(order) and answers[order[j]]['cost']==c:j+=1
        fm=answers[order[i]]['fraction']
        if best is None or fm>best:
            keep+=[order[k] for k in range(i,j) if answers[order[k]]['fraction']==fm];best=fm
        i=j
    return [answers[k] for k in keep]

def enumerate_layouts(mounts,sample_weights,max_detectors,required_votes,base_votes=None,cancel=None):
    """Exhaustive enumeration (<=16 candidates) with a sorted Pareto frontier.
    base_votes (optional): {sample_id: votes from the fixed existing layout}.
    cancel: optional callable checked inside the enumeration loops (raises RuntimeError('Cancelled'))."""
    with localcontext() as ctx:
        ctx.prec=DECIMAL_PREC;ctx.rounding=ROUND_HALF_EVEN
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
        valid=sorted((m for m in mounts if m.feasible and m.maintainable),key=lambda m:m.id);answers=[];den=sum(weights.values(),Decimal(0))
        ids=sorted(weights);bv=[base.get(i,0) for i in ids];wv=[weights[i] for i in ids]
        inc={m.id:[i in m.visible_sample_ids for i in ids] for m in valid}
        n_done=0
        for n in range(min(max_detectors,len(valid))+1):
            for combo in combinations(valid,n):
                n_done+=1
                if cancel and n_done%64==0 and cancel():raise RuntimeError('Cancelled')
                cols=[inc[m.id] for m in combo];numerator=Decimal(0)
                for k in range(len(ids)):
                    if bv[k]+sum(c[k] for c in cols)>=required_votes:numerator+=wv[k]
                answers.append({'mount_ids':[m.id for m in combo],'fraction':numerator/den,'cost':sum((decimal(m.cost) for m in combo),Decimal(0))})
        if cancel and cancel():raise RuntimeError('Cancelled')
        pareto=pareto_frontier(answers)
        return {'status':'CANDIDATE SYNTHETIC PROPOSALS','qualification':'UNVERIFIED','enumerated':len(answers),'decimal_precision':DECIMAL_PREC,
                'pareto':[dict(a,fraction=str(a['fraction']),cost=str(a['cost'])) for a in sorted(pareto,key=lambda a:(-a['fraction'],a['cost'],a['mount_ids']))]}
