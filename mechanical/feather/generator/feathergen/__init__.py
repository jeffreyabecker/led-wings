"""feathergen — programmatic feather outline drafting.

Tasks: geometry engine (G2-G9) + arrangement engine (A1-A8) per
backlog-geometry-engine.md / backlog-arrangement-engine.md.
"""

from .emargination import (
    DEFAULT_EMARGINATION_DEPTH,
    DEFAULT_EMARGINATION_SPAN,
    apply_emargination,
)
from .geometry import (
    Point,
    Polyline,
    bbox,
    distance,
    is_simple_polygon,
    point_at_arc,
    polyline_length,
    reflect_vertical,
    resample,
    rotate,
    segments_intersect,
    translate,
    unit_tangent_at_arc,
)
from .markdown_sync import lint_flight_rows, lint_markdown, main as markdown_sync_main
from .outline import DEFAULT_LIT_VANE_FLOOR_CM, feather_outline
from .rachis import (
    CURVATURE_BOW_FRACTION,
    DEFAULT_LED_PITCH_CM,
    Rachis,
    compute_rachis,
    max_lateral_offset,
)
from .tips import (
    TIP_RADIUS_FRACTION,
    TIP_STYLES,
    apply_tip,
    tip_cap_width,
    tip_radius,
)
from .vane import Vane, compute_vane, vane_width_at, width_profile

__all__ = [
    "CURVATURE_BOW_FRACTION",
    "DEFAULT_EMARGINATION_DEPTH",
    "DEFAULT_EMARGINATION_SPAN",
    "DEFAULT_LED_PITCH_CM",
    "DEFAULT_LIT_VANE_FLOOR_CM",
    "Point",
    "Polyline",
    "Rachis",
    "TIP_RADIUS_FRACTION",
    "TIP_STYLES",
    "Vane",
    "apply_emargination",
    "apply_tip",
    "bbox",
    "compute_rachis",
    "compute_vane",
    "distance",
    "feather_outline",
    "is_simple_polygon",
    "lint_flight_rows",
    "lint_markdown",
    "markdown_sync_main",
    "max_lateral_offset",
    "point_at_arc",
    "polyline_length",
    "reflect_vertical",
    "resample",
    "rotate",
    "segments_intersect",
    "tip_cap_width",
    "tip_radius",
    "translate",
    "unit_tangent_at_arc",
    "vane_width_at",
    "width_profile",
]
