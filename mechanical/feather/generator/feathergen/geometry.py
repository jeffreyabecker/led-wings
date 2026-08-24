"""G2 — core listable geometry.

Pure-math, dependency-free geometry primitives in cm (no CAD dependency).
Points/polylines are plain tuples ``(x, y)``; unit is cm throughout
(matching ``feathers.json``). The geometry engine builds every feather
outline on top of these primitives.

See backlog-geometry-engine.md task G2.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

# A point is (x, y) in cm. A polyline is a list of points.
Point = Tuple[float, float]
Polyline = Sequence[Point]


def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def polyline_length(pts: Polyline) -> float:
    """Total arc length of a polyline (0 for <2 points)."""
    return sum(distance(a, b) for a, b in zip(pts, pts[1:]))


def bbox(pts: Polyline) -> Tuple[float, float, float, float]:
    """(min_x, min_y, max_x, max_y) of a polyline; raises on empty input."""
    if not pts:
        raise ValueError("bbox() of an empty polyline")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def translate(pts: Polyline, dx: float, dy: float) -> list[Point]:
    """Translate every point by (dx, dy)."""
    return [(x + dx, y + dy) for x, y in pts]


def rotate(pts: Polyline, angle_deg: float, origin: Point = (0.0, 0.0)) -> list[Point]:
    """Rotate every point about ``origin`` by ``angle_deg`` (CCW, degrees)."""
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    ox, oy = origin
    out = []
    for x, y in pts:
        dx, dy = x - ox, y - oy
        out.append((ox + dx * c - dy * s, oy + dx * s + dy * c))
    return out


def reflect_vertical(pts: Polyline, axis_x: float = 0.0) -> list[Point]:
    """Mirror points across the vertical line x = axis_x."""
    return [(2.0 * axis_x - x, y) for x, y in pts]


def sample_bezier(control: Sequence[Point], n: int) -> list[Point]:
    """Sample a quadratic (3 control points) or cubic (4) Bézier into n+1 points.

    n >= 1; returns n+1 points with t in [0, 1] inclusive.
    """
    if len(control) == 3:
        return _sample_quad(control, n)
    if len(control) == 4:
        return _sample_cubic(control, n)
    raise ValueError(f"sample_bezier expects 3 or 4 control points, got {len(control)}")


def _bezier(control: Sequence[Point], t: float) -> Point:
    """De Casteljau evaluation at parameter t in [0, 1] (any degree)."""
    pts = [tuple(p) for p in control]
    while len(pts) > 1:
        pts = [
            ((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1])
            for a, b in zip(pts, pts[1:])
        ]
    return pts[0]


def _sample_quad(control: Sequence[Point], n: int) -> list[Point]:
    return [_bezier(control, i / n) for i in range(n + 1)]


def _sample_cubic(control: Sequence[Point], n: int) -> list[Point]:
    return [_bezier(control, i / n) for i in range(n + 1)]


def resample(pts: Polyline, spacing: float) -> list[Point]:
    """Resample a polyline to evenly spaced points (spacing in cm).

    Emits points at arc distances 0, spacing, 2*spacing, ... from the start,
    then appends the final point if it wasn't already placed. The first point
    is always kept.
    """
    if spacing <= 0:
        raise ValueError(f"spacing must be > 0, got {spacing}")
    if len(pts) < 2:
        return list(pts)

    out = [pts[0]]
    arc = 0.0          # arc distance from pts[0] to current segment start
    next_emit = spacing

    for a, b in zip(pts, pts[1:]):
        seg = distance(a, b)
        seg_end = arc + seg
        while next_emit <= seg_end + 1e-12:
            t = (next_emit - arc) / seg if seg else 0.0
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            next_emit += spacing
        arc = seg_end

    if distance(out[-1], pts[-1]) > 1e-9:
        out.append(pts[-1])
    return out
