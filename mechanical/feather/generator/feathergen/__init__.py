"""feathergen — programmatic feather outline drafting.

Tasks: geometry engine (G2-G9) + arrangement engine (A1-A8) per
backlog-geometry-engine.md / backlog-arrangement-engine.md.
"""

from .geometry import (
    Point,
    Polyline,
    bbox,
    distance,
    polyline_length,
    reflect_vertical,
    rotate,
    translate,
)
from .rachis import (
    CURVATURE_BOW_FRACTION,
    DEFAULT_LED_PITCH_CM,
    Rachis,
    compute_rachis,
    max_lateral_offset,
)

__all__ = [
    "CURVATURE_BOW_FRACTION",
    "DEFAULT_LED_PITCH_CM",
    "Point",
    "Polyline",
    "Rachis",
    "bbox",
    "compute_rachis",
    "distance",
    "max_lateral_offset",
    "polyline_length",
    "reflect_vertical",
    "rotate",
    "translate",
]
