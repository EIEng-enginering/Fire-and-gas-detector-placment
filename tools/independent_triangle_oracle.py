"""Independent exact-rational determinant oracle. No production imports.

Cramer's rule solves [end-start, a-b, a-c]*(t,u,v)=a-start.
Constructive non-coplanar fixtures only; Fraction preserves decimal input strings.
"""
from fractions import Fraction as F

def det(m):
    return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
def exact_segment_triangle(start,end,triangle):
    s=tuple(F(str(x)) for x in start);e=tuple(F(str(x)) for x in end)
    a,b,c=[tuple(F(str(x)) for x in p) for p in triangle]
    cols=[tuple(e[i]-s[i] for i in range(3)),tuple(a[i]-b[i] for i in range(3)),tuple(a[i]-c[i] for i in range(3))]
    m=[[cols[j][i] for j in range(3)] for i in range(3)];d=det(m)
    if d==0:raise ValueError('Oracle fixture must be nonparallel')
    rhs=[a[i]-s[i] for i in range(3)];out=[]
    for j in range(3):out.append(det([[rhs[i] if k==j else m[i][k] for k in range(3)] for i in range(3)])/d)
    t,u,v=out
    return 0<=t<=1 and u>=0 and v>=0 and u+v<=1
