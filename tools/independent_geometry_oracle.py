"""Independent small reference oracle; intentionally does not import engine.

Analytic truth for an axis-aligned segment vs a box, plus simple cone threshold.
This tests the PROTOTYPE geometry behaviour only, not detector physics.
"""
from math import acos, degrees, sqrt

def independent_segment_box_intersection(start, finish, minimum, maximum):
    # Distinct method: clip parametric segment using six half-space inequalities.
    lo,hi=0.,1.
    for k in (0,1,2):
        step=finish[k]-start[k]
        for sign,bound in ((-1.,minimum[k]),(1.,maximum[k])):
            a=sign*step; rhs=sign*(bound-start[k])
            if abs(a)<1e-14:
                if rhs<0:return False
            elif a>0:hi=min(hi,rhs/a)
            else:lo=max(lo,rhs/a)
            if lo>hi:return False
    return True

def independent_cone_check(start,direction,point,maximum_distance,half_angle):
    v=[point[k]-start[k] for k in (0,1,2)]
    d=sqrt(sum(x*x for x in v))
    direction_length=sqrt(sum(x*x for x in direction))
    if d==0 or d>maximum_distance:return False
    value=sum(v[k]*direction[k] for k in (0,1,2))/(d*direction_length)
    angle=degrees(acos(max(-1.,min(1.,value))))
    return angle <= half_angle+1e-9
