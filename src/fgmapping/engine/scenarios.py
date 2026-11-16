"""WP08 exact Decimal aggregation of supplied SYNTHETIC scenario outcomes.

Frequency-weighted detection is not risk reduction, availability or SIL credit.
No leak frequencies, response times or consequence values are generated here.
"""
from dataclasses import dataclass
from decimal import Decimal,localcontext

def decimal(value):
    if isinstance(value,float):raise ValueError('Use decimal strings, integers or Decimal; binary float frequency refused')
    x=Decimal(value)
    if not x.is_finite():raise ValueError('Finite Decimal required')
    return x

@dataclass(frozen=True)
class SyntheticScenario:
    id:str
    frequency_per_year:str
    detection_probability:str
    frequency_source:str
    response_source:str
    detection_seconds:str|None=None
    deadline_seconds:str|None=None

def aggregate(rows):
    rows=tuple(rows)
    if not rows or len({r.id for r in rows})!=len(rows):raise ValueError('Nonempty unique scenarios required')
    with localcontext() as ctx:
        ctx.prec=34
        total=Decimal(0);detected=Decimal(0);prob=Decimal(0);timely=Decimal(0);have_time=True
        for r in rows:
            if not r.id.strip() or not r.frequency_source.strip() or not r.response_source.strip():raise ValueError('Scenario IDs and independent input sources required')
            f=decimal(r.frequency_per_year);p=decimal(r.detection_probability)
            if f<0 or not 0<=p<=1:raise ValueError('Nonnegative frequency and probability [0,1] required')
            total+=f;detected+=f*p;prob+=p
            if r.detection_seconds is None or r.deadline_seconds is None:have_time=False
            else:
                t=decimal(r.detection_seconds);deadline=decimal(r.deadline_seconds)
                if t<0 or deadline<0:raise ValueError('Nonnegative times required')
                if t<=deadline:timely+=f*p
        if total==0:raise ValueError('Positive total scenario frequency required')
        return {'metric':'SYNTHETIC scenario detection aggregation','qualification':'UNVERIFIED','frequency_units':'1/year',
                'unweighted_mean_detection_probability':str(prob/len(rows)),
                'frequency_weighted_detection_fraction':str(detected/total),
                'timely_frequency_weighted_detection_fraction':str(timely/total) if have_time else 'NOT SUPPLIED',
                'total_frequency_per_year':str(total),'risk_reduction':'NOT CALCULATED','availability':'NOT CALCULATED'}
