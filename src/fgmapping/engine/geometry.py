"""Pure, deterministic geometry teaching/prototype engine, NOT a F&G coverage model.

This code demonstrates 3D point visibility and a simplistic angular/range threshold.
It deliberately excludes fire-size-dependent response, detector specifications,
attenuation, gas dispersion, target area, uncertainty and engineering qualification.
No safety decision may be based on these outputs.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import cos, radians, sqrt, isfinite
from typing import Iterable

Vec3 = tuple[float, float, float]

@dataclass(frozen=True)
class Box:
    low: Vec3
    high: Vec3
    def __post_init__(self):
        if any(not isfinite(v) for v in (*self.low, *self.high)):
            raise ValueError('Coordinates must be finite')
        if any(lo >= hi for lo, hi in zip(self.low, self.high)):
            raise ValueError('Box limits must be strictly ordered')

@dataclass(frozen=True)
class DemoDetector:
    tag: str
    position: Vec3
    direction: Vec3
    max_distance: float
    half_angle_deg: float
    def __post_init__(self):
        if not self.tag.strip() or not 0 < self.max_distance < float('inf') or not 0 <= self.half_angle_deg <= 90:
            raise ValueError('Invalid illustrative detector parameters')
        if any(not isfinite(v) for v in (*self.position, *self.direction)) or norm(self.direction) == 0:
            raise ValueError('Invalid illustrative detector geometry')

def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def dot(a: Vec3, b: Vec3) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def norm(a: Vec3) -> float:
    return sqrt(dot(a,a))

def line_hits_box(a: Vec3, b: Vec3, box: Box, eps: float=1e-12) -> bool:
    """Return whether closed segment a->b intersects the closed AABB.

    Contact at an edge counts as blocked; start/end on an obstacle counts blocked.
    This is a prototype modelling convention and an explicit owner decision.
    """
    if any(not isfinite(v) for v in (*a,*b)):
        raise ValueError('Coordinates must be finite')
    if not (isfinite(eps) and eps > 0):
        raise ValueError('eps must be positive and finite')
    d = sub(b,a)
    near, far = 0.0,1.0
    for k in range(3):
        if abs(d[k]) < eps:
            if a[k] < box.low[k] or a[k] > box.high[k]:
                return False
            continue
        lo=(box.low[k]-a[k])/d[k]; hi=(box.high[k]-a[k])/d[k]
        if lo > hi: lo,hi=hi,lo
        near=max(near,lo); far=min(far,hi)
        if near>far: return False
    return True

def illustrative_point_visible(detector: DemoDetector, target: Vec3, obstacles: Iterable[Box]) -> bool:
    """Educational binary geometry only; NOT a genuine fire detector response model."""
    if any(not isfinite(v) for v in target):
        raise ValueError('Target coordinates must be finite')
    vec = sub(target, detector.position)
    dist=norm(vec)
    if dist <= 1e-12 or dist > detector.max_distance:
        return False
    u = dot(vec,detector.direction)/(dist*norm(detector.direction))
    if u < cos(radians(detector.half_angle_deg)) - 1e-12:
        return False
    return not any(line_hits_box(detector.position,target,b) for b in obstacles)

def illustrative_vote_count(detectors: Iterable[DemoDetector], target: Vec3, obstacles: Iterable[Box]) -> int:
    boxes=tuple(obstacles)
    return sum(illustrative_point_visible(d,target,boxes) for d in detectors)

def illustrative_coverage(detectors: Iterable[DemoDetector], samples: Iterable[tuple[Vec3,float]], obstacles: Iterable[Box], required_votes: int) -> float:
    """Synthetic weighted fraction only, not geographic F&G coverage."""
    if not isinstance(required_votes,int) or required_votes<1:
        raise ValueError('required_votes must be a positive integer')
    dets=tuple(detectors); boxes=tuple(obstacles)
    points=tuple(samples)
    if not points or any(w<=0 or not isfinite(w) for _,w in points):
        raise ValueError('Samples require finite positive weights')
    return sum(w for p,w in points if illustrative_vote_count(dets,p,boxes)>=required_votes)/sum(w for _,w in points)
