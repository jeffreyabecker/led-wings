"""feathergen — programmatic feather outline drafting.

Tasks: geometry engine (G2-G9) + arrangement engine (A1-A8) per
backlog-geometry-engine.md / backlog-arrangement-engine.md.
"""

from .geometry import (
    Point,
    Polyline,
    bbox,
    distance,
    point_at_arc,
    polyline_length,
    reflect_vertical,
    resample,
    rotate,
    translate,
    unit_tangent_at_arc,
)
from .rachis import (
    CURVATURE_BOW_FRACTION,
    DEFAULT_LED_PITCH_CM,
    Rachis,
    compute_rachis,
    max_lateral_offset,
)
from .vane import Vane, compute_vane, vane_width_at, width_profile

__all__ = [
    "CURVATURE_BOW_FRACTION",
    "DEFAULT_LED_PITCH_CM",
    "Point",
    "Polyline",
    "Rachis",
    "Vane",
    "bbox",
    "compute_rachis",
    "compute_vane",
    "distance",
    "max_lateral_offset",
    "point_at_arc",
    "polyline_length",
    "reflect_vertical",
    "resample",
    "rotate",
    "translate",
    "unit_tangent_at_arc",
    "vane_width_at",
    "width_profile",
]
