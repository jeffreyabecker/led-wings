"""G5 — tip styles.

Tip profile tweaks applied to a ``Vane``'s closed outline. ``pointed`` keeps
the sharp taper (width → 0 at the tip); the rounded family replaces the tip
with a semicircular cap of radius ``TIP_RADIUS_FRACTION × effective_max_width``
(wider radius = blunter tip); ``hooked`` replaces it with a quadratic Bézier
that curls toward the outer vane.

Mechanically: trim both rails back to the vane fraction where the local
vane width equals the cap diameter (2 × radius), then cap with a semicircle
on that chord, bulging toward the original tip. The cap fits the vane width
seamlessly and stays simple (no self-intersection).

See backlog-geometry-engine.md task G5.
"""

from __future__ import annotations

import math
from dataclasses import replace

from .geometry import Point, Polyline, distance, sample_bezier
from .vane import Vane

TIP_STYLES = ("pointed", "hooked", "rounded-point", "rounded", "very-rounded")

# cap radius as a fraction of the effective max width
TIP_RADIUS_FRACTION: dict[str, float] = {
    "pointed": 0.0,
    "rounded-point": 0.04,
    "rounded": 0.08,
    "very-rounded": 0.12,
    "hooked": 0.05,
}

# hooked tip: displacement of the Bézier control as multiples of the cap
# radius — outward (toward the outer vane) and along the tip direction
HOOK_X_FRACTION = 0.45
HOOK_Y_FRACTION = 0.8

DEFAULT_PEAK_S = 0.45


def tip_radius(vane: Vane, tip: str) -> float:
    """Cap radius for a tip style on this vane (0 for pointed)."""
    return TIP_RADIUS_FRACTION[tip] * vane.effective_max_width


def _width_at(s: float, max_width: float, peak_s: float) -> float:
    """Mirror of vane.width_profile (fall branch only matters here)."""
    if s <= 0 or s >= 1:
        return 0.0
    if s <= peak_s:
        return max_width * (s / peak_s) ** 2
    return max_width * ((1.0 - s) / (1.0 - peak_s)) ** 2


def _trim_fraction(max_width: float, radius: float, peak_s: float) -> float:
    """Vane fraction s where width(s) == 2*radius (on the fall branch)."""
    if radius <= 0:
        return 1.0
    frac = (1.0 - peak_s) * math.sqrt(2.0 * radius / max_width)
    s = 1.0 - frac
    return min(max(s, peak_s + 1e-3), 1.0)


def _semicircle_cap(a: Point, b: Point, bulge: Point, n: int) -> list[Point]:
    """Semicircular arc from a to b (diameter a-b), bulging toward ``bulge``.

    t=0 lands on ``a`` and t=pi on ``b`` so the arc can be spliced after a
    rail ending at ``a``.
    """
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    r = distance(a, b) / 2.0
    if r <= 1e-12:
        return [a]
    ux, uy = (a[0] - mx) / r, (a[1] - my) / r  # chord direction a -> b
    vx, vy = -uy, ux  # perpendicular to chord
    if vx * bulge[0] + vy * bulge[1] < 0:
        vx, vy = uy, -ux  # flip toward the bulge direction
    pts = []
    for i in range(n + 1):
        t = math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        pts.append((mx + r * (c * ux + s * vx), my + r * (c * uy + s * vy)))
    return pts


def _unit(p: Point) -> Point:
    d = math.hypot(p[0], p[1])
    if d == 0:
        return (0.0, 1.0)
    return (p[0] / d, p[1] / d)


def apply_tip(vane: Vane, tip: str, n: int = 16) -> Vane:
    """Apply a tip style to the vane; returns a new Vane with the new outline.

    ``tip="pointed"`` (or radius 0) returns the vane unchanged.
    """
    if tip not in TIP_STYLES:
        raise ValueError(
            f"unknown tip {tip!r}; expected one of {sorted(TIP_STYLES)}"
        )
    radius = tip_radius(vane, tip)
    if radius <= 0:
        return vane

    max_width = vane.effective_max_width
    s_cut = _trim_fraction(max_width, radius, DEFAULT_PEAK_S)
    i_cut = round(s_cut * (len(vane.outer_rail) - 1))
    i_cut = max(1, min(len(vane.outer_rail) - 1, i_cut))

    a = vane.outer_rail[i_cut]
    b = vane.inner_rail[i_cut]
    tip_pt = vane.outer_rail[-1]  # original tip (both rails meet there)
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    bulge = _unit((tip_pt[0] - mx, tip_pt[1] - my))

    if tip == "hooked":
        outward = _unit((a[0] - mx, a[1] - my))  # toward the outer vane
        ctrl = (
            mx + HOOK_X_FRACTION * radius * outward[0] + HOOK_Y_FRACTION * radius * bulge[0],
            my + HOOK_X_FRACTION * radius * outward[1] + HOOK_Y_FRACTION * radius * bulge[1],
        )
        cap = sample_bezier([a, ctrl, b], n)
    else:
        cap = _semicircle_cap(a, b, bulge, n)

    outline = (
        list(vane.outer_rail[: i_cut + 1])
        + cap
        + list(reversed(vane.inner_rail[: i_cut + 1]))
    )
    return replace(vane, outline=outline)


def tip_cap_width(vane: Vane, vane_cm: float, top_frac: float = 0.05) -> float:
    """Max x-extent of the outline in the top ``top_frac`` of the vane.

    For rounded/hooked tips this is dominated by the cap's diameter
    (≈ 2 × radius), so a larger value = blunter tip; for pointed it is the
    (small) width of the taper near the tip.
    """
    ys = [p[1] for p in vane.outline]
    top = max(ys)
    cutoff = top - top_frac * vane_cm
    pts = [p for p in vane.outline if p[1] >= cutoff]
    xs = [p[0] for p in pts]
    return max(xs) - min(xs) if xs else 0.0
