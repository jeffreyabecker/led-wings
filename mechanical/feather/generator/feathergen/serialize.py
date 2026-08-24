"""G8 — serializers: DXF (ezdxf) + SVG (stdlib) per feather.

Writes one closed-outline artifact per feather into
``generator/out/{dxf,svg}/``:

- **DXF** via ezdxf — one LWPOLYLINE per feather on the layer named after its
  group (e.g. ``P``, ``S``, ``GC``), R2010 format.
- **SVG** via stdlib — a minimal valid SVG with one closed ``<path>`` per
  feather, viewBox fit to the outline's bbox.

Both read from a ``feather_outline`` result (``{"outline", "rachis"}``).

See backlog-geometry-engine.md task G8.
"""

from __future__ import annotations

import math
import os
from typing import Mapping, Sequence

from .outline import feather_outline

# SVG output is scaled/offset so the feather fits a fixed viewport
SVG_VIEWBOX_SIZE = 200.0
SVG_PAD = 10.0


def _out_dir(base: str, sub: str) -> str:
    d = os.path.join(base, sub)
    os.makedirs(d, exist_ok=True)
    return d


def _bbox(pts: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def write_dxf(
    outline: Sequence[tuple[float, float]],
    layer: str,
    out_dir: str,
    filename: str,
) -> str:
    """Write one closed polyline as DXF R2010; returns the file path."""
    import ezdxf

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    if layer not in doc.layers:
        doc.layers.add(layer)
    msp.add_lwpolyline(list(outline), close=True, dxfattribs={"layer": layer})
    path = os.path.join(_out_dir(out_dir, "dxf"), filename)
    doc.saveas(path)
    return path


def write_svg(
    outline: Sequence[tuple[float, float]],
    out_dir: str,
    filename: str,
    title: str = "",
) -> str:
    """Write one closed outline as an SVG <path>; returns the file path."""
    min_x, min_y, max_x, max_y = _bbox(outline)
    w = max_x - min_x
    h = max_y - min_y
    if w <= 0 or h <= 0:
        raise ValueError(f"degenerate bbox for {filename}: {w}x{h}")

    # scale/translate into the viewBox, preserving aspect ratio
    scale = (SVG_VIEWBOX_SIZE - 2 * SVG_PAD) / max(w, h)
    ox = SVG_PAD - min_x * scale
    oy = SVG_PAD - min_y * scale

    def pt(p: tuple[float, float]) -> str:
        return f"{p[0] * scale + ox:.3f},{p[1] * scale + oy:.3f}"

    d = "M " + pt(outline[0]) + " " + " ".join(f"L {pt(p)}" for p in outline[1:]) + " Z"
    title_el = f"<title>{title}</title>" if title else ""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '
        f"{SVG_VIEWBOX_SIZE} {SVG_VIEWBOX_SIZE}\">{title_el}"
        f'<path d="{d}" fill="none" stroke="black" stroke-width="0.5"/></svg>'
    )
    path = os.path.join(_out_dir(out_dir, "svg"), filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return path


def serialize_feather(
    params: Mapping[str, object],
    out_dir: str,
    vane_ratio_adjustment: float = 0.0,
) -> dict[str, str]:
    """Serialize one feather to DXF + SVG; returns {"dxf": path, "svg": path}."""
    result = feather_outline(params, vane_ratio_adjustment=vane_ratio_adjustment)
    outline = result["outline"]
    fid = str(params["id"])
    layer = str(params["group"])
    dxf = write_dxf(outline, layer, out_dir, f"{fid}.dxf")
    svg = write_svg(outline, out_dir, f"{fid}.svg", title=fid)
    return {"dxf": dxf, "svg": svg}


def serialize_all(
    rows: Sequence[Mapping[str, object]],
    out_dir: str,
    vane_ratio_adjustment: float = 0.0,
) -> dict[str, dict[str, str]]:
    """Serialize every feather; returns {feather_id: {"dxf": ..., "svg": ...}}."""
    return {
        str(r["id"]): serialize_feather(r, out_dir, vane_ratio_adjustment)
        for r in rows
    }
