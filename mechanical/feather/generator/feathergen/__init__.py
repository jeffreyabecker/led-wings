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

__all__ = [
    "Point",
    "Polyline",
    "bbox",
    "distance",
    "polyline_length",
    "reflect_vertical",
    "rotate",
    "translate",
]
