"""G4 — compute_vane.

The vane is the closed barbed outline around the rachis: it spans the top
``vane`` cm of the feather (the bare quill is the lower ``total - vane``),
sweeps out to ``max_width`` at ~40-50 % of the vane length, and tapers to a
point at the tip and to the quill root.

Two rails are built by offsetting the rachis perpendicular to its local
tangent: the **outer rail** takes ``outer`` of the width (rachis split
outer:inner, e.g. P1 30:70 → outer vane 30 %), the **inner rail** takes
``inner``. The closed outline is outer rail base→tip + inner rail tip→base.

Width scaling: effective width = ``max_width × (1 + vane_ratio_adjustment)``
(default 0 % = pure §3 ratios; the flag is applied here, per G4).

Local frame (from G3): +y along the feather axis (base at origin, tip at
+total); +x is the outer-vane side. The rachis bow leans the tip toward +x,
so the "outer" offset is toward +x.

See backlog-geometry-engine.md task G4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .geometry import Point, Polyline, point_at_arc, unit_tangent_at_arc
from .rachis import Rachis


@dataclass(frozen=True)
class Vane:
    outline: Polyline      # closed vane outline
    outer_rail: Polyline   # outer rail, base → tip
    inner_rail: Polyline   # inner rail, base → tip
    effective_max_width: float  # max_width after vane_ratio_adjustment
    quill_cm: float        # bare quill length (total - vane)


def width_profile(s: float, max_width: float, peak_s: float = 0.45) -> float:
    """Vane half-width profile at fraction s of vane length.

    s = 0 at the quill root, s = 1 at the tip. Rises to ``max_width`` at
    ``peak_s`` (~0.45), zero at both ends. Piecewise quadratic so the sweep
    is smooth and the max is exact.
    """
    if s <= 0 or s >= 1:
        return 0.0
    if s <= peak_s:
        return max_width * (s / peak_s) ** 2
    return max_width * ((1.0 - s) / (1.0 - peak_s)) ** 2


def compute_vane(
    params: Mapping[str, object],
    rachis: Rachis,
    n: int = 64,
    vane_ratio_adjustment: float = 0.0,
    peak_s: float = 0.45,
) -> Vane:
    """Build the closed vane outline from a feathers.json row + its rachis.

    ``params`` needs ``vane_cm``, ``max_width_cm``, ``rachis_split``
    (``{"outer": .., "inner": ..}``); other keys are ignored. Width scaling
    via ``vane_ratio_adjustment`` is applied here (default 0 %).
    """
    vane_len = float(params["vane_cm"])
    max_width = float(params["max_width_cm"])
    split = params["rachis_split"]
    outer_frac = split["outer"] / 100.0
    inner_frac = split["inner"] / 100.0

    total = rachis.total
    quill = total - vane_len
    if quill < 0:
        raise ValueError(f"vane_cm {vane_len} exceeds total_cm {total}")
    if max_width <= 0:
        raise ValueError(f"max_width_cm must be > 0, got {max_width}")
    if not (0.0 < peak_s < 1.0):
        raise ValueError(f"peak_s must be in (0, 1), got {peak_s}")

    effective_width = max_width * (1.0 + vane_ratio_adjustment)
    if effective_width <= 0:
        raise ValueError(
            f"vane_ratio_adjustment {vane_ratio_adjustment} drives max width <= 0"
        )

    outer_rail: list[Point] = []
    inner_rail: list[Point] = []
    for i in range(n + 1):
        s = i / n
        arc = quill + s * vane_len
        p = point_at_arc(rachis.polyline, arc)
        tx, ty = unit_tangent_at_arc(rachis.polyline, arc)
        # normal = (ty, -tx) points to the +x (outer) side for a +y rachis
        nx, ny = ty, -tx
        half = width_profile(s, effective_width, peak_s)
        outer = (p[0] + nx * outer_frac * half, p[1] + ny * outer_frac * half)
        inner = (p[0] - nx * inner_frac * half, p[1] - ny * inner_frac * half)
        outer_rail.append(outer)
        inner_rail.append(inner)

    # closed outline: outer base→tip, then inner tip→base
    outline = outer_rail + list(reversed(inner_rail))
    return Vane(
        outline=outline,
        outer_rail=outer_rail,
        inner_rail=inner_rail,
        effective_max_width=effective_width,
        quill_cm=quill,
    )


def vane_width_at(s: float, vane: Vane, n: int = 64) -> float:
    """Distance between the two rails at vane fraction s (for tests/checks)."""
    idx = round(s * n)
    idx = max(0, min(n, idx))
    a = vane.outer_rail[idx]
    b = vane.inner_rail[idx]
    from .geometry import distance

    return distance(a, b)
