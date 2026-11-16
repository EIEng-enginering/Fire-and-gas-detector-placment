"""Explicit detector orientation convention: azimuth X toward Y, elevation above XY.

A direction is a mounting orientation only; it does not specify field of view.
"""
import math

def direction(azimuth_deg,elevation_deg):
 if any(not math.isfinite(x) for x in (azimuth_deg,elevation_deg)) or not -180<=azimuth_deg<=180 or not -90<=elevation_deg<=90:raise ValueError('Explicit finite azimuth/elevation within supported range required')
 a,e=math.radians(azimuth_deg),math.radians(elevation_deg)
 return (math.cos(e)*math.cos(a),math.cos(e)*math.sin(a),math.sin(e))
