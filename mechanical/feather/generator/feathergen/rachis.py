"""G3 — compute_rachis.

The rachis is the feather's central shaft: a polyline of ``total`` length
along the feather axis (local frame: +y from base at origin to tip at
(0, total)), bowed laterally per the feather's ``curvature``. Modelled as a
quadratic Bézier: base (0, 0) → control (bow, total/2) → tip (0, total).

Returns a ``Rachis`` with:
- ``polyline`` — the sampled bowed rachis (base → tip), used by G4's vane.
- ``bend_points`` — points on the rachis at LED pitch (default 1.04 cm ≈
  96 LED/m), the "length + bend points" input the LED segment boards need
  (see lighting-and-boards.md).

Local frame convention: +y along the feather axis (base at origin, tip at
+total); +x is the outer-vane side, so a positive bow leans the tip toward
the leading edge (primaries bow forward).

See backlog-geometry-engine.md task G3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .geometry import Point, Polyline, polyline_length, resample, sample_bezier

# Curvature level -> lateral control-point offset as a fraction of total.
# "high" for outer primaries (P1-P3) → gentle forward bow; "low" ≈ straight
# (coverts); "straight" is the explicit no-bend option. Tuned to the feather
# reference (≈3-5 % bow at high; the old 8 % read as a dramatic banana curve).
CURVATURE_BOW_FRACTION: dict[str, float] = {
    "high": 0.05,
    "med-high": 0.038,
    "med": 0.028,
    "med-low": 0.018,
    "low": 0.008,
    "straight": 0.0,
}

DEFAULT_LED_PITCH_CM = 1.04  # 96 LED/m ≈ 10.4 mm pitch


@dataclass(frozen=True)
class Rachis:
    total: float
    curvature: str
    bow_cm: float  # lateral control-point offset (max lean ≈ bow_cm / 2)
    polyline: Polyline
    bend_points: Polyline

    @property
    def length(self) -> float:
        """Arc length of the bowed rachis polyline."""
        return polyline_length(self.polyline)


def compute_rachis(
    params: Mapping[str, float | str],
    n: int = 64,
    bend_pitch: float = DEFAULT_LED_PITCH_CM,
) -> Rachis:
    """Build the bowed rachis from a feathers.json row (``total_cm`` + ``curvature``).

    ``params`` may be a full feathers.json entry (other keys ignored) or a
    minimal dict with ``total_cm`` and ``curvature``.
    """
    total = float(params["total_cm"])
    curvature = str(params["curvature"])
    if total <= 0:
        raise ValueError(f"total_cm must be > 0, got {total}")
    if curvature not in CURVATURE_BOW_FRACTION:
        raise ValueError(
            f"unknown curvature {curvature!r}; expected one of "
            f"{sorted(CURVATURE_BOW_FRACTION)}"
        )
    if bend_pitch <= 0:
        raise ValueError(f"bend_pitch must be > 0, got {bend_pitch}")

    bow = CURVATURE_BOW_FRACTION[curvature] * total
    control = [(0.0, 0.0), (bow, total / 2.0), (0.0, total)]
    polyline = sample_bezier(control, n)
    bend_points = resample(polyline, bend_pitch)
    return Rachis(total=total, curvature=curvature, bow_cm=bow,
                  polyline=polyline, bend_points=bend_points)


def max_lateral_offset(rachis: Rachis) -> float:
    """Max |x| of the rachis polyline (how far the tip leans from the axis)."""
    return max(abs(x) for x, _ in rachis.polyline)
