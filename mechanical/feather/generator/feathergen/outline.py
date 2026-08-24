"""G7 — feather_outline: the public entry point.

Composes the geometry engine stages for one feathers.json row:

    compute_rachis → compute_vane (with vane_ratio_adjustment) →
    apply_tip → apply_emargination

Returns ``{"outline": closed vane outline, "rachis": Rachis}`` — the two
artifacts everything downstream consumes (CAD/laser/DXF/SVG outline, and the
rachis polyline + LED bend points).

Floor enforcement: a *lit* feather must keep a vane ≥ ~14 mm (1.4 cm) at the
ribbon (§2 of lighting-and-boards.md). If ``vane_ratio_adjustment`` would
drive a lit feather below ``lit_vane_floor_cm``, the effective width is
clamped to the floor (default) or the call raises (``floor_policy="raise"``).

See backlog-geometry-engine.md task G7.
"""

from __future__ import annotations

from typing import Mapping

from .emargination import apply_emargination
from .rachis import Rachis, compute_rachis
from .tips import apply_tip
from .vane import compute_vane

DEFAULT_LIT_VANE_FLOOR_CM = 1.4


def feather_outline(
    params: Mapping[str, object],
    vane_ratio_adjustment: float = 0.0,
    lit_vane_floor_cm: float = DEFAULT_LIT_VANE_FLOOR_CM,
    floor_policy: str = "clamp",
) -> dict[str, object]:
    """Build the closed vane outline + rachis for one feather.

    ``params`` is a feathers.json row (``total_cm``, ``vane_cm``,
    ``max_width_cm``, ``rachis_split``, ``curvature``, ``tip``,
    ``emargination``, ``lit``, ...). ``vane_ratio_adjustment`` scales every
    max width (0 % = pure §3 ratios).
    """
    rachis = compute_rachis(params)

    max_width = float(params["max_width_cm"])
    effective = max_width * (1.0 + vane_ratio_adjustment)
    lit = bool(params.get("lit", False))

    if floor_policy not in ("clamp", "raise"):
        raise ValueError(f"unknown floor_policy {floor_policy!r}")

    if lit and effective < lit_vane_floor_cm:
        if floor_policy == "raise":
            raise ValueError(
                f"{params.get('id', '?')}: vane_ratio_adjustment "
                f"{vane_ratio_adjustment} drives a lit vane below the "
                f"{lit_vane_floor_cm} cm floor (effective {effective:.2f} cm)"
            )
        # clamp the adjustment so the lit vane lands exactly on the floor
        vane_ratio_adjustment = lit_vane_floor_cm / max_width - 1.0

    vane = compute_vane(
        params,
        rachis,
        vane_ratio_adjustment=vane_ratio_adjustment,
    )
    vane = apply_tip(vane, str(params.get("tip", "pointed")))
    vane = apply_emargination(vane, emargination=bool(params.get("emargination", False)))

    return {"outline": vane.outline, "rachis": rachis}
