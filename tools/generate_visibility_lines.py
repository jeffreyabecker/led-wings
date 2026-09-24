"""Generate per-feather "visibility lines" from the aggregate feather SVG.

Source of truth (read-only):

    mechanical/templates/feathers-aggregate-min.svg

For every feather this computes how much of it is actually visible when the wing
is assembled: feathers overlap, so a feather's base is covered by the feathers
stacked in front of it. The script draws the boundary between the *visible* part
and the *hidden* part of each feather -- its "visibility line" -- as paths inside
the feather outline. That is exactly the line a lighting design needs ("stop
putting LEDs past here").

How it works
------------
1. Parse the SVG and flatten every feather outline to an absolute (mm) polygon,
   composing the nested ``matrix``/``rotate``/``scale`` transforms. The heavy
   lifting (path parsing, transforms, bezier flattening) is reused from
   ``make_feather_template_pdf_from_aggregate``.
2. Order the feathers front-to-back:
   * families in ``FRONT_TO_BACK_FAMILIES`` (front first);
   * within a family, "leading edge first" (top-most feather is on top -- the
     shingling direction of a real wing row), i.e. sorted by min-Y then min-X.
   A full explicit order can be supplied with ``--order-file``.
3. Rasterize the whole wing onto one grid (``--res`` mm/pixel) with one binary
   mask per feather.
4. Walk the feathers front-to-back keeping a running union of the masks in
   front; a feather's visible region is ``own_mask AND NOT front_union``.
5. Trace the visible/hidden interface *inside* each feather (the unit edges
   separating a visible pixel from a hidden one, chained into polylines,
   Douglas-Peucker simplified), which are the visibility lines.
6. Emit a new SVG (outline references + one red polyline per feather + labels),
   a JSON report of visible area per feather, and optionally a PNG preview.

Outputs (written beside the source unless overridden):
    mechanical/templates/feathers-visibility-lines.svg
    mechanical/templates/feathers-visibility-report.json
    mechanical/templates/feathers-visibility-preview.png   (with --preview)

Usage:
    python tools/generate_visibility_lines.py
    python tools/generate_visibility_lines.py --res 0.5 --preview
    python tools/generate_visibility_lines.py --order-file order.txt
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import make_feather_template_pdf_from_aggregate as svg_util  # noqa: E402

SVG_NS = svg_util.SVG_NS
_local = svg_util._local

TEMPLATES_DIR = REPO_ROOT / "mechanical" / "templates"
DEFAULT_SRC = TEMPLATES_DIR / "feathers-aggregate-min.svg"
DEFAULT_OUT = TEMPLATES_DIR / "feathers-visibility-lines.svg"
DEFAULT_REPORT = TEMPLATES_DIR / "feathers-visibility-report.json"
DEFAULT_PREVIEW = TEMPLATES_DIR / "feathers-visibility-preview.png"

DEFAULT_RES_MM = 0.25          # mm per pixel

# ---------------------------------------------------------------------------
# Stacking. Front = drawn on top = what you see first.
# ---------------------------------------------------------------------------
# Authoritative group order, bottom to top: B sits at the back, LC at the front.
# Front-to-back is the reverse. Within a group, a higher feather number covers a
# lower one (so a higher number is nearer the front).
FAMILY_ORDER_BOTTOM_TO_TOP = ["B", "P", "PC", "A", "S", "SC", "MC", "LC"]
FRONT_TO_BACK_FAMILIES = list(reversed(FAMILY_ORDER_BOTTOM_TO_TOP))

# Family palette, reused from the aggregate's stylesheet (for the preview).
FAMILY_COLORS = {
    "P":  "#1f77b4", "S": "#ff7f0e", "A": "#2ca02c", "PC": "#d62728",
    "SC": "#9467bd", "MC": "#17becf", "LC": "#bcbd22", "B": "#8c564b",
}


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def _poly_bounds(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def _poly_area_mm2(polys):
    """Signed area of the largest polyline (feathers are simple closed loops)."""
    largest = max(polys, key=len)
    if len(largest) < 3:
        return 0.0
    xs = np.asarray([p[0] for p in largest])
    ys = np.asarray([p[1] for p in largest])
    # shoelace
    return abs(0.5 * float(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys)))


def mat_inv(m):
    """Inverse of an affine (a, b, c, d, e, f); raises on a singular matrix."""
    a, b, c, d, e, f = m
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError("cannot invert a singular matrix")
    return (d / det, -b / det, -c / det, a / det,
            (c * f - d * e) / det, (b * e - a * f) / det)


def douglas_peucker(pts, tol):
    """Simplify a polyline (Nx2) so no point deviates from the line by > tol."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 3:
        return pts

    def perp_dist(a, b, points):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        denom = math_hypot(dx, dy)
        if denom == 0:
            return np.hypot(points[:, 0] - ax, points[:, 1] - ay)
        return np.abs(dx * (points[:, 1] - ay) - dy * (points[:, 0] - ax)) / denom

    def recurse(segment):
        start, end = segment[0], segment[-1]
        dist = perp_dist(start, end, segment)
        i = int(np.argmax(dist))
        if dist[i] <= tol:
            return np.array([start, end])
        left = recurse(segment[: i + 1])
        right = recurse(segment[i:])
        return np.vstack([left[:-1], right])

    return recurse(pts)


def math_hypot(x, y):
    return (x * x + y * y) ** 0.5


# ---------------------------------------------------------------------------
# SVG reading
# ---------------------------------------------------------------------------

@dataclass
class Feather:
    id: str
    family: str
    polys: list            # absolute mm polylines (lists of (x, y))
    mask: np.ndarray = None
    visible: np.ndarray = None
    hidden: np.ndarray = None
    lines_mm: list = None  # visibility lines, mm polylines
    group_matrix: tuple = None  # composed transform of the feather's own group
    visible_frac: float = 0.0
    area_mm2: float = 0.0
    visible_area_mm2: float = 0.0


def load_feathers(src: Path) -> list[Feather]:
    tree = ET.parse(src)
    root = tree.getroot()
    parents = svg_util._matrix_chain(root)
    feathers: list[Feather] = []
    seen = set()
    for fg in root.iter(f"{{{SVG_NS}}}g"):
        cls = (fg.get("class") or "").strip()
        if not cls.startswith("group"):
            continue
        fid = (fg.get("id") or "").strip()
        if not fid or fid in seen:
            continue
        seen.add(fid)
        family = cls.split()[1] if " " in cls else ""
        outline_el = None
        for el in fg:
            if _local(el.tag) == "path" and (el.get("id") or "").endswith("-outline"):
                outline_el = el
                break
        if outline_el is None:
            continue
        m = svg_util.element_matrix(outline_el, parents)
        m_group = svg_util.element_matrix(fg, parents)
        sp = svg_util.parse_path(outline_el.get("d") or "")
        sp = svg_util.transform_path(sp, m)
        polys = svg_util.flatten_path(sp, tol=0.05)
        polys = [list(poly) for poly in polys if len(poly) >= 3]
        if not polys:
            continue
        feathers.append(Feather(id=fid, family=family, polys=polys,
                                group_matrix=m_group,
                                area_mm2=_poly_area_mm2(polys)))
    return feathers


# ---------------------------------------------------------------------------
# ordering
# ---------------------------------------------------------------------------

def _feather_index(fid: str) -> int:
    """Trailing integer of a feather id (P3 -> 3); 0 when there is none."""
    m = re.search(r"(\d+)\s*$", fid)
    return int(m.group(1)) if m else 0


def default_order(feathers: list[Feather]) -> list[Feather]:
    """Front-to-back order: family order, then higher number first within family."""
    by_family: dict[str, list[Feather]] = {}
    for f in feathers:
        by_family.setdefault(f.family, []).append(f)

    ordered: list[Feather] = []
    for fam in FRONT_TO_BACK_FAMILIES:
        if fam not in by_family:
            continue
        fam_feathers = by_family.pop(fam)
        # higher number covers lower number -> higher number nearer the front
        fam_feathers.sort(key=lambda f: _feather_index(f.id), reverse=True)
        ordered.extend(fam_feathers)
    # any family not named in the constant goes behind everything
    for fam, leftover in by_family.items():
        leftover.sort(key=lambda f: _feather_index(f.id), reverse=True)
        ordered.extend(leftover)
    return ordered


def order_from_file(feathers: list[Feather], path: Path) -> list[Feather]:
    ids = [ln.strip() for ln in path.read_text().splitlines()
           if ln.strip() and not ln.strip().startswith("#")]
    by_id = {f.id: f for f in feathers}
    ordered = [by_id[i] for i in ids if i in by_id]
    missing = [i for i in ids if i not in by_id]
    if missing:
        print(f"warning: --order-file names unknown feathers {missing}", file=sys.stderr)
    unlisted = [f for f in feathers if f.id not in ids]
    if unlisted:
        print(f"warning: {[f.id for f in unlisted]} not in order file -> placed behind",
              file=sys.stderr)
    return ordered + unlisted


# ---------------------------------------------------------------------------
# rasterisation
# ---------------------------------------------------------------------------

def rasterize(feathers: list[Feather], res: float) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Fill one binary mask per feather on a shared grid.

    Returns (x0, y0) in mm and the grid shape; stores each feather's mask.
    """
    xs = [p[0] for f in feathers for poly in f.polys for p in poly]
    ys = [p[1] for f in feathers for poly in f.polys for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w = int(math.ceil((x1 - x0) / res)) + 2
    h = int(math.ceil((y1 - y0) / res)) + 2

    def to_px(poly):
        return [(int(round((x - x0) / res)), int(round((y - y0) / res)))
                for (x, y) in poly]

    for f in feathers:
        img = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(img)
        # largest polyline is the outer boundary; any smaller ones are holes.
        polys = sorted(f.polys, key=len, reverse=True)
        for i, poly in enumerate(polys):
            d.polygon(to_px(poly), fill=(0 if i else 1))
        f.mask = np.asarray(img, dtype=bool)
    return x0, y0, w, h


# ---------------------------------------------------------------------------
# interface tracing
# ---------------------------------------------------------------------------

def extract_interface(visible: np.ndarray, hidden: np.ndarray) -> list[np.ndarray]:
    """Polylines separating visible from hidden pixels (grid-corner coords).

    Both arrays are disjoint subsets of one feather. Returns a list of Nx2
    float arrays in grid-corner coordinates (0..w, 0..h).
    """
    h, w = visible.shape
    adj: dict[tuple, list[tuple]] = {}

    def add_edge(a, b):
        a, b = tuple(a), tuple(b)
        if a == b:
            return
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    for r in range(h):
        for c in range(w):
            v = visible[r, c]
            hd = hidden[r, c]
            if not (v or hd):
                continue
            # horizontal neighbour -> vertical edge at x = c+1
            if c + 1 < w:
                ov = visible[r, c + 1]
                oh = hidden[r, c + 1]
                if (v and oh) or (hd and ov):
                    add_edge((c + 1, r), (c + 1, r + 1))
            # vertical neighbour -> horizontal edge at y = r+1
            if r + 1 < h:
                ov = visible[r + 1, c]
                oh = hidden[r + 1, c]
                if (v and oh) or (hd and ov):
                    add_edge((c, r + 1), (c + 1, r + 1))

    # dedupe neighbours
    adj = {k: list(dict.fromkeys(v)) for k, v in adj.items()}

    used: set[tuple] = set()
    polylines: list[np.ndarray] = []

    def walk(start):
        path = [start]
        used.add(start)
        cur = start
        prev = None
        while True:
            nbrs = [n for n in adj[cur] if n != prev and n not in used]
            if not nbrs:
                break
            prev, cur = cur, nbrs[0]
            used.add(cur)
            path.append(cur)
        return path

    # open chains (degree-1 endpoints) first
    for v, ns in adj.items():
        if len(ns) == 1 and v not in used:
            polylines.append(walk(v))
    # then closed loops
    for v in adj:
        if v not in used:
            p = walk(v)
            if p[0] in adj[p[-1]]:
                p.append(p[0])
            polylines.append(p)

    return [np.asarray(p, dtype=float) for p in polylines if len(p) >= 2]


# ---------------------------------------------------------------------------
# SVG / report / preview output
# ---------------------------------------------------------------------------

def _poly_to_d(poly_mm, closed_eps=0.01, prec=3):
    if len(poly_mm) < 2:
        return ""
    pts = [f"{x:.{prec}f},{y:.{prec}f}" for (x, y) in poly_mm]
    d = "M " + pts[0] + " L " + " ".join(pts[1:])
    first = poly_mm[0]
    last = poly_mm[-1]
    if (last[0] - first[0]) ** 2 + (last[1] - first[1]) ** 2 <= closed_eps ** 2:
        d += " Z"
    return d


def write_svg(out: Path, src: Path, feathers: list[Feather]):
    tree = ET.parse(src)
    root = tree.getroot()
    vb = root.get("viewBox", "0 0 247.95744 570.1775")
    w = root.get("width", "247.95744mm")
    h = root.get("height", "570.17749mm")

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{w}" height="{h}" viewBox="{vb}" version="1.1"',
        '     xmlns="http://www.w3.org/2000/svg">',
        "  <style>",
        "    .ref { fill:none; stroke:#b5b5b5; stroke-width:0.2; }",
        "    .visline { fill:none; stroke:#e41a1c; stroke-width:0.45;"
        " stroke-linecap:round; stroke-linejoin:round; }",
        "    .lbl { font-family:sans-serif; font-size:4px; fill:#e41a1c; }",
        "  </style>",
        '  <g id="feathers">',
    ]
    # keep the source's wider (family) groupings, in the authoritative order
    by_family: dict[str, list[Feather]] = {}
    for f in feathers:
        by_family.setdefault(f.family, []).append(f)
    families = [fam for fam in FAMILY_ORDER_BOTTOM_TO_TOP if fam in by_family]
    families += sorted(set(by_family) - set(FAMILY_ORDER_BOTTOM_TO_TOP))
    for fam in families:
        parts.append(f'    <g id="{fam}" data-family="{fam}">')
        for f in sorted(by_family[fam], key=lambda x: _feather_index(x.id)):
            parts.append(f'      <g id="{f.id}" data-family="{f.family}">')
            d = _poly_to_d(f.polys[0])
            parts.append(f'        <path class="ref" id="ref-{f.id}" d="{d}"/>')
            if f.lines_mm:
                parts.append(f'        <g id="vis-{f.id}">')
                for line in f.lines_mm:
                    d = _poly_to_d(line)
                    parts.append(f'          <path class="visline" d="{d}"/>')
                # label at the midpoint of the longest line
                longest = max(f.lines_mm, key=len)
                mid = longest[len(longest) // 2]
                parts.append(f'          <text class="lbl" x="{mid[0]:.3f}" '
                             f'y="{mid[1]:.3f}">{f.id}</text>')
                parts.append("        </g>")
            parts.append("      </g>")
        parts.append("    </g>")
    parts.append("  </g>")
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8", newline="\n")


def write_report(out: Path, feathers: list[Feather], res: float):
    rows = []
    for f in feathers:
        if f.visible_frac >= 0.999:
            status = "full"
        elif f.visible_frac <= 0.001:
            status = "none"
        else:
            status = "partial"
        rows.append({
            "id": f.id,
            "family": f.family,
            "area_mm2": round(f.area_mm2, 2),
            "visible_area_mm2": round(f.visible_area_mm2, 2),
            "visible_fraction": round(f.visible_frac, 4),
            "status": status,
            "num_lines": len(f.lines_mm or []),
            "res_mm_per_px": res,
        })
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8", newline="\n")
    return rows


def write_preview(out: Path, feathers: list[Feather], x0, y0, res, w, h):
    img = Image.new("RGB", (w, h), (255, 255, 255))
    overlay = Image.new("RGB", (w, h), (255, 255, 255))
    dover = ImageDraw.Draw(overlay)

    for f in feathers:
        color = FAMILY_COLORS.get(f.family, "#777777")
        rgb = tuple(int(color.lstrip("#")[i: i + 2], 16) for i in (0, 2, 4))
        # draw hidden region darker, visible region in the family colour
        if f.hidden is not None:
            dover.bitmap((0, 0), Image.fromarray(f.hidden), fill=(60, 60, 60))
        if f.visible is not None:
            dover.bitmap((0, 0), Image.fromarray(f.visible), fill=rgb)

    img = Image.blend(img, overlay, alpha=0.75)

    d = ImageDraw.Draw(img)
    # outlines
    for f in feathers:
        for poly in f.polys:
            pts = [(round((x - x0) / res), round((y - y0) / res)) for (x, y) in poly]
            d.line(pts + [pts[0]], fill=(0, 0, 0), width=1)
    # visibility lines
    for f in feathers:
        for line in (f.lines_mm or []):
            pts = [(round((x - x0) / res), round((y - y0) / res)) for (x, y) in line]
            d.line(pts, fill=(229, 26, 28), width=3)

    img.save(out)


VIS_STYLE = """/* generated visibility lines -- see tools/generate_visibility_lines.py */
.visibility-line {
  fill: none;
  stroke: #e41a1c;
  stroke-width: 0.264583;
  stroke-linecap: round;
  stroke-linejoin: round;
}
"""


def integrate_into_source(src: Path, feathers: list[Feather]) -> int:
    """Write the visibility lines into the aggregate source, beside each feather.

    The lines are computed in absolute mm, but the source stores every feather in
    its own transformed local frame, so each polyline is mapped back through the
    inverse of its feather group's composed transform and inserted as a
    ``<path class="visibility-line">`` immediately after that feather's outline --
    inside the feather group, so it inherits the same transform. Idempotent: lines
    and the stylesheet rule from a previous run are replaced, not stacked.
    """
    text = src.read_text(encoding="utf-8")

    # drop whatever a previous run wrote
    text = re.sub(r"\n[ \t]*<path\b[^>]*?-visibility-line[^>]*?/>", "", text)
    text = text.replace(VIS_STYLE, "")
    if "</style>" not in text:
        raise SystemExit("no <style> block found in " + str(src))
    text = text.replace("</style>", VIS_STYLE + "</style>", 1)

    inserted = 0
    for f in feathers:
        if not f.lines_mm or f.group_matrix is None:
            continue
        inv = mat_inv(f.group_matrix)
        d = " ".join(
            _poly_to_d([svg_util.mat_apply(inv, x, y) for (x, y) in line], prec=4)
            for line in f.lines_mm)
        el = (f'\n      <path'
              f'\n         class="visibility-line"'
              f'\n         id="{f.id}-visibility-line"'
              f'\n         inkscape:label="{f.id} visibility"'
              f'\n         d="{d}" />')
        m = re.search(
            r'<path\b[^>]*?id="' + re.escape(f.id) + r'-outline"[^>]*?/>', text)
        if not m:
            print(f"warning: no outline for {f.id}; not integrated", file=sys.stderr)
            continue
        text = text[:m.end()] + el + text[m.end():]
        inserted += 1

    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        raise SystemExit(f"integrated file would not parse: {exc}")

    src.write_text(text, encoding="utf-8", newline="\n")
    return inserted


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate per-feather visibility lines from the aggregate SVG.")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--preview", type=Path, default=None,
                    help="also write a PNG preview (path; default: off)")
    ap.add_argument("--res", type=float, default=DEFAULT_RES_MM,
                    help="raster resolution in mm/pixel (default %(default)s)")
    ap.add_argument("--order-file", type=Path, default=None,
                    help="text file of feather ids, front-to-back, one per line")
    ap.add_argument("--integrate", action="store_true",
                    help="write the lines into the source SVG (--src), inside each "
                         "feather group; replaces any it wrote before")
    args = ap.parse_args(argv)

    feathers = load_feathers(args.src)
    if not feathers:
        raise SystemExit("no feather outlines found in " + str(args.src))
    print(f"loaded {len(feathers)} feathers from {args.src}")

    if args.order_file:
        ordered = order_from_file(feathers, args.order_file)
    else:
        ordered = default_order(feathers)
    print("front-to-back order:")
    print("  " + " ".join(f.id for f in ordered))

    x0, y0, w, h = rasterize(feathers, args.res)
    print(f"grid {w}x{h} px at {args.res} mm/px "
          f"(wing bbox {w * args.res:.0f} x {h * args.res:.0f} mm)")

    # walk front-to-back; the running union holds everything in front.
    occluder = np.zeros((h, w), dtype=bool)
    for f in ordered:
        mask = f.mask
        f.visible = mask & ~occluder
        f.hidden = mask & occluder
        occluder |= mask

    # visibility lines and metrics
    for f in feathers:
        vis_count = int(f.visible.sum())
        total = int(f.mask.sum())
        f.visible_frac = vis_count / total if total else 0.0
        f.visible_area_mm2 = vis_count * args.res * args.res
        ifaces = extract_interface(f.visible, f.hidden)
        f.lines_mm = []
        for iface in ifaces:
            # grid corner coords -> mm, then simplify (tol in mm)
            line_mm = np.array([(x0 + px * args.res, y0 + py * args.res)
                                for (px, py) in iface])
            line_mm = douglas_peucker(line_mm, 0.5)
            if len(line_mm) >= 2:
                f.lines_mm.append(line_mm)

    write_svg(args.out, args.src, feathers)
    rows = write_report(args.report, feathers, args.res)
    if args.preview:
        write_preview(args.preview, feathers, x0, y0, args.res, w, h)

    print(f"\nwrote {args.out}")
    print(f"wrote {args.report}")
    if args.preview:
        print(f"wrote {args.preview}")

    if args.integrate:
        n = integrate_into_source(args.src, feathers)
        print(f"integrated {n} visibility-line paths into {args.src}")

    print("\nper-feather visibility:")
    for r in rows:
        print(f"  {r['id']:>4} {r['family']:>2}  visible {r['visible_fraction']*100:5.1f}%"
              f"  ({r['status']})  lines={r['num_lines']}")


if __name__ == "__main__":
    main()
