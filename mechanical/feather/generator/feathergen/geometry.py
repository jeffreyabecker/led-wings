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


def point_at_arc(pts: Polyline, target: float) -> Point:
    """Point at arc distance ``target`` along the polyline (clamped to ends).

    ``target <= 0`` returns the first point, ``target >= length`` the last;
    otherwise the point is interpolated along the containing segment.
    """
    if not pts:
        raise ValueError("point_at_arc() of an empty polyline")
    if target <= 0:
        return pts[0]
    total = polyline_length(pts)
    if target >= total:
        return pts[-1]
    walked = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = distance(a, b)
        if walked + seg >= target:
            t = (target - walked) / seg if seg else 0.0
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        walked += seg
    return pts[-1]


def unit_tangent_at_arc(pts: Polyline, target: float) -> Point:
    """Unit tangent of the polyline at arc distance ``target`` (clamped).

    Returns the direction of the segment containing ``target``; falls back to
    (0, 1) for a degenerate (zero-length) polyline.
    """
    if not pts:
        raise ValueError("unit_tangent_at_arc() of an empty polyline")
    if len(pts) < 2:
        return (0.0, 1.0)
    if target <= 0:
        a, b = pts[0], pts[1]
    elif target >= polyline_length(pts):
        a, b = pts[-2], pts[-1]
    else:
        walked = 0.0
        a, b = pts[0], pts[1]
        for x, y in zip(pts, pts[1:]):
            seg = distance(x, y)
            if walked + seg >= target:
                a, b = x, y
                break
            walked += seg
    d = distance(a, b)
    if d == 0:
        return (0.0, 1.0)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _orient(a: Point, b: Point, c: Point) -> int:
    """Cross-product sign of (b-a) x (c-a): +1 CCW, -1 CW, 0 collinear."""
    val = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if abs(val) < 1e-12:
        return 0
    return 1 if val > 0 else -1


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    """True if p lies on segment a-b (inclusive)."""
    return (
        min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12
        and min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12
    )


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    """True if segments a-b and c-d intersect (including touching)."""
    o1, o2 = _orient(a, b, c), _orient(a, b, d)
    o3, o4 = _orient(c, d, a), _orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(a, b, c):
        return True
    if o2 == 0 and _on_segment(a, b, d):
        return True
    if o3 == 0 and _on_segment(c, d, a):
        return True
    if o4 == 0 and _on_segment(c, d, b):
        return True
    return False


def is_simple_polygon(pts: Polyline) -> bool:
    """True if the closed polyline has no self-intersections.

    Zero-length segments (duplicate vertices) are skipped. Adjacent segments
    share their endpoint by construction and are not checked.
    """
    n = len(pts)
    if n < 3:
        return False
    # skip zero-length segments
    segs = [(a, b) for a, b in zip(pts, pts[1:] + pts[:1]) if distance(a, b) > 1e-12]
    m = len(segs)
    for i in range(m):
        a, b = segs[i]
        for j in range(i + 1, m):
            c, d = segs[j]
            if (i + 1) % m == j or (j + 1) % m == i:
                continue  # adjacent segments share an endpoint
            if segments_intersect(a, b, c, d):
                return False
    return True
