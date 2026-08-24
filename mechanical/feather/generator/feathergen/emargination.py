"""G6 — emargination.

Emargination is a notch cut into the **outer** vane near the tip (real outer
primaries, P1-P5). ``apply_emargination`` replaces the outer-rail span near
the tip with a quadratic Bézier whose control point is pulled inward toward
the inner rail, producing a clean V-notch. The inner rail and the rest of the
outline are untouched, so the profile stays a single closed loop.

Notch geometry (knobs): ``span`` = vane fractions (start, end) of the notch,
``depth`` = how far the Bézier control is pulled inward, as a fraction of the
local half-width at the notch's midpoint.

See backlog-geometry-engine.md task G6.
"""

from __future__ import annotations

import math
from dataclasses import replace

from .geometry import Point, distance, sample_bezier
from .vane import Vane

# notch spans from 62 % to 95 % of the vane (near the tip), on the outer rail
DEFAULT_EMARGINATION_SPAN = (0.62, 0.95)
# control pulled inward by 40 % of the local half-width at the notch midpoint
DEFAULT_EMARGINATION_DEPTH = 0.4


def apply_emargination(
    vane: Vane,
    emargination: bool = True,
    span: tuple[float, float] = DEFAULT_EMARGINATION_SPAN,
    depth: float = DEFAULT_EMARGINATION_DEPTH,
    n: int = 12,
) -> Vane:
    """Cut the outer-vane notch; returns a new Vane.

    ``emargination=False`` returns the vane unchanged. ``span`` vane
    fractions must satisfy 0 < start < end < 1; ``depth`` in (0, 1).
    """
    if not emargination:
        return vane
    if not (0.0 < span[0] < span[1] < 1.0):
        raise ValueError(f"span must satisfy 0 < start < end < 1, got {span}")
    if not (0.0 < depth < 1.0):
        raise ValueError(f"depth must be in (0, 1), got {depth}")

    n_rail = len(vane.outer_rail) - 1
    i0 = max(1, round(span[0] * n_rail))
    i1 = min(n_rail - 1, round(span[1] * n_rail))
    if i1 - i0 < 2:
        return vane  # vane too short to notch

    a = vane.outer_rail[i0]
    b = vane.outer_rail[i1]
    im = (i0 + i1) // 2
    outer_m = vane.outer_rail[im]
    inner_m = vane.inner_rail[im]

    # direction from the outer edge toward the inner rail (across the vane)
    dx, dy = inner_m[0] - outer_m[0], inner_m[1] - outer_m[1]
    d = math.hypot(dx, dy)
    if d < 1e-12:
        return vane
    ux, uy = dx / d, dy / d
    half_width = d / 2.0

    ctrl = (
        outer_m[0] + ux * half_width * depth,
        outer_m[1] + uy * half_width * depth,
    )
    notch = sample_bezier([a, ctrl, b], n)

    new_outer = (
        list(vane.outer_rail[: i0 + 1])
        + notch
        + list(vane.outer_rail[i1:])
    )
    outline = new_outer + list(reversed(vane.inner_rail))
    return replace(vane, outline=outline, outer_rail=new_outer)
