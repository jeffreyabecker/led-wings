"""Generate a printable, multi-page PDF of feather templates from the AGGREGATE SVG.

This is a separate document from ``tools/make_feather_template_pdf.py`` (which reads one
SVG per feather from ``as-built/vectors/individuals``, now removed). This generator
takes its paths straight from the catalog built by
``mechanical/templates/build-feather-aggregate.py``:

    mechanical/templates/as-built/vectors/feathers-aggregate.svg

Three things the aggregate needs that the per-file source did not:

* **The ``toplines`` group is ignored.** The guide curves that run along the leading
  edge of each feather group are scaffolding, not cut lines, so neither the group nor
  anything inside it reaches the document. Any other group whose style hides it
  (``display:none``) is skipped too.
* **Centre lines are read but never printed, and a feather may have none.** The quill
  guide tells the generator which end of a feather is the base, so it is still read
  where the aggregate carries it; a feather group with no ``*-center-line`` path just
  falls back to reading the base off the outline. Nothing is drawn either way: the
  outline is the only thing this document is for.
* **Every feather is turned upright first.** The aggregate is a *hand arrangement* --
  each prefix group carries its own rotation and scale, and 38 of the 42 feathers are
  drawn rotated (B1-B4 are all but horizontal, SC2-SC8 sit at 140-158 degrees). The
  catalogue is right to store it that way; a cutting template is not. Each outline is
  therefore rotated onto its own long axis (minimum-area rectangle, so a curved
  feather is not left leaning) before any layout happens.

The large feathers (P, S, B -- the long primaries, secondaries and body feathers) are
then laid down as *headless* pairs: the feather keeps its long axis vertical, but the
pair itself is turned a quarter turn, so the two halves stack above and below a
horizontal mirror axis rather than sitting side by side. An upright B or P pair is
around 260 mm across and cannot share the 273 mm page with anything else; headless it
is ~205 mm wide, which is what lets those pages exist at all. The choice is made per
feather by comparing the page height each orientation needs (``--pair-orientation``),
so it follows the geometry rather than a hard-coded family list.

Pages print at TRUE SCALE: user units are millimetres, so geometry is emitted
unchanged and the PDF MediaBox uses that grain. Every page is 273 mm wide (the
requested maximum) with a height that adapts to its pairs.

Usage:
    python tools/make_feather_template_pdf_from_aggregate.py
    python tools/make_feather_template_pdf_from_aggregate.py --only P1 B5 LC1
    python tools/make_feather_template_pdf_from_aggregate.py --scale 0.8
    python tools/make_feather_template_pdf_from_aggregate.py --orientation upright
    python tools/make_feather_template_pdf_from_aggregate.py --out some/other.pdf
    # poster-tile every logical page onto physical sheets (US Letter, landscape):
    python tools/make_feather_template_pdf_from_aggregate.py --tile-paper letter
    # the same on A4 with a custom overlap:
    python tools/make_feather_template_pdf_from_aggregate.py --tile-paper a4 --tile-overlap 10
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = (
    REPO_ROOT / "mechanical" / "templates" / "as-built" / "vectors"
    / "feathers-aggregate-min.svg"
)
DEFAULT_OUT = (
    REPO_ROOT / "mechanical" / "templates" / "as-built" / "print" / "feathers-from-aggregate.pdf"
)
SVG_NS = "http://www.w3.org/2000/svg"

FLATTEN_TOL_MM = 0.02           # max chord deviation when flattening curves
PT_PER_MM = 72.0 / 25.4
DEFAULT_STROKE_MM = 0.5         # the aggregate's `.group` stylesheet

# Groups that are scaffolding rather than feather geometry, matched on the `id` of a
# top-level group in the aggregate. Everything inside them is ignored.
SKIP_GROUPS = ("toplines",)

# Feather order: inner primary (P1) through to the small lower coverts.
FEATHER_ORDER = (
    [f"P{i}" for i in range(1, 11)]
    + [f"S{i}" for i in range(1, 11)]
    + [f"B{i}" for i in range(1, 6)]
    + [f"SC{i}" for i in range(1, 11)]
    + [f"PC{i}" for i in range(1, 7)]
    + [f"A{i}" for i in range(1, 5)]
    + [f"MC{i}" for i in range(1, 6)]
    + [f"LC{i}" for i in range(1, 7)]
    + [f"U{i}" for i in range(1, 11)]
)

# ---------------------------------------------------------------------------
# layout constants (millimetres)
# ---------------------------------------------------------------------------
PAGE_WIDTH_MM = 273.0           # hard maximum page width
MARGIN_MM = 12.0                # preferred page edge to the outermost content
MIN_MARGIN_MM = 5.0             # allowed to shrink so a wide pair still fits
# Clear space at the top and bottom of a page. These documents are meant to be
# printed through Acrobat's poster/tile mode, which joins tiles with an overlap
# (0.5 in by default), so no ink should sit nearer the trim than that or a tile
# cannot be registered against its neighbour.
MARGIN_TOP_MM = 6.0
MARGIN_BOTTOM_MM = 6.0
# Clear space between the two halves of ONE mirrored pair, across its centre line.
# This is what makes a pair usable: the mirror-image outline is not on top of the
# cut edge you are working on.
SMALL_PARTNER_GAP_MM = 30.0
LARGE_PARTNER_GAP_MM = 70.0
# Families that take the wide gap: the long primaries, secondaries and body
# feathers. Their profiles run close to the pair's centre line along their whole
# length, so the mirror-image cut edge really would be in the way.
LARGE_FAMILIES = ("P", "S", "B")
# Floor for the ideal gap when a pair would otherwise be a few millimetres too wide
# for the page (see ``_pair_candidates``). Two primaries need this; nothing else does.
MIN_PARTNER_GAP_MM = 30.0
# Clear space between neighbouring pairs on a page.
SPARSE_GAP_MM = 70.0            # around a row that holds a single pair
DENSE_GAP_MM = 30.0             # between pairs sharing a row, and between rows
# Vertical furniture, each measured from the page edge to the body of pairs.
HEAD_MM = MARGIN_TOP_MM + 15.2
LABEL_BAND_MM = 6.6
FOOT_MM = MARGIN_BOTTOM_MM + 15.0
LABEL_SIZE_MM = 4.4
ID_SIZE_MM = 6.0
FOOT_SIZE_MM = 3.0
LABEL_GAP_MM = 0.9              # gap from the pair to its ID line
MIN_PAGE_HEIGHT_MM = 60.0
SCALE_BAR_MM = 50.0
MAX_PAGE_HEIGHT_MM = 1050.0     # pages are packed up to about this height
GROUP_JOIN = (("SC", "PC", "A"), ("MC", "LC"))
# Families whose pages are capped separately from the long feathers. The primaries,
# secondaries and body feathers cannot come down to this size -- a single pair is
# 405-567 mm tall and no amount of spacing changes that -- so they keep the full
# budget and the small coverts get the short pages. A pair this size tiles into ONE
# row of sheets rather than a grid, which is what makes the document printable on a
# machine that refuses a tall sheet.
SMALL_FAMILIES = ("SC", "PC", "A", "MC", "LC")
# The same set, named the way a packed *group* is named: `GROUP_JOIN` merges those
# five families into two groups, and the group name is what the cap is asked about.
SMALL_PAGE_GROUPS = ("SC / PC / A", "MC / LC")
SMALL_PAGE_HEIGHT_MM = 200.0

# ---------------------------------------------------------------------------
# paper sizes and tiling (poster mode)
# ---------------------------------------------------------------------------
MM_PER_INCH = 25.4

# Landscape sheet extents are what matter here -- the sheet is never used portrait.
# Keyed on the spec with everything but letters and digits removed, so `8.5x11`,
# `8.5 x 11` and `85x11` all land on the same sheet.
TILE_PAPER_SIZES = {
    "85x11": ("8.5x11", 8.5 * MM_PER_INCH, 11.0 * MM_PER_INCH),
    "letter": ("8.5x11", 8.5 * MM_PER_INCH, 11.0 * MM_PER_INCH),
    "a4": ("A4", 210.0, 297.0),
}

TILE_PAPER_NAMES = "8.5x11|a4"   # what the CLI advertises

TILE_MARGIN_MM = 5.0             # non-printable margin kept clear on each sheet
TILE_OVERLAP_MM = 12.7           # Acrobat's default poster overlap (0.5 in)
TILE_GAP_MM = 6.0                # clear space between two pages sharing one sheet

HALF_FILL = (0.93, 0.93, 0.93)
GUIDE_GREY = (0.55, 0.55, 0.55)
TEXT_GREY = (0.25, 0.25, 0.25)

HELVETICA_WIDTHS = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, "0": 556, "1": 556, "2": 556, "3": 556, "4": 556,
    "5": 556, "6": 556, "7": 556, "8": 556, "9": 556, ":": 278, ";": 278,
    "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015, "A": 667, "B": 667,
    "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722, "I": 278,
    "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469,
    "_": 556, "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556,
    "f": 278, "g": 556, "h": 556, "i": 222, "j": 222, "k": 500, "l": 222,
    "m": 833, "n": 556, "o": 556, "p": 556, "q": 556, "r": 333, "s": 500,
    "t": 278, "u": 556, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584,
}

NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
COMMAND_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]")


def text_width_mm(text: str, size_mm: float) -> float:
    """Width of `text` in Helvetica at `size_mm` em size (1/1000 em units)."""
    return sum(HELVETICA_WIDTHS.get(c, 556) for c in text) / 1000.0 * size_mm


# ---------------------------------------------------------------------------
# affine matrices, stored as (a, b, c, d, e, f) meaning
#     x' = a*x + c*y + e
#     y' = b*x + d*y + f
# (SVG space: x right, y DOWN. Every operation here stays in that space until the
#  layout flips it onto the PDF page, exactly as the source files are authored.)
# ---------------------------------------------------------------------------
Matrix = tuple


def mat_identity() -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m1: Matrix, m2: Matrix) -> Matrix:
    """m1 * m2, i.e. the transform that applies m2 first, then m1."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def mat_apply(m: Matrix, x: float, y: float) -> tuple:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def mat_translate(tx: float, ty: float) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def mat_scale(sx: float, sy: float) -> Matrix:
    return (sx, 0.0, 0.0, sy, 0.0, 0.0)


def mat_rotate(deg: float, cx: float = 0.0, cy: float = 0.0) -> Matrix:
    rad = math.radians(deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    rot = (cos_r, sin_r, -sin_r, cos_r, 0.0, 0.0)
    if cx or cy:
        return mat_mul(mat_mul(mat_translate(cx, cy), rot), mat_translate(-cx, -cy))
    return rot


def parse_transform(text: str) -> Matrix:
    """Parse an SVG transform attribute list (matrix/translate/scale/rotate/skew)."""
    result = mat_identity()
    for name, raw_args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", text or ""):
        args = [float(v) for v in NUMBER_RE.findall(raw_args)]
        name = name.strip()
        if name == "matrix" and len(args) == 6:
            m = tuple(args)
        elif name == "translate":
            m = mat_translate(args[0], args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            m = mat_scale(args[0], args[1] if len(args) > 1 else args[0])
        elif name == "rotate":
            cx, cy = (args[1], args[2]) if len(args) > 2 else (0.0, 0.0)
            m = mat_rotate(args[0], cx, cy)
        elif name == "skewX":
            m = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
        elif name == "skewY":
            m = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise ValueError(f"unsupported transform: {name}({raw_args})")
        result = mat_mul(result, m)
    return result


# ---------------------------------------------------------------------------
# path parsing (SVG path data -> absolute M/L/C segments)
# ---------------------------------------------------------------------------
@dataclass
class SvgPath:
    subpaths: list = field(default_factory=list)
    closed: bool = False


def _tokenize(d: str) -> list:
    tokens: list = []
    i, n = 0, len(d)
    while i < n:
        ch = d[i]
        if ch in " ,\t\r\n":
            i += 1
            continue
        if ch.isalpha():
            tokens.append(ch)
            i += 1
            continue
        m = NUMBER_RE.match(d, i)
        if not m:
            raise ValueError(f"bad path token at {i}: {d[i:i + 24]!r}")
        tokens.append(float(m.group(0)))
        i = m.end()
    return tokens


def _arc_to_curves(x0, y0, rx, ry, phi_deg, large_arc, sweep, x1, y1) -> list:
    """Convert an SVG elliptical arc to a list of cubic segments (absolute coords)."""
    if rx == 0 or ry == 0:
        return [("L", x1, y1)]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg % 360.0)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x0 - x1) / 2.0, (y0 - y1) / 2.0
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1.0:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(num / den, 0.0))
    if large_arc == sweep:
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cos_p * cxp - sin_p * cyp + (x0 + x1) / 2.0
    cy = sin_p * cxp + cos_p * cyp + (y0 + y1) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        norm = math.hypot(ux, uy) * math.hypot(vx, vy)
        val = max(-1.0, min(1.0, dot / norm)) if norm else 1.0
        ang = math.acos(val)
        if ux * vy - uy * vx < 0:
            ang = -ang
        return ang

    theta1 = angle(1.0, 0.0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                   (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep and dtheta < 0:
        dtheta += 2 * math.pi

    n_seg = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2.0))))
    delta = dtheta / n_seg
    t = 4.0 / 3.0 * math.tan(delta / 4.0)
    segments = []
    theta = theta1
    for _ in range(n_seg):
        cos1, sin1 = math.cos(theta), math.sin(theta)
        cos2, sin2 = math.cos(theta + delta), math.sin(theta + delta)
        e1x = cos_p * rx * cos1 - sin_p * ry * sin1 + cx
        e1y = sin_p * rx * cos1 + cos_p * ry * sin1 + cy
        e2x = cos_p * rx * cos2 - sin_p * ry * sin2 + cx
        e2y = sin_p * rx * cos2 + cos_p * ry * sin2 + cy
        d1x = -cos_p * rx * sin1 - sin_p * ry * cos1
        d1y = -sin_p * rx * sin1 + cos_p * ry * cos1
        d2x = -cos_p * rx * sin2 - sin_p * ry * cos2
        d2y = -sin_p * rx * sin2 + cos_p * ry * cos2
        segments.append(("C",
                         e1x + t * d1x, e1y + t * d1y,
                         e2x - t * d2x, e2y - t * d2y,
                         e2x, e2y))
        theta += delta
    return segments


def parse_path(d: str) -> SvgPath:
    """Parse SVG path data into an SvgPath of absolute M/L/C/Z segments (arcs -> cubics)."""
    tokens = _tokenize(d)
    subpaths: list = []
    current: list = []
    i, n = 0, len(tokens)
    cmd = None
    x = y = 0.0
    start_x = start_y = 0.0
    prev_c2 = None
    prev_q1 = None
    closed_any = False

    def flush():
        nonlocal current
        if current:
            subpaths.append(current)
            current = []

    while i < n:
        tok = tokens[i]
        if isinstance(tok, str):
            cmd = tok
            i += 1
            if cmd in "Zz":
                if current:
                    current.append(("Z",))
                    closed_any = True
                x, y = start_x, start_y
                prev_c2 = prev_q1 = None
                continue
        elif cmd is None:
            raise ValueError("path data does not start with a command")

        upper = cmd.upper()
        relative = cmd.islower()
        if upper in "ML":
            x1, y1 = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if relative:
                x1, y1 = x + x1, y + y1
            if upper == "M":
                flush()
                current.append(("M", x1, y1))
                start_x, start_y = x1, y1
                cmd = "l" if relative else "L"
            else:
                current.append(("L", x1, y1))
            x, y = x1, y1
            prev_c2 = prev_q1 = None
            continue
        if upper == "H":
            x1 = float(tokens[i])
            i += 1
            if relative:
                x1 = x + x1
            current.append(("L", x1, y))
            x = x1
            prev_c2 = prev_q1 = None
            continue
        if upper == "V":
            y1 = float(tokens[i])
            i += 1
            if relative:
                y1 = y + y1
            current.append(("L", x, y1))
            y = y1
            prev_c2 = prev_q1 = None
            continue
        if upper == "C":
            vals = [float(v) for v in tokens[i:i + 6]]
            i += 6
            x1, y1, x2, y2, x3, y3 = vals
            if relative:
                x1, y1, x2, y2, x3, y3 = (
                    x + x1, y + y1, x + x2, y + y2, x + x3, y + y3,
                )
            current.append(("C", x1, y1, x2, y2, x3, y3))
            prev_c2 = (x2, y2)
            x, y = x3, y3
            prev_q1 = None
            continue
        if upper == "S":
            vals = [float(v) for v in tokens[i:i + 4]]
            i += 4
            x2, y2, x3, y3 = vals
            if relative:
                x2, y2, x3, y3 = x + x2, y + y2, x + x3, y + y3
            if prev_c2 is None:
                x1, y1 = x, y
            else:
                x1, y1 = 2 * x - prev_c2[0], 2 * y - prev_c2[1]
            current.append(("C", x1, y1, x2, y2, x3, y3))
            prev_c2 = (x2, y2)
            x, y = x3, y3
            prev_q1 = None
            continue
        if upper in "QT":
            if upper == "Q":
                vals = [float(v) for v in tokens[i:i + 4]]
                i += 4
                qx, qy, x3, y3 = vals
                if relative:
                    qx, qy, x3, y3 = x + qx, y + qy, x + x3, y + y3
                prev_q1 = (qx, qy)
            else:
                vals = [float(v) for v in tokens[i:i + 2]]
                i += 2
                x3, y3 = vals
                if relative:
                    x3, y3 = x + x3, y + y3
                if prev_q1 is None:
                    qx, qy = x, y
                else:
                    qx, qy = 2 * x - prev_q1[0], 2 * y - prev_q1[1]
                prev_q1 = (qx, qy)
            c1x, c1y = x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y)
            c2x, c2y = x3 + 2.0 / 3.0 * (qx - x3), y3 + 2.0 / 3.0 * (qy - y3)
            current.append(("C", c1x, c1y, c2x, c2y, x3, y3))
            x, y = x3, y3
            prev_c2 = None
            continue
        if upper == "A":
            vals = tokens[i:i + 7]
            i += 7
            rx, ry, rot, large, sweep, ax, ay = [float(v) for v in vals]
            if relative:
                ax, ay = x + ax, y + ay
            for seg in _arc_to_curves(x, y, rx, ry, rot, int(large), int(sweep), ax, ay):
                current.append(seg)
            x, y = ax, ay
            prev_c2 = prev_q1 = None
            continue
        raise ValueError(f"unsupported path command: {cmd}")

    flush()
    return SvgPath(subpaths, closed=closed_any)


# ---------------------------------------------------------------------------
# transforms, flattening and bbox
# ---------------------------------------------------------------------------
def transform_path(path: SvgPath, m: Matrix) -> SvgPath:
    """Return a new SvgPath with every coordinate mapped through m."""
    if m == mat_identity():
        return path
    out: list = []
    for sub in path.subpaths:
        new_sub = []
        for seg in sub:
            if seg[0] == "Z":
                new_sub.append(("Z",))
            else:
                pts = [mat_apply(m, seg[i], seg[i + 1]) for i in range(1, len(seg), 2)]
                flat = [seg[0]]
                for x, y in pts:
                    flat.extend((x, y))
                new_sub.append(tuple(flat))
        out.append(new_sub)
    return SvgPath(out, closed=path.closed)


def _flatten_cubic(p0, p1, p2, p3, tol, out, depth=0):
    """Adaptive subdivision; appends points after p0 up to and including p3."""
    if depth >= 24:
        out.append(p3)
        return
    x0, y0 = p0
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    ux, uy = 3 * x1 - 2 * x0 - x3, 3 * y1 - 2 * y0 - y3
    vx, vy = 3 * x2 - 2 * x3 - x0, 3 * y2 - 2 * y3 - y0
    d = max(ux * ux, vx * vx) + max(uy * uy, vy * vy)
    if d <= 16.0 * tol * tol:
        out.append(p3)
        return
    x01, y01 = (x0 + x1) / 2, (y0 + y1) / 2
    x12, y12 = (x1 + x2) / 2, (y1 + y2) / 2
    x23, y23 = (x2 + x3) / 2, (y2 + y3) / 2
    x012, y012 = (x01 + x12) / 2, (y01 + y12) / 2
    x123, y123 = (x12 + x23) / 2, (y12 + y23) / 2
    xm, ym = (x012 + x123) / 2, (y012 + y123) / 2
    _flatten_cubic((x0, y0), (x01, y01), (x012, y012), (xm, ym), tol, out, depth + 1)
    _flatten_cubic((xm, ym), (x123, y123), (x23, y23), (x3, y3), tol, out, depth + 1)


def flatten_path(path: SvgPath, tol: float = FLATTEN_TOL_MM) -> list:
    """Convert an SvgPath to closed polylines of (x, y) points."""
    polys: list = []
    for sub in path.subpaths:
        pts: list = []
        cx = cy = sx = sy = 0.0
        for seg in sub:
            op = seg[0]
            if op == "M":
                if len(pts) > 1:
                    polys.append(pts)
                cx = sx = seg[1]
                cy = sy = seg[2]
                pts = [(cx, cy)]
            elif op == "L":
                cx, cy = seg[1], seg[2]
                pts.append((cx, cy))
            elif op == "C":
                _flatten_cubic((cx, cy), (seg[1], seg[2]), (seg[3], seg[4]),
                               (seg[5], seg[6]), tol, pts)
                cx, cy = seg[5], seg[6]
            elif op == "Z":
                if pts and (abs(pts[0][0] - cx) > 1e-9 or abs(pts[0][1] - cy) > 1e-9):
                    pts.append(pts[0])
                cx, cy = sx, sy
        if len(pts) > 1:
            polys.append(pts)
    return polys


def bbox_of_polys(polys) -> tuple:
    xs_min = ys_min = math.inf
    xs_max = ys_max = -math.inf
    for poly in polys:
        for x, y in poly:
            xs_min = min(xs_min, x)
            xs_max = max(xs_max, x)
            ys_min = min(ys_min, y)
            ys_max = max(ys_max, y)
    if xs_min is math.inf:
        raise ValueError("empty geometry")
    return (xs_min, ys_min, xs_max, ys_max)


def expand_bbox(box, amount: float) -> tuple:
    x0, y0, x1, y1 = box
    return (x0 - amount, y0 - amount, x1 + amount, y1 + amount)


def path_points(d: str) -> list:
    """Sample a path's points (cubic controls included), for extent tests."""
    pts: list = []
    for sub in parse_path(d).subpaths:
        for seg in sub:
            for i in range(1, len(seg), 2):
                pts.append((seg[i], seg[i + 1]))
    return pts


# ---------------------------------------------------------------------------
# reading the aggregate
# ---------------------------------------------------------------------------
def family_of(name: str) -> str:
    """The group a feather belongs to for page packing: its letters, with the
    families that share a page merged (``GROUP_JOIN``). One definition, used by the
    packing, the page cap and the page itself, so they cannot disagree.
    """
    joins = {member: group for group in GROUP_JOIN for member in group}
    letters = "".join(c for c in name if c.isalpha())
    return joins.get(letters, letters)


def group_title(group) -> str:
    """A packing group's name as text: ('SC', 'PC', 'A') -> 'SC / PC / A'."""
    return " / ".join(group) if isinstance(group, (tuple, list)) else str(group)


@dataclass
class Feather:
    name: str
    source: Path
    polys_right: list              # outline in the as-drawn orientation, mm
    box: tuple                     # bbox of the stroke centreline of the outline
    stroke_mm: float
    declared_size_mm: tuple        # size in the aggregate before straightening
    view_box: tuple
    centered_guide: bool = False   # the aggregate carried a quill guide for this feather
    turned_deg: float = 0.0        # rotation applied to bring it upright

    @property
    def group(self) -> str:
        return family_of(self.name)

    @property
    def width(self) -> float:
        return self.box[2] - self.box[0]

    @property
    def height(self) -> float:
        return self.box[3] - self.box[1]

    @property
    def cut_box(self) -> tuple:
        """Bounding box including half the stroke width on each side."""
        return expand_bbox(self.box, self.stroke_mm / 2.0)


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _style_declared_hidden(el) -> bool:
    style = (el.get("style") or "").replace(" ", "").lower()
    if "display:none" in style:
        return True
    return (el.get("display") or "").strip().lower() == "none"


def _matrix_chain(root):
    """Parent map for the whole document, so ancestor transforms can be composed."""
    return {child: parent for parent in root.iter() for child in parent}


def element_matrix(el, parents) -> Matrix:
    """The composed transform of every ancestor of `el` and `el` itself."""
    chain = []
    cur = el
    while cur in parents:
        cur = parents[cur]
        chain.append(cur)
    m = mat_identity()
    for ancestor in reversed(chain):
        m = mat_mul(m, parse_transform(ancestor.get("transform", "")))
    return mat_mul(m, parse_transform(el.get("transform", "")))


def _direct_paths(group) -> list:
    """The group's own <path> children, ignoring anything in a nested group."""
    return [el for el in group if _local(el.tag) == "path"]


def _outline_and_centreline(group) -> tuple:
    """(outline path element, [centre line elements]) for one feather group.

    The group's own paths decide this, not its descendants: a prefix group wrapping
    several feathers must not be mistaken for a feather itself. A feather without a
    centre line (the aggregate stores none for it) simply reports an empty list.
    """
    paths = _direct_paths(group)
    outline = None
    for el in paths:
        eid = (el.get("id") or "").strip()
        if eid.endswith("-center-line"):
            continue
        if eid.endswith("-outline"):
            outline = el
            break
    if outline is None:
        # No id convention to go on: the outline is the stroked, unfilled path.
        stroked = [el for el in paths
                   if "fill:none" in (el.get("style") or "").replace(" ", "").lower()
                   or (el.get("fill") or "").strip().lower() == "none"]
        candidates = stroked or paths
        outline = candidates[0] if candidates else None
    lines = [el for el in paths if (el.get("id") or "").strip().endswith("-center-line")]
    return outline, lines


def _feather_groups(root) -> list:
    """Every feather group in the aggregate, skipping scaffolding groups.

    A feather group is a group whose *own* children carry an outline path. A prefix
    group (``P``, ``SC``, ...) holds no path of its own -- only a transform and its
    feathers -- so the walk descends through it and returns the individual feathers.
    A group named in ``SKIP_GROUPS`` (``toplines``) or hidden by its style is never
    entered, so no guide curve from it can reach the document.
    """
    out: list = []

    def visit(el):
        for child in el:
            if _local(child.tag) != "g":
                continue
            cid = (child.get("id") or "").strip()
            if cid in SKIP_GROUPS or _style_declared_hidden(child):
                continue
            if _direct_paths(child):
                out.append(child)
            else:
                visit(child)

    visit(root)
    return out


def de_anisotropy_calibration(m: Matrix) -> Matrix:
    """Scale each axis by 1/|column|, so an anisotropically scaled frame reads true.

    The aggregate's prefix groups do not merely rotate: P's group carries
    ``matrix(0.9997, 0, 0, 1.2001, ...)``, a frame stretched 20 percent in y, and B's
    is both rotated and scaled. Anything judging the *shape* of a feather -- how wide
    a vane is, which end is the tip -- has to compensate first, or the shear misleads
    it. (The rotation that stands the feather up is not one of those: see
    ``min_width_angle`` for why that is measured on the drawn geometry.)
    """
    sx = math.hypot(m[0], m[1]) or 1.0
    sy = math.hypot(m[2], m[3]) or 1.0
    return (1.0 / sx, 0.0, 0.0, 1.0 / sy, 0.0, 0.0)


def min_width_angle(pts) -> float:
    """The rotation (degrees, SVG space) that stands the points on their long axis.

    Found by searching: the answer is the angle at which the axis-aligned bounding
    box comes out narrowest, i.e. the feather's long axis vertical and its width (the
    across-feather extent) at its minimum. A coarse sweep pins the neighbourhood and
    a golden-section refinement takes it to well under a hundredth of a degree.

    This is deliberately *not* the long side of the minimum-area enclosing rectangle
    from the convex hull. That rectangle encloses the least area, which is a different
    question, and on these outlines -- curved vanes, a hooked tip -- the two answers
    diverge by up to several degrees, leaving the template visibly leaning.

    The angle is measured on the geometry exactly as the aggregate draws it, because
    that is the geometry being turned: the aggregate's prefix groups carry an
    anisotropic scale (P is 1.2001x in y, B is both rotated and scaled), and asking
    for the narrowest box in that sheared frame is the right question. It comes out
    about half a degree from the angle that would look upright in the pre-scale
    frame, and half a degree of lean over a 468 mm primary is 4 mm.
    """
    if len(pts) < 3:
        return 0.0

    def width_at(deg: float) -> float:
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        # Rotating about the origin is enough: a bounding-box width does not care
        # where the pivot is, and this is the linear part of mat_rotate(deg, ...).
        xs = [c * x - s * y for x, y in pts]
        return max(xs) - min(xs)

    coarse_step = 0.25
    best = (-90.0, float("inf"))
    deg = -90.0
    while deg <= 90.0 + 1e-9:
        w = width_at(deg)
        if w < best[1]:
            best = (deg, w)
        deg += coarse_step

    lo, hi = best[0] - coarse_step, best[0] + coarse_step
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    c = hi - ratio * (hi - lo)
    d = lo + ratio * (hi - lo)
    fc, fd = width_at(c), width_at(d)
    for _ in range(40):
        if hi - lo < 1e-7:
            break
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - ratio * (hi - lo)
            fc = width_at(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + ratio * (hi - lo)
            fd = width_at(d)
    return (lo + hi) / 2.0


def upright_matrix(polys, box, centre_hint=None) -> tuple:
    """(matrix, turned degrees) that turns an outline onto its own long axis.

    The long axis is made vertical, then the feather is turned end-for-end so the
    *base* -- where the quill starts -- is at the top of this SVG frame. The caller
    flips the frame onto the page, so that puts the base at the bottom of the printed
    template, the way the per-feather documents had it.

    The base is located from the quill centre line when there is one: its first point
    is the calamus end, and it runs nearly the full length of the feather (checked:
    0.99-1.01 of the length on this catalogue). Without a usable centre line the
    narrower end is taken as the tip, which is the one property that holds for every
    feather shape here.
    """
    pts = [p for poly in polys for p in poly]
    angle = min_width_angle(pts)
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    # `angle` is the rotation that stands the long axis up, in exactly the sense
    # mat_rotate applies it (both use x' = x cos - y sin), so it goes straight in.
    turn = mat_rotate(angle, cx, cy)
    turned = [[mat_apply(turn, x, y) for x, y in poly] for poly in polys]
    tbox = bbox_of_polys(turned)
    # The ends of the geometry itself, not of its bounding box: the quill guide can
    # stick out past the vane at either end, and using the box corners to decide
    # which way round the feather goes gets it wrong when it does.
    y_top = min(y for poly in turned for _, y in poly)
    y_bot = max(y for poly in turned for _, y in poly)

    def width_near(y):
        span = max((y_bot - y_top) * 0.015, 0.4)
        sel = [p for poly in turned for p in poly if abs(p[1] - y) <= span]
        return None if not sel else max(p[0] for p in sel) - min(p[0] for p in sel)

    base_at_top = None
    if centre_hint:
        hint = [mat_apply(turn, x, y) for x, y in centre_hint]
        h_len = max(p[1] for p in hint) - min(p[1] for p in hint)
        if h_len >= 0.5 * (tbox[3] - tbox[1]):
            start_y = hint[0][1]
            # The centre line starts at the calamus, so put that end at the top.
            base_at_top = abs(start_y - y_top) < abs(start_y - y_bot)
    if base_at_top is None:
        w_top, w_bot = width_near(y_top), width_near(y_bot)
        if w_top is not None and w_bot is not None:
            # no guide to go on: the narrower end is the tip, so the wider one is
            # the base and belongs at the top
            base_at_top = w_top > w_bot
    if base_at_top is None:
        base_at_top = True

    deg = angle
    if not base_at_top:
        # turn it end for end about its own centre
        spin = mat_rotate(180.0, (tbox[0] + tbox[2]) / 2.0, (tbox[1] + tbox[3]) / 2.0)
        turn = mat_mul(spin, turn)
        deg += 180.0
    return turn, deg


def load_aggregate_feathers(path: Path, only=None) -> list:
    """Every feather in the aggregate as a straight, vertical ``Feather``."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise SystemExit(f"{path}: not a readable SVG ({exc})") from exc
    root = tree.getroot()
    if root.tag != f"{{{SVG_NS}}}svg":
        raise SystemExit(f"{path}: unexpected root element {root.tag!r}")

    vb = [float(v) for v in NUMBER_RE.findall(root.get("viewBox", ""))]
    parents = _matrix_chain(root)

    wanted = set(only) if only else None
    feathers: list = []
    seen: set = set()
    for group in _feather_groups(root):
        name = (group.get("id") or "").strip()
        if not name:
            raise SystemExit(f"{path}: a feather group has no id")
        if wanted is not None and name not in wanted:
            continue
        if name in seen:
            raise SystemExit(f"{path}: feather group {name!r} appears twice")
        seen.add(name)

        outline, lines = _outline_and_centreline(group)
        if outline is None:
            raise SystemExit(f"{path}: {name}: no outline path found")
        m = element_matrix(group, parents)
        m = mat_mul(m, parse_transform(outline.get("transform", "")))

        raw_outline = parse_path(outline.get("d", ""))
        raw_polys = flatten_path(transform_path(raw_outline, m))
        if not raw_polys:
            raise SystemExit(f"{path}: {name}: the outline path is empty")
        raw_box = bbox_of_polys(raw_polys)
        declared = (raw_box[2] - raw_box[0], raw_box[3] - raw_box[1])

        # The quill guide is read only to say which end of the feather is the base;
        # it is turned with the outline so that test is made in the upright frame,
        # and then dropped. Nothing of it is drawn.
        guide_raw: list = []
        for el in lines:
            lm = mat_mul(element_matrix(group, parents),
                         parse_transform(el.get("transform", "")))
            guide_raw.extend(flatten_path(transform_path(parse_path(el.get("d", "")), lm)))
        guide_hint = [p for poly in guide_raw for p in poly]

        turn, deg = upright_matrix(raw_polys, raw_box, guide_hint)
        polys = [[mat_apply(turn, x, y) for x, y in poly] for poly in raw_polys]
        box = bbox_of_polys(polys)

        stroke_raw = outline.get("stroke-width")
        stroke = DEFAULT_STROKE_MM
        if stroke_raw:
            nums = NUMBER_RE.findall(stroke_raw)
            if nums:
                stroke = float(nums[0])
        # The aggregate's `.group` rule only applies to elements that are not hidden.
        feathers.append(Feather(
            name=name,
            source=path,
            polys_right=polys,
            box=box,
            stroke_mm=stroke,
            declared_size_mm=declared,
            view_box=tuple(vb) if len(vb) == 4 else (0.0, 0.0, 0.0, 0.0),
            centered_guide=bool(guide_hint),
            turned_deg=deg,
        ))

    if wanted is not None:
        missing = sorted(wanted - seen)
        if missing:
            raise SystemExit(f"unknown feather(s): {', '.join(missing)}")
    if not feathers:
        raise SystemExit(f"no feather groups found in {path}")
    return order_feathers(feathers)


def order_feathers(feathers: list) -> list:
    """Feather order: inner primary (P1) through to the small lower coverts."""
    found = {f.name: f for f in feathers}
    names = [n for n in FEATHER_ORDER if n in found]
    names += [n for n in sorted(found) if n not in FEATHER_ORDER]
    return [found[n] for n in names]


# ---------------------------------------------------------------------------
# PDF primitives
# ---------------------------------------------------------------------------
def num(value: float, places: int = 3) -> str:
    out = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return out if out not in ("", "-0", "-0.", "0.") else "0"


def pdf_string(text: str) -> str:
    out = []
    for ch in text:
        if ch in "()\\":
            out.append("\\" + ch)
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            out.append(f"\\{ord(ch) & 0xFF:03o}")
    return "".join(out)


def rgb(color) -> str:
    return " ".join(num(c, 3) for c in color)


def text_cmd(x: float, y: float, size: float, text: str, color=TEXT_GREY,
             align: str = "left", halo_mm: float = 0.0) -> str:
    """Emit text with `size` as the em size in millimetres, on one line."""
    width = text_width_mm(text, size)
    if align == "center":
        x -= width / 2.0
    elif align == "right":
        x -= width
    body = f"/F1 {num(size)} Tf 1 0 0 1 {num(x)} {num(y)} Tm ({pdf_string(text)}) Tj"
    if halo_mm <= 0:
        return f"BT {rgb(color)} rg {body} ET"
    pad = halo_mm
    backing = (
        f"{rgb((1, 1, 1))} rg "
        f"{num(x - pad)} {num(y - pad)} m "
        f"{num(x + width + pad)} {num(y - pad)} l "
        f"{num(x + width + pad)} {num(y + size + pad)} l "
        f"{num(x - pad)} {num(y + size + pad)} l h f"
    )
    return f"{backing}\nBT {rgb(color)} rg {body} ET"


def path_cmd(transformed_polys, close: bool = True) -> str:
    """PDF path construction operators for already page-space polylines."""
    parts = []
    for poly in transformed_polys:
        if len(poly) < 2:
            continue
        parts.append(f"{num(poly[0][0])} {num(poly[0][1])} m")
        for x, y in poly[1:]:
            parts.append(f"{num(x)} {num(y)} l")
        if close:
            parts.append("h")
    return "\n".join(parts)


def transform_polys(polys, matrix):
    return [[mat_apply(matrix, x, y) for x, y in poly] for poly in polys]


def mat_fit(box, x0: float, y0: float) -> tuple:
    """Map a bbox onto the rectangle whose lower-left corner is (x0, y0), flipping y."""
    bx0, by0, bx1, by1 = box
    return (1.0, 0.0, 0.0, -1.0, x0 - bx0, y0 + by1)


def fit_bbox(box, transform) -> tuple:
    x0, y0, x1, y1 = box
    corners = [mat_apply(transform, x, y) for x in (x0, x1) for y in (y0, y1)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------------------
# page building
# ---------------------------------------------------------------------------
@dataclass
class PairSlot:
    """One mirrored feather pair placed at a known position on a page."""

    feather: Feather
    axis_x: float
    cell_left: float           # left edge of the pair's cell
    cell_right: float          # right edge of the pair's cell
    pair_top: float            # top of the pair's ink
    pair_bottom: float
    label_y: float             # baseline of the half labels
    right_box: tuple           # page rect of the as-drawn half
    left_box: tuple            # page rect of the mirrored half
    right_to_page: tuple       # as-drawn geometry -> page
    left_to_page: tuple        # as-drawn geometry -> page, mirrored
    headless: bool = False     # pair laid down a quarter turn (halves stacked)
    gap_mm: float = 0.0        # clear space actually left between the halves

    @property
    def name(self) -> str:
        return self.feather.name

    @property
    def axis_y(self) -> float:
        """The mirror axis, when the pair is headless (it runs horizontally)."""
        return (self.pair_top + self.pair_bottom) / 2.0


@dataclass
class PageLayout:
    """A logical page holding one or more mirrored pairs."""

    page_w: float
    page_h: float
    slots: list
    title: str
    stroke_scale: float
    margin: float = MARGIN_MM
    group: str = ""                # the family group this page holds

    @property
    def names(self) -> list:
        return [s.name for s in self.slots]


def mat_scale_about(sx: float, sy: float, cx: float, cy: float) -> tuple:
    """Uniform scale by (sx, sy) about the point (cx, cy)."""
    return mat_mul(
        mat_mul(mat_translate(cx, cy), mat_scale(sx, sy)),
        mat_translate(-cx, -cy),
    )


def partner_gap(feather: Feather, scale: float = 1.0) -> float:
    """The ideal clear space between the two halves *within* one mirrored pair."""
    letters = "".join(c for c in feather.name if c.isalpha())
    large = letters in LARGE_FAMILIES
    return (LARGE_PARTNER_GAP_MM if large else SMALL_PARTNER_GAP_MM) * scale


@dataclass
class Pairing:
    """How one feather's mirrored pair is laid on the page."""

    headless: bool     # the pair is turned a quarter turn (the halves stack)
    gap_mm: float      # clear space between the halves, at TRUE size
    width_mm: float    # cell extents at print size
    height_mm: float


def _pair_candidates(feather: Feather, scale: float, mode: str,
                     page_w: float | None = None) -> list:
    """The pair layouts worth considering, each fitted to the page width.

    An upright pair is `2 * across + gap` wide, so the gap is the one dimension that
    can give: it is capped at whatever space is left once both halves are on the
    page. That matters only for the broadest primaries -- P2's upright pair wants
    70 mm between the halves and comes to 266.3 mm against a 273 mm page, 3.3 mm too
    wide -- and giving up 3 mm of channel costs nothing structural. A headless pair
    is `along` wide, which nothing can change, so its gap stays at the ideal figure.
    A candidate that cannot be fitted even at MIN_PARTNER_GAP_MM is dropped, so
    demanding an orientation the page cannot hold fails loudly instead of printing a
    pair with its halves overlapping.

    Every figure on a Pairing is at TRUE size, including the gap; `--scale` is
    applied once, when the pair is laid onto a page. `page_w` defaults to the
    document's page width (`PAGE_WIDTH_MM`); it is passed explicitly while the page
    width itself is being decided, since that is the question being answered.
    """
    cut = feather.cut_box
    across = cut[2] - cut[0]         # across the feather (long axis vertical)
    along = cut[3] - cut[1]          # along the feather
    ideal = partner_gap(feather)     # true size; scales with the document
    width = PAGE_WIDTH_MM if page_w is None else page_w
    usable = (width - 2.0 * MIN_MARGIN_MM) * scale
    candidates: list = []

    if mode in ("auto", "upright"):
        room = usable - 2.0 * across * scale
        if room + 1e-9 >= MIN_PARTNER_GAP_MM * scale:
            gap = min(ideal, max(room / scale, MIN_PARTNER_GAP_MM))
            candidates.append(Pairing(False, gap,
                                      (2.0 * across + gap) * scale, along * scale))

    if mode in ("auto", "headless"):
        if along * scale <= usable + 1e-9:
            candidates.append(Pairing(True, ideal,
                                      along * scale, (2.0 * across + ideal) * scale))
    return candidates


def pairing(feather: Feather, scale: float = 1.0, mode: str = "auto") -> Pairing:
    """Decide how this feather's pair is laid on the page.

    ``auto`` takes the shortest page; headless and upright are usually far enough
    apart (S3: 88 mm of page height) that the choice is unambiguous, and where they
    are close it hardly matters.
    """
    candidates = _pair_candidates(feather, scale, mode)
    if not candidates:
        cut = feather.cut_box
        raise ValueError(
            f"{feather.name}: no pair layout fits the {PAGE_WIDTH_MM:g} mm page "
            f"(feather {cut[2] - cut[0]:.1f} x {cut[3] - cut[1]:.1f} mm across x "
            f"along, {MIN_PARTNER_GAP_MM:g} mm minimum partner gap)"
        )
    return min(candidates, key=lambda p: p.height_mm)


def minimum_page_width(feather: Feather, scale: float = 1.0,
                       mode: str = "auto") -> float:
    """The narrowest page this feather's pair can be laid on, in millimetres.

    Found by searching, not by formula: `_pair_candidates` is the only thing that
    knows what a pair needs (an upright pair can give up gap down to the floor, a
    headless one cannot give up anything), so the question is simply the smallest
    width at which it returns anything at all.
    """
    lo, hi = 0.0, 1.0
    while not _pair_candidates(feather, scale, mode, hi):
        hi *= 2.0
        if hi > 1e5:
            raise ValueError(f"{feather.name}: no page width can hold this pair")
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if _pair_candidates(feather, scale, mode, mid):
            hi = mid
        else:
            lo = mid
    return hi


def settle_page_width(feathers: list, scale: float = 1.0, mode: str = "auto",
                      nominal: float = PAGE_WIDTH_MM) -> tuple:
    """(page width, explanation) that every pair in the document fits on.

    A logical page is 273 mm because that is what tiles well, not for its own sake.
    A source whose feathers are drawn a little broader can need more: the minified
    aggregate's P1 is 118.5 mm across, so its upright pair is 307 mm and nothing
    about spacing rescues it. Rather than fail, the document widens to the widest
    pair it holds -- which is a property of the source, not of one feather, so every
    page gets the same width and the geometry stays comparable between them.

    Returns the nominal width when everything already fits, so the common case is
    unchanged and byte-identical.
    """
    needed = max(minimum_page_width(f, scale, mode) for f in feathers)
    if needed <= nominal + 1e-9:
        return nominal, None
    width = math.ceil(needed * 10.0) / 10.0
    names = [f.name for f in feathers
             if minimum_page_width(f, scale, mode) > nominal + 1e-9]
    return width, (f"widened to {width:g} mm for {', '.join(names)} "
                   f"(the page is {nominal:g} mm unless a pair needs more)")
    """Decide how this feather's pair is laid on the page.

    ``auto`` takes the shortest page; headless and upright are usually far enough
    apart (S3: 88 mm of page height) that the choice is unambiguous, and where they
    are close it hardly matters.
    """
    candidates = _pair_candidates(feather, scale, mode)
    if not candidates:
        cut = feather.cut_box
        raise ValueError(
            f"{feather.name}: no pair layout fits the {PAGE_WIDTH_MM:g} mm page "
            f"(feather {cut[2] - cut[0]:.1f} x {cut[3] - cut[1]:.1f} mm across x "
            f"along, {MIN_PARTNER_GAP_MM:g} mm minimum partner gap)"
        )
    return min(candidates, key=lambda p: p.height_mm)


def is_headless(feather: Feather, mode: str = "auto") -> bool:
    """Whether this feather's pair is laid down a quarter turn (halves stacked)."""
    return pairing(feather, 1.0, mode).headless


def pair_size(feather: Feather, scale: float = 1.0, mode: str = "auto") -> tuple:
    """(width, height) of one mirrored pair's cell, in millimetres."""
    p = pairing(feather, scale, mode)
    return (p.width_mm, p.height_mm)


def make_slot(feather: Feather, cell_left: float, cell_width: float,
              pair_bottom: float, scale: float,
              headless: bool, gap: float) -> PairSlot:
    """Place one mirrored pair in its printed cell, with the halves held apart.

    Coordinates and sizes here are at PRINT size: `cell_left`, `cell_width`,
    `pair_bottom` and `gap` all come from the packing, which measured every cell
    before anything was placed. The caller also supplies `headless` rather than
    letting this function re-derive it -- re-deciding after the packing is exactly
    how the layout and the drawn geometry drift apart.

    The pair is built at true size inside its own cell and then shrunk onto the
    printed one, so `--scale` is a similarity transform away from the true-size pair
    and cannot pull a half off its cell or across the mirror axis.

    The source geometry is the feather as the aggregate draws it, straightened
    upright. Upright, the as-drawn half occupies the right-hand side of a vertical
    mirror axis and its reflection the left, `gap` clear of it. Headless the pair is
    turned a quarter turn: the as-drawn half sits below a horizontal axis and its
    reflection above, again `gap` clear of it.
    """
    cut = feather.cut_box
    across = cut[2] - cut[0]                # across the feather, at true size
    along = cut[3] - cut[1]                 # along the feather, at true size
    gap_true = gap                          # make_slot is handed the true-size gap
    gap_half = gap_true / 2.0
    true_x0 = cell_left / scale
    true_y0 = pair_bottom / scale

    if headless:
        # Each slot runs `along` across the page and `across` down it. Turn the
        # as-drawn half a quarter turn and stand its lower-left corner on the slot's.
        pair_h_true = 2.0 * across + gap_true
        cell_w_true = along
        turn = mat_rotate(90.0, (cut[0] + cut[2]) / 2.0, (cut[1] + cut[3]) / 2.0)
        turned = fit_bbox(cut, turn)
        right_to_true = mat_mul(
            mat_translate(true_x0 - turned[0], true_y0 - turned[1]), turn)
        axis_x_true = true_x0 + along / 2.0
        axis_y_true = true_y0 + pair_h_true / 2.0
        reflect = mat_mul(
            mat_mul(mat_translate(0.0, axis_y_true), mat_scale(1.0, -1.0)),
            mat_translate(0.0, -axis_y_true),
        )
    else:
        pair_h_true = along
        cell_w_true = 2.0 * across + gap_true
        axis_x_true = true_x0 + gap_half + across
        axis_y_true = true_y0 + pair_h_true / 2.0
        right_to_true = mat_fit(cut, axis_x_true + gap_half, true_y0)
        reflect = mat_mul(
            mat_mul(mat_translate(axis_x_true, 0.0), mat_scale(-1.0, 1.0)),
            mat_translate(-axis_x_true, 0.0),
        )
    left_to_true = mat_mul(reflect, right_to_true)

    # true-size cell -> printed cell: shrink about the true cell's corner, then move
    # that corner onto the printed cell's.
    shrink = mat_scale(scale, scale)
    offset = mat_translate(cell_left - true_x0 * scale, pair_bottom - true_y0 * scale)
    right_to_page = mat_mul(offset, mat_mul(shrink, right_to_true))
    left_to_page = mat_mul(offset, mat_mul(shrink, left_to_true))

    pair_h = pair_h_true * scale
    pair_top = pair_bottom + pair_h
    axis_x_value = axis_x_true * scale
    axis_y_value = axis_y_true * scale

    # The placed pair must land exactly on the cell the layout packed. A mistake in
    # composing these transforms is otherwise silent: the page simply draws the
    # template somewhere else, while the margins and spacing the layout worked out
    # describe a rectangle nothing occupies. Each half fills the cell across the
    # pair; along the pair it fills one slot of two, with `gap` between them.
    placed = fit_bbox(cut, right_to_page)
    want_y = (pair_bottom, pair_bottom + across * scale) if headless \
        else (pair_bottom, pair_top)
    if abs(placed[1] - want_y[0]) > 1e-6 or abs(placed[3] - want_y[1]) > 1e-6:
        raise AssertionError(
            f"{feather.name}: placed half spans y {placed[1]:.4f}..{placed[3]:.4f}, "
            f"cell wants {want_y[0]:.4f}..{want_y[1]:.4f}"
            + (f" (pair {pair_bottom:.4f}..{pair_top:.4f})" if headless else ""))
    if headless:
        want_x = (cell_left, cell_left + along * scale)
    else:
        want_x = (axis_x_value + gap_true * scale / 2.0,
                  axis_x_value + gap_true * scale / 2.0 + across * scale)
    if abs(placed[0] - want_x[0]) > 1e-6 or abs(placed[2] - want_x[1]) > 1e-6:
        raise AssertionError(
            f"{feather.name}: placed half spans x {placed[0]:.4f}..{placed[2]:.4f}, "
            f"cell wants {want_x[0]:.4f}..{want_x[1]:.4f}")

    return PairSlot(
        feather=feather,
        axis_x=axis_x_value,
        cell_left=cell_left,
        cell_right=cell_left + cell_width,
        pair_top=pair_top,
        pair_bottom=pair_bottom,
        label_y=pair_top + LABEL_GAP_MM,
        right_box=fit_bbox(cut, right_to_page),
        left_box=fit_bbox(cut, left_to_page),
        right_to_page=right_to_page,
        left_to_page=left_to_page,
        headless=headless,
        gap_mm=gap * scale,
    )


def row_gap(row: dict) -> float:
    """Clear space this row keeps from its neighbours."""
    return DENSE_GAP_MM if len(row["items"]) > 1 else SPARSE_GAP_MM


def _pack_rows(pairs: list) -> list:
    """Pack (key, width, height) pairs into rows, tallest-first (LPT)."""
    content_w = PAGE_WIDTH_MM - 2.0 * MIN_MARGIN_MM
    rows: list = []
    for key, width, height in sorted(pairs, key=lambda p: -p[2]):
        if width > content_w + 1e-9:
            raise ValueError(
                f"{key}: mirrored pair is {width:.2f} mm wide, which exceeds the "
                f"{content_w:.2f} mm printable width"
            )
        best = None
        for row in rows:
            needed = width + (DENSE_GAP_MM if row["items"] else 0.0)
            if row["width"] + needed <= content_w + 1e-9:
                if best is None or row["height"] < best["height"] - 1e-9:
                    best = row
        if best is None:
            best = {"items": [], "width": 0.0, "height": 0.0}
            rows.append(best)
        best["items"].append((key, width, height))
        best["width"] += width + (DENSE_GAP_MM if len(best["items"]) > 1 else 0.0)
        best["height"] = max(best["height"], height)

    order = {key: i for i, (key, _, _) in enumerate(pairs)}
    for row in rows:
        row["items"].sort(key=lambda item: order[item[0]])
        row["width"] = sum(w for _, w, _ in row["items"]) + DENSE_GAP_MM * (
            len(row["items"]) - 1
        )
    rows.sort(key=lambda row: order[row["items"][0][0]])
    return rows


def page_height_for_rows(rows: list) -> float:
    """Page height a list of packed rows would need, including its row gaps."""
    body_h = sum(LABEL_BAND_MM + row["height"] for row in rows)
    for upper, lower in zip(rows, rows[1:]):
        body_h += max(row_gap(upper), row_gap(lower))
    return max(HEAD_MM + body_h + FOOT_MM, MIN_PAGE_HEIGHT_MM)


def page_height_cap(group: str, max_page_h: float,
                    small_page_h: float | None = None) -> float:
    """The height budget for one family group, in millimetres.

    The small coverts are held to their own, much lower cap so their pages tile into
    a single row of sheets; the long feathers keep the global budget, because a
    single P or S pair is taller than any small cap could ever allow and the cap
    would simply be ignored for them. ``None`` means the small groups are not capped
    separately.
    """
    if small_page_h is None:
        return max_page_h
    # `group` is either one family or a merged group's title ("SC / PC / A").
    if group in SMALL_FAMILIES or group in SMALL_PAGE_GROUPS:
        return min(max_page_h, small_page_h)
    return max_page_h


def split_rows_by_height(rows: list, max_page_h: float,
                         max_rows: int | None = None) -> list:
    """Split packed rows into pages, balanced in height and within the budget.

    A greedy fill knocks the last page down to a single row whenever the total is
    not a clean multiple of the budget, which wastes a sheet for one pair. This
    instead works out how many pages the rows need, then splits them as evenly as
    possible, so the sheets come out close to the same length.

    A single row taller than the budget still gets its own chunk, so an exceptionally
    long pair can never prevent the document from being built.
    """
    row_count = len(rows)
    if row_count == 0:
        return []
    if max_rows is not None:
        return [rows[i: i + max_rows] for i in range(0, row_count, max_rows)]

    pages = 1
    while pages < row_count:
        size = row_count / pages
        fits = True
        for i in range(pages):
            start = round(i * size)
            end = round((i + 1) * size)
            if page_height_for_rows(rows[start:end]) > max_page_h + 1e-9:
                fits = False
                break
        if fits:
            break
        pages += 1

    size = row_count / pages
    chunks = []
    for i in range(pages):
        start = round(i * size)
        end = round((i + 1) * size)
        if end > start:
            chunks.append(rows[start:end])
    return chunks


def plan_pages(feathers: list, scale: float = 1.0,
               max_page_h: float = MAX_PAGE_HEIGHT_MM,
               max_rows: int | None = None, mode: str = "auto",
               small_page_h: float | None = SMALL_PAGE_HEIGHT_MM) -> list:
    """Group feathers into logical pages, packing several pairs per page.

    Feathers are grouped by family (the leading letters of the ID), with `GROUP_JOIN`
    merging the families that share a page, and each group is split against its own
    height budget -- see ``page_height_cap``.
    """
    groups: dict = {}
    for feather in feathers:
        groups.setdefault(family_of(feather.name), []).append(feather)

    pages: list = []
    for key, members in groups.items():
        rows = _pack_rows([(f.name, *pair_size(f, scale, mode)) for f in members])
        by_name = {f.name: f for f in members}
        # A merged group may be a tuple of families ('SC', 'PC', 'A'); a single one is
        # just its string. `page_height_cap` and the page title both want the string.
        group = group_title(key)
        cap = page_height_cap(group, max_page_h, small_page_h)
        for chunk in split_rows_by_height(rows, cap, max_rows):
            pages.append((group, chunk, by_name))
    return pages


def layout_page(title: str, rows: list, by_name: dict, scale: float,
                mode: str = "auto") -> PageLayout:
    """Give a page's packed rows concrete coordinates and build its slots."""
    if not rows:
        raise ValueError("a page needs at least one row")

    # One pairing per feather on this page, decided the same way plan_pages decided
    # the cell sizes that were packed.
    pairs = [key for row in rows for key, _, _ in row["items"]]
    pairings = {key: pairing(by_name[key], scale, mode) for key in pairs}

    page_h = page_height_for_rows(rows)
    widest_row = max(
        sum(w for _, w, _ in row["items"]) + DENSE_GAP_MM * (len(row["items"]) - 1)
        for row in rows
    )
    margin = max(MIN_MARGIN_MM,
                 min(MARGIN_MM, (PAGE_WIDTH_MM - widest_row) / 2.0))
    content_w = PAGE_WIDTH_MM - 2.0 * margin
    body_h = page_h - HEAD_MM - FOOT_MM

    slots: list = []
    row_bottom = page_h - HEAD_MM - body_h
    n_rows = len(rows)
    for index, row in enumerate(reversed(rows)):
        row_width = sum(w for _, w, _ in row["items"]) + DENSE_GAP_MM * (
            len(row["items"]) - 1
        )
        x = margin + (content_w - row_width) / 2.0
        for key, width, height in row["items"]:
            # The packed cell is already at print size, so its width passes straight
            # through, as does the gap. The pairing was decided once, in plan_pages;
            # re-deriving it here is how the packing and the geometry drift apart.
            plan = pairings[key]
            slot = make_slot(by_name[key], x, width, row_bottom + LABEL_BAND_MM,
                             scale, plan.headless, plan.gap_mm)
            slots.append(slot)
            x += width + DENSE_GAP_MM
        row_bottom += LABEL_BAND_MM + row["height"]
        if index != n_rows - 1:
            upper = rows[n_rows - 2 - index]
            row_bottom += max(row_gap(row), row_gap(upper))

    return PageLayout(
        page_w=PAGE_WIDTH_MM,
        page_h=page_h,
        slots=slots,
        title=title,
        stroke_scale=scale,
        margin=margin,
        group=by_name[pairs[0]].group if pairs else "",
    )


def slot_labels(slot: PairSlot) -> list:
    """(text, x, y, align) for the feather ID above each half of a pair."""
    y = slot.label_y
    if not slot.headless:
        inset = slot.axis_x - slot.cell_left
        return [
            (f"{slot.name} L", slot.axis_x - inset, y, "left"),
            (f"{slot.name} R", slot.axis_x + inset, y, "right"),
        ]
    return [
        (f"{slot.name} L", slot.cell_left, y, "left"),
        (f"{slot.name} R", slot.cell_right, y, "right"),
    ]


def slot_axis_ticks(slot: PairSlot) -> list:
    """The two dashed ticks marking a pair's mirror axis, as ((x0,y0),(x1,y1))."""
    if not slot.headless:
        return [
            ((slot.axis_x, slot.pair_bottom - 5.0), (slot.axis_x, slot.pair_bottom)),
            ((slot.axis_x, slot.pair_top), (slot.axis_x, slot.pair_top + 5.0)),
        ]
    axis_y = slot.axis_y
    return [
        ((slot.cell_left - 5.0, axis_y), (slot.cell_left, axis_y)),
        ((slot.cell_right, axis_y), (slot.cell_right + 5.0, axis_y)),
    ]


def compute_layout_geometry(layout: PageLayout) -> str:
    """The drawing section of a page: CTMs, mirror-axis ticks and the geometry.

    Kept separate from the text furniture so a verifier can rebuild exactly this part
    and compare it against what the writer emitted.
    """
    cmds: list = [
        "1 0 0 1 0 0 cm",
        f"{num(PT_PER_MM)} 0 0 {num(PT_PER_MM)} 0 0 cm",
    ]

    cmds.append(f"{rgb(GUIDE_GREY)} RG {num(0.25)} w [2 2] 0 d")
    for slot in layout.slots:
        (x0, y0), (x1, y1) = slot_axis_ticks(slot)[0]
        cmds.append(f"{num(x0)} {num(y0)} m {num(x1)} {num(y1)} l S")
    cmds.append("[] 0 d")

    # Draw each half from the single set of as-drawn outlines: the as-drawn half on
    # one side of the axis, its reflection on the other.
    for slot in layout.slots:
        stroke = slot.feather.stroke_mm * layout.stroke_scale
        for to_page in (slot.left_to_page, slot.right_to_page):
            geometry = path_cmd(transform_polys(slot.feather.polys_right, to_page))
            # 1. halo stroke in the fill colour rounds the fill edge off under the cut line
            cmds.append(f"{rgb(HALF_FILL)} RG {num(stroke)} w")
            cmds.append(geometry)
            cmds.append("S")
            # 2. paper-coloured fill so the cut line reads clearly
            cmds.append(f"{rgb((1, 1, 1))} rg")
            cmds.append(geometry)
            cmds.append("f")
            # 3. the cut line itself
            cmds.append(f"{rgb((0, 0, 0))} RG {num(stroke)} w")
            cmds.append("1 J 1 j")
            cmds.append(geometry)
            cmds.append("S")

    # The quill centre line is deliberately NOT drawn. The aggregate's guides are
    # read (they say which end of a feather is the base, see ``upright_matrix``) but
    # they are presentation, not template: a dashed line down every feather invites
    # scoring or creasing along it, and the cut outline is the only thing this
    # document is for.

    # Second axis ticks, over the geometry so the mirror axis stays visible.
    cmds.append(f"{rgb(GUIDE_GREY)} RG {num(0.25)} w [2 2] 0 d")
    for slot in layout.slots:
        (x0, y0), (x1, y1) = slot_axis_ticks(slot)[1]
        cmds.append(f"{num(x0)} {num(y0)} m {num(x1)} {num(y1)} l S")
    cmds.append("[] 0 d")
    return "\n".join(cmds)


def footer_pair_line(layout: PageLayout) -> str:
    """The footer line listing a page's pairs, as drawn."""
    return (f"{len(layout.slots)} pair(s): "
            + " ".join(slot.name for slot in layout.slots)
            + "   (mm, stroke centreline)")


def _check_text_fits(layout: PageLayout, scale: float) -> None:
    """Fail loudly rather than emit a header or footer that runs off the page."""
    usable = layout.page_w - 2.0 * layout.margin
    scale_note = "1:1" if scale == 1.0 else f"1:{1.0 / scale:.1f} reduced"
    header = f"{layout.title}  -  mirrored pairs  ({scale_note})"
    header_w = text_width_mm(header, ID_SIZE_MM)
    if header_w > usable:
        raise ValueError(
            f"header {header_w:.1f} mm is wider than the {usable:.1f} mm content area")
    footer = footer_pair_line(layout)
    footer_w = text_width_mm(footer, FOOT_SIZE_MM)
    if footer_w > usable:
        raise ValueError(
            f"footer listing {len(layout.slots)} pairs is {footer_w:.1f} mm wide, "
            f"wider than the {usable:.1f} mm content area")


def build_page(layout: PageLayout, page_no: int, page_total: int,
               generated: str, scale: float) -> str:
    cmds: list = [compute_layout_geometry(layout)]

    for slot in layout.slots:
        for text, x, y, align in slot_labels(slot):
            cmds.append(text_cmd(x, y, LABEL_SIZE_MM, text, color=(0, 0, 0),
                                 align=align))

    scale_note = "1:1" if scale == 1.0 else f"1:{1.0 / scale:.1f} reduced"
    header = f"{layout.title}  -  mirrored pairs  ({scale_note})"
    subtitle = "aggregate geometry, straightened and mirrored about each centre line"
    header_y = layout.page_h - MARGIN_TOP_MM - ID_SIZE_MM
    cmds.append(text_cmd(layout.page_w / 2.0, header_y, ID_SIZE_MM,
                         header, color=(0, 0, 0), align="center"))
    cmds.append(text_cmd(layout.page_w / 2.0, header_y - 4.6,
                         FOOT_SIZE_MM, subtitle, color=TEXT_GREY, align="center"))

    bar_y = MARGIN_BOTTOM_MM + 3.0
    bar_x = MARGIN_MM
    if scale == 1.0:
        cmds.append(f"{rgb((0, 0, 0))} RG {num(0.3)} w")
        cmds.append(f"{num(bar_x)} {num(bar_y)} m {num(bar_x + SCALE_BAR_MM)} {num(bar_y)} l S")
        for x in (bar_x, bar_x + SCALE_BAR_MM):
            cmds.append(f"{num(x)} {num(bar_y)} m {num(x)} {num(bar_y + 2.5)} l S")
        bar_note = f"{num(SCALE_BAR_MM)} mm - verify before cutting"
    else:
        bar_note = (f"reduced print: 1 mm here = {num(1.0 / scale, 2)} mm actual - "
                    f"not full size")
    cmds.append(text_cmd(bar_x, bar_y - 0.8, FOOT_SIZE_MM,
                         bar_note, color=TEXT_GREY))
    cmds.append(text_cmd(layout.page_w - MARGIN_MM, bar_y - 0.8, FOOT_SIZE_MM,
                         f"page {page_no} of {page_total}   generated {generated}",
                         color=TEXT_GREY, align="right"))
    _check_text_fits(layout, scale)
    cmds.append(text_cmd(layout.page_w / 2.0, bar_y + 4.6, FOOT_SIZE_MM,
                         footer_pair_line(layout), color=TEXT_GREY, align="center"))
    return "\n".join(cmds)


# ---------------------------------------------------------------------------
# document assembly
# ---------------------------------------------------------------------------
def build_stamp() -> tuple:
    """(footer date, PDF CreationDate) for this build.

    Honours SOURCE_DATE_EPOCH so a rebuild is byte-identical: otherwise every build
    differs only in its timestamp, which makes it impossible to tell a real content
    change from a rebuild by comparing the files.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.strip().isdigit():
        when = dt.datetime.fromtimestamp(int(epoch), tz=dt.timezone.utc).astimezone()
    else:
        when = dt.datetime.now().astimezone()
    return when.date().isoformat(), when.strftime("D:%Y%m%d%H%M%S%z")


class PdfDocument:
    """Multi-page PDF with per-page point dimensions.

    Pages may be plain (each carrying its own content stream) or tiles that draw a
    shared form XObject. Forms are emitted before the pages that reference them, so
    their object numbers are known when a page dictionary is written.
    """

    def __init__(self, title: str) -> None:
        self.pages: list = []
        self.forms: list = []
        self.tile_pages: list = []
        self.metadata = {
            "Title": title,
            "Creator": "tools/make_feather_template_pdf_from_aggregate.py (wings-pcbs)",
            "Producer": "wings-pcbs aggregate template generator",
            "CreationDate": build_stamp()[1],
        }

    def add_page(self, width_mm: float, height_mm: float, content: str) -> None:
        self.pages.append((width_mm, height_mm, content))

    def add_form(self, width_mm: float, height_mm: float, content: str) -> int:
        self.forms.append((width_mm, height_mm, content))
        return len(self.forms) - 1

    def add_tile_page(self, width_mm: float, height_mm: float, content: str,
                      used_forms: list) -> None:
        """Add a sheet page that draws each form in `used_forms` by its /F name.

        A sheet can hold more than one logical page, so a page's resources have to
        name every form it draws, not just one.
        """
        self.tile_pages.append((width_mm, height_mm, content, used_forms))

    def build(self) -> bytes:
        objects: list = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        font_obj = add(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        )
        pages_obj = add(b"")
        info_obj = add(b"")
        catalog_obj = add(b"")

        form_obj_nums: list = []
        for width_mm, height_mm, content in self.forms:
            packed = zlib.compress(content.encode("ascii"), 9)
            form_obj_nums.append(add(
                b"<< /Type /XObject /Subtype /Form "
                b"/BBox [0 0 %s %s] /Matrix [1 0 0 1 0 0] "
                b"/Resources << /Font << /F1 %d 0 R >> >> "
                b"/Length %d /Filter /FlateDecode >>\nstream\n"
                % (
                    num(width_mm * PT_PER_MM).encode(),
                    num(height_mm * PT_PER_MM).encode(),
                    font_obj,
                    len(packed),
                )
                + packed
                + b"\nendstream"
            ))

        def emit_page(width_mm: float, height_mm: float, content: str,
                      extra_resources: bytes) -> int:
            packed = zlib.compress(content.encode("ascii"), 9)
            content_obj = add(
                b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(packed)
                + packed
                + b"\nendstream"
            )
            return add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] "
                b"/Resources << /Font << /F1 %d 0 R >>%s >> /Contents %d 0 R >>"
                % (
                    pages_obj,
                    num(width_mm * PT_PER_MM).encode(),
                    num(height_mm * PT_PER_MM).encode(),
                    font_obj,
                    extra_resources,
                    content_obj,
                )
            )

        page_objs: list = []
        for width_mm, height_mm, content in self.pages:
            page_objs.append(emit_page(width_mm, height_mm, content, b""))
        for width_mm, height_mm, content, used_forms in self.tile_pages:
            entries = b" ".join(
                b"/F%d %d 0 R" % (index, form_obj_nums[index])
                for index in sorted(set(used_forms))
            )
            xobjects = b" /XObject << " + entries + b" >>"
            page_objs.append(emit_page(width_mm, height_mm, content, xobjects))

        kids = b" ".join(b"%d 0 R" % n for n in page_objs)
        objects[pages_obj - 1] = b"<< /Type /Pages /Count %d /Kids [%s] >>" % (
            len(page_objs),
            kids,
        )
        info_parts = [b"<<"]
        for key, value in self.metadata.items():
            info_parts.append(b" /%s (%s)" % (key.encode(), pdf_string(value).encode()))
        info_parts.append(b" >>")
        objects[info_obj - 1] = b"".join(info_parts)
        objects[catalog_obj - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj

        out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0] * (len(objects) + 1)
        for i, body in enumerate(objects, start=1):
            offsets[i] = len(out)
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref_pos = len(out)
        out += b"xref\n0 %d\n" % (len(objects) + 1)
        out += b"0000000000 65535 f \n"
        for i in range(1, len(objects) + 1):
            out += b"%010d 00000 n \n" % offsets[i]
        out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objects) + 1,
            catalog_obj,
            info_obj,
            xref_pos,
        )
        return bytes(out)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.build())


# ---------------------------------------------------------------------------
# paper parsing + tiling (poster mode)
# ---------------------------------------------------------------------------
def tile_paper(spec: str) -> tuple:
    """Resolve a paper-size spec to (label, portrait width mm, portrait height mm).

    ``8.5x11`` and ``letter`` are the same sheet, and both spellings are accepted
    because both get used out loud; ``a4`` is the other. Punctuation is ignored, so
    the dot in ``8.5x11`` does not have to be remembered or escaped.
    """
    key = re.sub(r"[^a-z0-9]", "", spec.strip().lower())
    if key not in TILE_PAPER_SIZES:
        raise ValueError(
            f"paper size must be {TILE_PAPER_NAMES.replace('|', ' or ')} "
            f"(letter is accepted for 8.5x11), got {spec!r}"
        )
    return TILE_PAPER_SIZES[key]


@dataclass
class Tile:
    """One logical page placed on one physical sheet."""

    sheet_no: int     # 1-based sheet, in the order sheets are built
    page_no: int      # 1-based logical page
    page_total: int
    x0: float         # sheet mm of the logical page's lower-left corner
    y0: float
    tiled: bool = False    # the page is bigger than a sheet and gets crop marks


@dataclass
class SheetPlan:
    paper_label: str
    paper_w: float    # landscape sheet extents, mm
    paper_h: float
    margin: float
    overlap: float
    sheet_total: int
    tiles: list           # one entry per (sheet, logical page) placement


def tile_rows(page_h: float, ph: float, overlap: float) -> int:
    """How many overlapping landscape sheets tall a page takes."""
    if page_h <= ph + 1e-9:
        return 1
    stride_y = ph - overlap
    return int(math.ceil((page_h - ph) / stride_y - 1e-9)) + 1


def sheet_fits_whole(page_w: float, page_h: float, pw: float, ph: float) -> bool:
    """Whether a logical page fits one landscape sheet uncut."""
    return page_w <= pw + 1e-9 and page_h <= ph + 1e-9


def tile_grid(page_w: float, page_h: float, pw: float, ph: float,
              overlap: float) -> tuple:
    """(columns, rows) a logical page needs, in landscape sheets.

    **One column whenever one column can hold it**, which is the intended case: a
    logical page is 273-277 mm, a landscape 8.5x11 sheet prints 269.4 mm of width and
    A4 prints 287, so a page that fits a sheet whole tiles straight down a column of
    sheets with the overlap trimmed at each join.

    A page *wider* than the printable width cannot be covered by one column -- the
    right-hand strip would print nowhere -- so it falls back to as many columns as it
    takes. Silently dropping that strip would lose the edge of a template, and
    scaling the page down instead would print it at the wrong size.
    """
    stride_x = pw - overlap
    stride_y = ph - overlap
    cols = 1 if page_w <= pw + 1e-9 \
        else int(math.ceil((page_w - pw) / stride_x - 1e-9)) + 1
    rows = tile_rows(page_h, ph, overlap)
    return cols, rows


def plan_sheets(layouts: list, paper_w: float, paper_h: float,
                margin: float, overlap: float, paper_label: str,
                gap: float = 6.0) -> SheetPlan:
    """Precalculate every physical sheet: which logical pages go on it, and where.

    The sheet is always used in landscape, so the given portrait dimensions are
    swapped before the printable area is worked out.

    A logical page that fits the printable area whole is placed on ONE sheet and
    nothing is cut -- no grid, no overlap, no crop marks. That is the common case
    here and it is what the small-feather caps exist for: with the small groups held
    to their own page height, most of their pages are single sheets. A page too big
    for one sheet is tiled across the overlapping grid ``tile_grid`` works out, and
    those sheets carry crop marks.

    Fill order is first-fit: a page goes on the earliest sheet whose free strip is
    tall enough. Pages come in family order, so a sheet tends to hold one family's
    small pages and stay readable. Pages are never rotated: one is portrait or it is
    not, and rotating to fit would put the title and footer on their side.

    Everything here is millimetres, and the whole plan is worked out before a single
    tile is drawn, so the sheet count and every placement are known up front.
    """
    paper_w, paper_h = paper_h, paper_w       # landscape
    pw = paper_w - 2.0 * margin
    ph = paper_h - 2.0 * margin
    if pw <= 0 or ph <= 0:
        raise ValueError(
            f"margin {margin:g} mm leaves no printable area on "
            f"{paper_label} landscape"
        )
    if overlap < 0:
        raise ValueError("tile overlap cannot be negative")
    if overlap >= pw or overlap >= ph:
        raise ValueError(
            f"overlap {overlap:g} mm must be smaller than the printable area "
            f"{pw:g} x {ph:g} mm of {paper_label} landscape"
        )
    if gap < 0:
        raise ValueError("tile gap cannot be negative")

    tiles: list = []
    # Per sheet, the rectangles already spoken for. A page is placed on the first
    # sheet where its own rectangle overlaps none of them -- which lets a small page
    # sit above or beside a tiled page's first sheet rather than wasting it.
    used: list = []

    def free_spot(index: int, x: float, y: float, w: float, h: float) -> bool:
        if x < -1e-9 or y < -1e-9 or x + w > pw + 1e-9 or y + h > ph + 1e-9:
            return False
        if index == len(used):
            return True                      # a sheet that does not exist yet is empty
        for ux, uy, uw, uh in used[index]:
            if not (x + w <= ux + 1e-9 or ux + uw <= x + 1e-9
                    or y + h <= uy + 1e-9 or uy + uh <= y + 1e-9):
                return False
        return True

    def place_whole(page_no: int, layout) -> bool:
        """Put the page on the first sheet it fits on whole, or start a new sheet.

        Worth a real search rather than a stack: on A4 landscape two of the small
        coverts' pages fit on one sheet, and a page this size is centred, so the only
        candidate positions are the bottom and each existing rectangle's top edge.

        A page wider than the printable area is refused outright: it is going to be
        cut along a join, not placed on one sheet, and `free_spot` alone only guards
        the position it is asked about.
        """
        if layout.page_w > pw + 1e-9 or layout.page_h > ph + 1e-9:
            return False
        x = (pw - layout.page_w) / 2.0
        for index in range(len(used) + 1):
            if index == len(used):
                if free_spot(index, x, 0.0, layout.page_w, layout.page_h):
                    used.append([(x, 0.0, layout.page_w, layout.page_h)])
                    tiles.append(Tile(index + 1, page_no, len(layouts),
                                      x0=x, y0=0.0))
                    return True
                return False
            candidates = {0.0}
            for _ux, uy, _uw, uh in used[index]:
                candidates.add(uy + uh + gap)
            for y in sorted(candidates):
                if free_spot(index, x, y, layout.page_w, layout.page_h):
                    used[index].append((x, y, layout.page_w, layout.page_h))
                    tiles.append(Tile(index + 1, page_no, len(layouts),
                                      x0=x, y0=y))
                    return True
        return False

    def place_grid(page_no: int, cols: int, rows: int) -> None:
        """Lay the page down `cols` x `rows` overlapping landscape sheets.

        One column is the intended case (see ``tile_grid``): each sheet takes the
        full printable width, `x0` is 0, and the page walks up `stride_y` per sheet
        with `overlap` shared between neighbours. A second column only appears when
        the page is wider than a sheet can print, and then `x0` walks across too.

        A tiled page prefers the first sheet that has the whole printable area free,
        so it can start on a sheet a whole page already sits under.
        """
        stride_x = pw - overlap
        stride_y = ph - overlap
        for iy in range(rows):
            for ix in range(cols):
                if ix == 0 and iy == 0 and used:
                    for index in range(len(used)):
                        if free_spot(index, 0.0, 0.0, pw, ph):
                            used[index].append((0.0, 0.0, pw, ph))
                            tiles.append(Tile(index + 1, page_no, len(layouts),
                                              x0=0.0, y0=0.0, tiled=True))
                            break
                    else:
                        used.append([(0.0, 0.0, pw, ph)])
                        tiles.append(Tile(len(used), page_no, len(layouts),
                                          x0=0.0, y0=0.0, tiled=True))
                    continue
                used.append([(0.0, 0.0, pw, ph)])
                tiles.append(Tile(len(used), page_no, len(layouts),
                                  x0=ix * stride_x, y0=iy * stride_y, tiled=True))

    for page_no, layout in enumerate(layouts, start=1):
        # A page that fits a landscape sheet whole is printed natively: one sheet,
        # centred, nothing cut, no crop marks. That is the whole point of the small
        # coverts' page cap.
        if place_whole(page_no, layout):
            continue
        cols, rows = tile_grid(layout.page_w, layout.page_h, pw, ph, overlap)
        if cols == 1 and rows == 1:
            # No sheet would take it, yet it is no bigger than one -- give it its own.
            used.append([(0.0, 0.0, pw, ph)])
            tiles.append(Tile(len(used), page_no, len(layouts),
                              x0=(pw - layout.page_w) / 2.0, y0=0.0))
            continue
        place_grid(page_no, cols, rows)

    return SheetPlan(paper_label, paper_w, paper_h, margin, overlap,
                     len(used), tiles)


def tiles_on_sheet(plan: SheetPlan, sheet_no: int) -> list:
    return [t for t in plan.tiles if t.sheet_no == sheet_no]


def tiling_note(plan: SheetPlan, layouts: list) -> str:
    """A sentence about how the sheets came out, or "" when it is the plain case.

    Worth saying out loud when a page needs more than one column, because that means
    the paper is narrower than the page: the template survives (the columns cover it)
    but it is cut along a vertical join as well as the horizontal ones, which is not
    the single-column print the small pages get.
    """
    pw = plan.paper_w - 2.0 * plan.margin
    wide = [i for i, L in enumerate(layouts, start=1)
            if L.page_w > pw + 1e-9]
    if not wide:
        return ""
    return (f"{len(wide)} page(s) are wider than {plan.paper_label} landscape can "
            f"print ({pw:g} mm against {layouts[wide[0] - 1].page_w:g} mm), so they "
            f"tile across two columns as well as down: page(s) "
            + ", ".join(str(i) for i in wide[:6])
            + ("..." if len(wide) > 6 else "")
            + ". Use a wider sheet or --scale to keep it to one column.")


def _crop_marks(mx: float, my: float, pw: float, ph: float,
                margin_mm: float) -> list:
    """Corner crop marks just outside the printable area, sized to the margin."""
    if margin_mm <= 0.6:
        return []
    gap = min(1.5, margin_mm * 0.35)
    length = min(4.0, margin_mm - gap)
    if length <= 0.05:
        return []
    g = gap * PT_PER_MM
    ln = length * PT_PER_MM
    cmds = [f"{rgb(GUIDE_GREY)} RG {num(0.25 * PT_PER_MM, 2)} w"]
    for cx, hx in ((mx, -1), (mx + pw, 1)):
        for cy, hy in ((my, -1), (my + ph, 1)):
            cmds.append(
                f"{num(cx + hx * g)} {num(cy)} m "
                f"{num(cx + hx * (g + ln))} {num(cy)} l S"
            )
            cmds.append(
                f"{num(cx)} {num(cy + hy * g)} m "
                f"{num(cx)} {num(cy + hy * (g + ln))} l S"
            )
    return cmds


def _sheet_labels(sheet_no: int, sheet_tiles: list, plan: SheetPlan,
                  mx: float, my: float, pw: float, ph: float,
                  paper_w: float, paper_h: float) -> list:
    """Sheet identity and assembly notes, drawn in the sheet margins."""
    if plan.margin < 3.0:
        return []
    size = 6.0
    pages = sorted({t.page_no for t in sheet_tiles})
    total = sheet_tiles[0].page_total
    tiled = [t for t in sheet_tiles if t.tiled]
    if len(pages) > 1:
        head = (f"sheet {sheet_no} of {plan.sheet_total} - "
                + "page " + (f"{pages[0]} of {total}" if len(pages) == 1
                             else "/".join(str(p) for p in pages)))
        foot_l = f"{plan.paper_label} landscape - {len(pages)} pages"
        foot_r = "true scale - verify the 50 mm bar"
    elif tiled:
        # Which cell of the page's grid this sheet is. The grid comes from every tile
        # of that page, not just the ones on this sheet -- a sheet holds one cell, so
        # its own tile alone would always look like "1,1 of 1,1".
        here = sheet_tiles[0]
        grid = [t for t in plan.tiles if t.page_no == here.page_no]
        cols = sorted({round(t.x0, 3) for t in grid})
        rows = sorted({round(t.y0, 3) for t in grid}, reverse=True)
        head = (f"sheet {sheet_no} of {plan.sheet_total} - "
                f"page {here.page_no} of {total} - "
                f"tile {cols.index(round(here.x0, 3)) + 1},"
                f"{rows.index(round(here.y0, 3)) + 1} "
                f"of {len(cols)},{len(rows)}")
        foot_l = f"{plan.paper_label} landscape - overlap {num(plan.overlap, 1)} mm"
        foot_r = "cut on corner marks"
    else:
        head = (f"sheet {sheet_no} of {plan.sheet_total} - "
                f"page {pages[0]} of {total}")
        foot_l = f"{plan.paper_label} landscape"
        foot_r = "true scale - verify the 50 mm bar"
    top_y = (my + ph + paper_h) / 2.0 - 2.0
    bot_y = my / 2.0 - 2.0
    return [
        text_cmd(paper_w / 2.0, top_y, size, head, color=TEXT_GREY, align="center"),
        text_cmd(mx, bot_y, size, foot_l, color=TEXT_GREY),
        text_cmd(mx + pw, bot_y, size, foot_r, color=TEXT_GREY, align="right"),
    ]


def build_sheet_content(sheet_no: int, plan: SheetPlan, form_names: dict,
                        pt: float) -> str:
    """Content stream for one sheet: every page placed on it, clipped to the margin.

    Each logical page is drawn by referencing its form, slid so the part of it that
    belongs on this sheet lands in the printable area. A page placed whole is
    centred; a tiled page is one cell of its grid, and only tiled sheets get crop
    marks. `form_names` maps a logical page number to the /F name of its form.
    """
    mx = plan.margin * pt
    my = plan.margin * pt
    pw = (plan.paper_w - 2.0 * plan.margin) * pt
    ph = (plan.paper_h - 2.0 * plan.margin) * pt
    paper_w = plan.paper_w * pt
    paper_h = plan.paper_h * pt
    sheet_tiles = tiles_on_sheet(plan, sheet_no)
    if not sheet_tiles:
        raise ValueError(f"sheet {sheet_no} has no pages")

    # Sheet space is y-up from the printable area's lower-left, and so is page space,
    # so `y0` is used directly. Every form is drawn inside its own q/Q: a form's
    # content must not leak graphics state into the next page's placement.
    cmds: list = [
        "q",
        f"{num(mx)} {num(my)} {num(pw)} {num(ph)} re W n",
        f"1 0 0 1 {num(mx)} {num(my)} cm",
    ]
    for tile in sheet_tiles:
        cmds.append("q")
        cmds.append(f"1 0 0 1 {num(-tile.x0 * pt)} {num(-tile.y0 * pt)} cm")
        cmds.append(f"{form_names[tile.page_no]} Do")
        cmds.append("Q")
    cmds.append("Q")

    if any(t.tiled for t in sheet_tiles):
        cmds.extend(_crop_marks(mx, my, pw, ph, plan.margin))
    cmds.extend(_sheet_labels(sheet_no, sheet_tiles, plan, mx, my, pw, ph,
                              paper_w, paper_h))
    return "\n".join(cmds)


def build_tiled_document(layouts: list, plan: SheetPlan, generated: str,
                         scale: float) -> PdfDocument:
    """Assemble a tiled PDF.

    Identical logical pages share ONE form XObject: pages split from the same family
    with the same rows are the same drawing, and the tile form of a small group is a
    page after page of the same group's pairs. Text differs between pages, though --
    the footer carries the page number -- so a form is only shared when the whole
    rendered page is equal, not merely its geometry.
    """
    doc = PdfDocument(
        f"Feather templates from the aggregate - tiled for {plan.paper_label} landscape"
    )
    form_of: dict = {}
    by_content: dict = {}
    for page_no, layout in enumerate(layouts, start=1):
        content = build_page(layout, page_no, len(layouts), generated, scale)
        if content in by_content:
            form_of[page_no] = by_content[content]
        else:
            index = doc.add_form(layout.page_w, layout.page_h, content)
            by_content[content] = index
            form_of[page_no] = index
    for sheet_no in range(1, plan.sheet_total + 1):
        sheet_tiles = tiles_on_sheet(plan, sheet_no)
        form_names = {p: f"/F{index}" for p, index in form_of.items()}
        doc.add_tile_page(
            plan.paper_w, plan.paper_h,
            build_sheet_content(sheet_no, plan, form_names, PT_PER_MM),
            [form_of[t.page_no] for t in sheet_tiles],
        )
    return doc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    global DENSE_GAP_MM, SPARSE_GAP_MM, PAGE_WIDTH_MM

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregate", "--src", dest="aggregate", type=Path,
                    default=DEFAULT_SRC,
                    help=f"the aggregate SVG to read (default {DEFAULT_SRC})")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output PDF path")
    ap.add_argument("--only", nargs="+", metavar="ID", help="restrict to these feather IDs")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="uniform print scale (1.0 = true size; 0.5 = half size)")
    ap.add_argument("--list", action="store_true",
                    help="list the pages that would be generated")
    ap.add_argument("--geometry-report", action="store_true",
                    help="list each feather's aggregate size, turn applied and pair "
                         "orientation")
    ap.add_argument(
        "--pair-orientation", choices=("auto", "upright", "headless"), default="auto",
        help="how a pair is laid on the page: 'headless' turns it a quarter turn so "
             "the halves stack (shortest page height), 'upright' keeps them side by "
             "side, 'auto' (default) picks per feather by page height",
    )
    ap.add_argument(
        "--max-page-height", type=float, default=MAX_PAGE_HEIGHT_MM, metavar="MM",
        help=f"fill each logical page up to about this height (default "
             f"{MAX_PAGE_HEIGHT_MM:.0f} mm)",
    )
    ap.add_argument(
        "--small-page-height", default=SMALL_PAGE_HEIGHT_MM, metavar="MM",
        help=f"hold the small coverts ({'/'.join(SMALL_FAMILIES)}) to this much "
             f"shorter pages, so they tile into a single row of sheets (default "
             f"{SMALL_PAGE_HEIGHT_MM:.0f} mm); 'none' or 0 to lift the cap",
    )
    ap.add_argument("--max-rows", type=int, default=None, metavar="N",
                    help="also cap the rows stacked on one logical page")
    ap.add_argument("--spacing", type=float, default=None, metavar="MM",
                    help=f"clear space between pairs sharing a row (default "
                         f"{DENSE_GAP_MM:g} mm; a lone pair keeps "
                         f"{SPARSE_GAP_MM:g} mm from its neighbours)")
    ap.add_argument(
        "--tile-paper", metavar=TILE_PAPER_NAMES, default=None,
        help="precalculate every physical sheet as a landscape "
             f"{TILE_PAPER_NAMES.replace('|', ' or ')} and place the logical pages on "
             "them, instead of emitting poster-sized pages. A page that fits one "
             "sheet is printed natively and uncut; a larger page is tiled down a "
             "single column of sheets",
    )
    ap.add_argument("--tile-margin", type=float, default=TILE_MARGIN_MM, metavar="MM",
                    help=f"non-printable margin kept clear on every sheet "
                         f"(default {TILE_MARGIN_MM:g} mm)")
    ap.add_argument("--tile-overlap", type=float, default=TILE_OVERLAP_MM, metavar="MM",
                    help=f"overlap between adjacent tiles (default "
                         f"{TILE_OVERLAP_MM:g} mm)")
    ap.add_argument("--tile-gap", type=float, default=TILE_GAP_MM, metavar="MM",
                    help=f"clear space between two pages sharing one sheet "
                         f"(default {TILE_GAP_MM:g} mm)")
    ap.add_argument(
        "--page-width", type=float, default=None, metavar="MM",
        help=f"nominal logical page width (default {PAGE_WIDTH_MM:g} mm). A source "
             f"whose pairs need more widens the document to the widest of them, since "
             f"a pair that does not fit cannot be cut; pass a value to set it "
             f"yourself",
    )
    args = ap.parse_args(argv)

    if args.spacing is not None:
        if args.spacing < 0:
            raise SystemExit("--spacing cannot be negative")
        DENSE_GAP_MM = args.spacing
        SPARSE_GAP_MM = max(SPARSE_GAP_MM, args.spacing)
    if args.max_rows is not None and args.max_rows < 1:
        raise SystemExit("--max-rows must be at least 1")
    if args.max_page_height <= 0:
        raise SystemExit("--max-page-height must be positive")
    small_page_h = args.small_page_height
    if isinstance(small_page_h, str):
        if small_page_h.strip().lower() in ("none", "off"):
            small_page_h = None
        else:
            try:
                small_page_h = float(small_page_h)
            except ValueError:
                raise SystemExit("--small-page-height takes a number of mm, "
                                 "or 'none'") from None
    if small_page_h is not None and small_page_h <= 0:
        small_page_h = None
    if args.scale <= 0:
        raise SystemExit("--scale must be positive")
    if args.tile_margin < 0:
        raise SystemExit("--tile-margin cannot be negative")
    if args.tile_overlap < 0:
        raise SystemExit("--tile-overlap cannot be negative")
    if args.tile_gap < 0:
        raise SystemExit("--tile-gap cannot be negative")

    if args.page_width is not None and args.page_width <= 0:
        raise SystemExit("--page-width must be positive")

    feathers = load_aggregate_feathers(args.aggregate, args.only)
    mode = args.pair_orientation

    # A pair that does not fit the page cannot be cut, so the width is the source's
    # question, not one feather's: every page gets the width the widest pair needs.
    nominal_width = PAGE_WIDTH_MM if args.page_width is None else args.page_width
    PAGE_WIDTH_MM, width_note = settle_page_width(feathers, args.scale, mode,
                                                  nominal_width)
    if width_note:
        print(f"note: page width {width_note}")

    if args.geometry_report:
        print(f"{args.aggregate.name}: {len(feathers)} feather(s)")
        print(f"  {'id':5} {'aggregate w x h':>18} {'turned':>8} {'upright w x h':>17} "
              f"{'pair':>9} {'quill guide':>12}")
        for f in feathers:
            turn = f.turned_deg % 360.0
            if turn > 180.0:
                turn -= 360.0
            headless = is_headless(f, mode)
            print(f"  {f.name:5} {f.declared_size_mm[0]:8.1f} x {f.declared_size_mm[1]:7.1f} "
                  f"{turn:7.1f}  {f.width:8.1f} x {f.height:7.1f} "
                  f"{'headless' if headless else 'upright':>9} "
                  f"{'read' if f.centered_guide else 'none':>12}")
        half = sum(1 for f in feathers if is_headless(f, mode))
        print(f"  {half} headless pair(s), {len(feathers) - half} upright; "
              f"pages split at {args.max_page_height:.0f} mm")
        print("  (the quill guide is read to find each feather's base; it is not "
              "printed)")
        if args.list:
            print()

    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows,
                         mode, small_page_h)
    layouts = [layout_page(group, rows, by_name, args.scale, mode)
               for group, rows, by_name in planned]
    generated = build_stamp()[0]

    if args.tile_paper is not None:
        try:
            paper_label, paper_w, paper_h = tile_paper(args.tile_paper)
            plan = plan_sheets(layouts, paper_w, paper_h, args.tile_margin,
                               args.tile_overlap, paper_label, args.tile_gap)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

        note = tiling_note(plan, layouts)
        if note:
            print(f"note: {note}")

        def page_note(index: int) -> str:
            """How the page is laid out across sheets, as text."""
            mine = [t for t in plan.tiles if t.page_no == index]
            if mine[0].tiled:
                cols = len({round(t.x0, 3) for t in mine})
                rows = len({round(t.y0, 3) for t in mine})
                return f"{cols} x {rows} tiles"
            sheets = len({t.sheet_no for t in mine})
            return "1 sheet" if sheets == 1 else f"shares {sheets} sheet(s)"

        if args.list:
            print(f"sheet plan: {plan.paper_label} landscape "
                  f"(paper {plan.paper_w:g} x {plan.paper_h:g} mm, "
                  f"margin {plan.margin:g} mm, overlap {plan.overlap:g} mm, "
                  f"gap {args.tile_gap:g} mm)")
            print(f"  {len(layouts)} logical page(s) -> {plan.sheet_total} sheet(s)")
            for index, layout in enumerate(layouts, start=1):
                print(f"  page {index:2}: {page_note(index):16} "
                      f"({layout.page_w:g} x {layout.page_h:g} mm "
                      f"[{', '.join(layout.names)}])")
            for sheet_no in range(1, plan.sheet_total + 1):
                on = tiles_on_sheet(plan, sheet_no)
                pages = sorted({t.page_no for t in on})
                print(f"  sheet {sheet_no:2}: page(s) "
                      + ", ".join(str(p) for p in pages)
                      + ("   [tiled]" if any(t.tiled for t in on) else ""))
            return 0

        doc = build_tiled_document(layouts, plan, generated, args.scale)
        doc.write(args.out)

        print(f"wrote {args.out}")
        print(f"  source      : {args.aggregate}")
        print(f"  paper       : {plan.paper_label} landscape "
              f"({plan.paper_w:g} x {plan.paper_h:g} mm)")
        print(f"  margin      : {plan.margin:g} mm (non-printable)")
        print(f"  overlap     : {plan.overlap:g} mm (tiled pages only)")
        print(f"  scale       : {args.scale:g} : 1")
        print(f"  logical     : {len(layouts)} poster page(s) "
              f"(from {len(feathers)} feather pairs)")
        print(f"  sheets      : {plan.sheet_total}")
        tiled = [p for p in range(1, len(layouts) + 1)
                 if any(t.tiled for t in plan.tiles if t.page_no == p)]
        print(f"                {len(layouts) - len(tiled)} page(s) fit a single "
              f"sheet whole; {len(tiled)} tiled: "
              + (", ".join(str(p) for p in tiled) if tiled else "none"))
        for index, layout in enumerate(layouts, start=1):
            print(f"    page {index:2}: {page_note(index):16} "
                  f"[{', '.join(layout.names)}]")
        return 0

    if args.list:
        for index, layout in enumerate(layouts, start=1):
            names = ", ".join(layout.names)
            print(f"page {index:2}  {layout.page_w:6.1f} x {layout.page_h:7.1f} mm  "
                  f"{len(layout.slots)} pair(s)  {names}")
        return 0

    doc = PdfDocument("Feather templates from the aggregate - mirrored left/right pairs")
    for index, layout in enumerate(layouts, start=1):
        content = build_page(layout, index, len(layouts), generated, args.scale)
        doc.add_page(layout.page_w, layout.page_h, content)
    doc.write(args.out)

    heights = [l.page_h for l in layouts]
    print(f"wrote {args.out}")
    print(f"  source      : {args.aggregate}")
    print(f"  pages       : {len(layouts)} (from {len(feathers)} feather pairs)")
    print(f"  scale       : {args.scale:g} : 1")
    print(f"  page width  : {PAGE_WIDTH_MM:g} mm (max)")
    print(f"  page height : {min(heights):.1f} .. {max(heights):.1f} mm")
    print(f"  spacing     : {SMALL_PARTNER_GAP_MM:g} mm between the halves of a "
          f"small-feather pair, {LARGE_PARTNER_GAP_MM:g} mm for "
          f"{'/'.join(LARGE_FAMILIES)}")
    print(f"                {DENSE_GAP_MM:g} mm between pairs in a row, "
          f"{SPARSE_GAP_MM:g} mm around a lone pair")
    for index, layout in enumerate(layouts, start=1):
        note = " ".join("headless" if s.headless else "upright" for s in layout.slots)
        print(f"    page {index:2}: {len(layout.slots)} pair(s) "
              f"{layout.page_w:.0f}x{layout.page_h:.0f} mm  "
              f"[{', '.join(layout.names)}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
