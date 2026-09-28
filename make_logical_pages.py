#!/usr/bin/env python3
"""
make_logical_pages.py
=====================

Script 1 of the print pipeline: build the mirrored-pair content and lay it out
into LOGICAL page SVGs, reading the feather geometry from
mechanical/templates/feathers-aggregate.svg.

Each page is self-contained, true scale (millimetres), sized to its content, and
labelled with a <title>. This script knows nothing about paper size, margins, or
tiling -- that is pages_to_pdf.py's job. The two scripts meet only at the
filesystem: a directory of page-NNN.svg files.

Output: mechanical/templates/print/logical-pages/page-NNN.svg (cover first).
"""

import math
import os
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Paths + cairo (cairosvg is used only to measure ink, for the placement crop)
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "mechanical" / "templates"
# The aggregate is the single source of truth for feather geometry: each feather
# and topline is one <g id="X"> holding its outline (and its frame, as
# data-wh/data-vb), with the transform that arranges it on that group rather than
# on a separate <use>.
AGG_SVG = TEMPLATES_DIR / "feathers-aggregate.svg"
OUT_DIR = TEMPLATES_DIR / "print" / "logical-pages"

CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
os.environ["CAIRO_PATH"] = CAIRO_BIN

import cairosvg
import pypdfium2 as pdfium

# --------------------------------------------------------------------------
# Config — the part you edit
# --------------------------------------------------------------------------

GAP = 10.0         # mm, clear space between the two halves of a pair
MAX_WIDTH = 260.0  # mm, a grouped page wraps into a new row beyond this width
PAD = 8.0          # mm, space between items on a shared page (raise if too tight)
# The overlay pages put their label on a band above the drawing instead of across
# its top, because that is where their origin digits are. AlignmentPage explains
# why; these are the band's height and the label's baseline inside it.
LABEL_BAND = 7.0   # mm
BAND_LABEL_Y = 3.6  # mm, baseline from the top of the band

# There are deliberately no FEATHERS / TOPLINES lists here any more. Both were
# only ever used to say which ids to read, and both duplicated what the manifest
# and the aggregate already say: SECTIONS names every item the pipeline prints,
# and the aggregate's <g id="outline-toplines"> holds the guides and the
# silhouette. The readers now derive both -- see "Reading the source files".
#
# This one id is still named, because it is the hinge the derivation turns on:
# it is both the list of guides and the placement template.
PLACEMENT_GROUP = "outline-toplines"

# The alignment overlays need no such hinge: each one is read from the manifest
# by its own id (<g id="B-align">, ...), so the "align" layer they nest in is
# never named here.

# The print manifest (SECTIONS) is defined below the section classes, because
# each entry is an instance of one of them -- see "The manifest".

SVG_NS = "{http://www.w3.org/2000/svg}"

# NOTE: stroke-width and font-size are UNITLESS on purpose. Our user units are
# millimetres, so "0.5" means 0.5 mm. Writing "0.5mm" trips a cairosvg quirk:
# it converts explicit CSS units through a 96-dpi px scale, then misreads those
# px as user units, inflating them ~3.78x (0.5mm -> 1.78mm).
CSS = """
.outline { stroke: #000000; stroke-width: 0.5; fill: none; }
.guide   { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: round; stroke-linejoin: round; }
.label   { font-family: sans-serif; fill: #000000; text-anchor: middle; dominant-baseline: middle; }
.title   { font-family: sans-serif; fill: #000000; font-size: 9; text-anchor: middle; font-weight: bold; }
.note    { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
.cal     { stroke: #000000; stroke-width: 0.5; }
.minor   { stroke: #000000; stroke-width: 0.15; }
.major   { stroke: #000000; stroke-width: 0.5; }
.num     { font-family: sans-serif; fill: #000000; font-size: 3.5; text-anchor: middle; }
.caltext { font-family: sans-serif; fill: #000000; font-size: 6; text-anchor: middle; font-weight: bold; }
"""

# The overlays need two rules the shared stylesheet has never had: a stroked
# hairline for an origin arrow (`.guide` is the same stroke but round-capped), and
# a solid fill for the fallback glyph. They are appended to the pages that use
# them -- overlay_page_svg() below -- rather than to CSS, so the shared block stays
# byte-identical and the pages that predate the overlays are not rewritten to
# carry rules nothing on them reads.
ARROW_CSS = """
.arrow { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: butt; stroke-linejoin: miter; }
.arrowhead { fill: #000000; stroke: none; }
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def fmt(x):
    """A millimetre value as a compact decimal (no trailing zeros)."""
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def parse_mm(s):
    return float(str(s).replace("mm", "").strip())


def label_size(Wp, Hp):
    """Label font size (mm): big enough to read, small enough to fit inside."""
    return max(3.0, min(12.0, min(Wp, Hp) / 6.0))


@dataclass
class Feather:
    name: str
    W: float        # file width  (mm)
    H: float        # file height (mm)
    x0: float       # viewBox origin
    y0: float
    d: str          # outline path data
    rotate90: bool  # B group is stored horizontal


@dataclass
class Item:
    """A printed component: a feather or a guide template."""
    name: str
    W: float        # placed width  (mm)
    H: float        # placed height (mm)
    body: str       # right-half SVG content, already in local [0,W]x[0,H]
    inside_label: bool = True   # feathers label each half; templates label the pair once
    mirror: bool = True         # False for items that should NOT be a left/right pair
    # Overlay origin glyphs. They are deliberately NOT in `body`: `body` is what
    # verify_body() renders and asserts lands inside [0,W]x[0,H], and a digit
    # centred on an origin can sit a hair outside that box. Keeping them out of
    # the body keeps the assertion about geometry, where it belongs. Both strings
    # are empty for everything but the alignment overlays.
    origins: str = ""           # the numbers, placed for the unmirrored page
    origins_flipped: str = ""   # the same numbers, placed for the mirrored page
    # (dx, dy) taking the source's own coordinates into the page's [0,W]x[0,H].
    # Only the overlays have one, because only they are drawn in a space other
    # than their page's; it is recorded here because the origin glyphs are inside
    # a transform rather than at page-local coordinates, and a check that wants to
    # know where they land should not have to take that markup apart.
    page_offset: tuple = (0.0, 0.0)
    # (x0, y0, x1, y1) of the drawn ink in page coordinates -- the same for both
    # pages, since mirroring a box is symmetric about the page. Empty for
    # everything but the overlays, which are the pages that label themselves from
    # it rather than from the page edge.
    ink_box: tuple = ()


# --------------------------------------------------------------------------
# Sections: one manifest entry, one or more logical pages
# --------------------------------------------------------------------------
#
# Every entry in SECTIONS is an object that owns its own layout. It reports the
# pages it contributes via pages(ctx) -- one for the shelf kinds, two for a
# whole-wing template (right, then left). So main() never inspects names or
# sizes to decide what a page is; the section knows.

@dataclass(frozen=True)
class Page:
    """One built logical page, ready to write."""
    title: str
    content: str
    w: float
    h: float
    # Page-specific rules appended to the shared stylesheet. Empty for every page
    # that does not need any, which keeps their bytes exactly as they were.
    extra_css: str = ""


@dataclass(frozen=True)
class Context:
    """What a section needs in order to lay itself out."""
    frags: dict     # name -> (built fragment, w, h)
    raw: dict       # name -> source Item (needed by MirroredWholePage)


class Section(ABC):
    """One entry in SECTIONS: owns a layout, emits one or more logical pages.

    `items` names the items the section is responsible for; the manifest is
    checked to cover every item that was read, exactly once."""

    items: tuple = ()

    @abstractmethod
    def pages(self, ctx: Context) -> list[Page]:
        """Return the logical pages this section contributes, in print order."""


class Shelf(Section):
    """Items placed left-to-right, wrapping at MAX_WIDTH. The one shared layout.

    `rotate` and `pad` are class knobs, not constructor arguments: a rotation is
    a kind of page here, not an option on a generic one."""

    rotate = 0.0
    pad = PAD

    def __init__(self, *items):
        assert items, f"{type(self).__name__} needs at least one item"
        self.items = tuple(items)

    def pages(self, ctx):
        content, w, h = shelf(self.items, ctx.frags, self.rotate, self.pad)
        return [Page("/".join(self.items), content, w, h)]


class MirroredPairs(Shelf):
    """Feather pairs, side by side. Emits 1 page."""


class MirroredPairsRot90(Shelf):
    """Feather pairs rotated 90 deg, so an oversized pair fits one sheet.
    Emits 1 page."""
    rotate = 90.0


class AlignmentPage(Section):
    """One alignment overlay, drawn whole and then mirrored. Emits 2 pages.

    Unlike a feather, an overlay is not one half of a pair: it is a single
    diagnostic drawing that already sits in placement space. So the two pages are
    two whole drawings -- the overlay, then the overlay mirrored left to right --
    the way MirroredWholePage treats the placement silhouette, and not the
    side-by-side pair build_pair() makes.

    The source is the RIGHT wing, so the raw drawing is the right page and the
    mirrored one is left. (This is the opposite of the placement page next door,
    which prints the same layer's raw geometry as its left. That is not a
    contradiction to paper over: the feather pages and the overlays are both
    right-handed, and the placement page's own naming is the odd one out. It is
    left alone here because its bytes are pinned by the acceptance test.)

    The origin digits sit outside the page mirror on the mirrored page (and are
    re-placed by it) so they stay upright instead of back to front.

    The label goes on a band added ABOVE the drawing, not across its top, and is
    centred on the drawing rather than on the page. An overlay's arrows point away
    from the silhouette's tip, so the first origin sits right where a label would
    otherwise go; more to the point, these drawings do not fill their page, and a
    page-centred label lands off the artwork entirely."""

    def __init__(self, item):
        self.items = (item,)

    def pages(self, ctx):
        item = ctx.raw[self.items[0]]
        W, H = item.W, item.H
        down = LABEL_BAND - 1.0        # 1 mm: read_align's margin is the rest

        # Centre the label over the drawing's own ink box, not over the page.
        ax0, ay0, ax1, ay1 = item.ink_box
        note = (f'<text class="label" font-size="{fmt(label_size(ax1 - ax0, ax1 - ax0))}" '
                f'x="{fmt((ax0 + ax1) / 2.0)}" y="{fmt(BAND_LABEL_Y)}">'
                f'{item.name}</text>')

        frame = f'translate(0 {fmt(down)})'
        body = f'<g transform="{frame}">{item.body}{item.origins}</g>'
        mirrored = (f'<g transform="translate({fmt(W)} 0) scale(-1 1)">{item.body}</g>'
                    f'<g transform="{frame}">{item.origins_flipped}</g>')
        return [Page(f"{item.name}-left", body + note, W, H + down, ARROW_CSS),
                Page(f"{item.name}-right", mirrored + note, W, H + down, ARROW_CSS)]


class MirroredWholePage(Section):
    """A whole-wing drawing, drawn whole rather than as a pair.
    Emits 2 pages: right, then left."""

    def __init__(self, item):
        self.items = (item,)

    def pages(self, ctx):
        return placement_halves(ctx.raw[self.items[0]])


class Cover(Section):
    """The calibration cover. Emits 1 page."""

    def pages(self, ctx):
        return [cover_page()]


# The manifest: the ordered list of sections, top to bottom, cover first.
# Every item that was read must appear here exactly once.
SECTIONS = [
    Cover(),
    MirroredPairs("P1"),
    MirroredPairs("P2"),
    MirroredPairs("P3"),
    MirroredPairs("P4"),
    MirroredPairs("P5"),
    MirroredPairsRot90("S1"),
    MirroredPairsRot90("S2"),
    MirroredPairs("S3"),
    MirroredPairs("S4"),
    MirroredPairs("B1"),
    MirroredPairsRot90("B2"),
    MirroredPairsRot90("B3"),
    MirroredPairs("A1", "A2", "A3"),
    MirroredPairs("PC1", "PC2"),
    MirroredPairs("SC1", "SC2"),
    MirroredPairs("SC3"),
    MirroredPairs("SC4"),
    MirroredPairs("MC1", "MC2"),
    MirroredPairs("MC3", "MC4"),
    MirroredPairs("LC1", "LC2", "LC3"),
    MirroredWholePage("outline-toplines"),
    # The alignment overlays, in family order. Two pages each (right, then the
    # mirrored left), so this is 16 pages, not 8. Print order is manifest order.
    AlignmentPage("B-align"),
    AlignmentPage("P-align"),
    AlignmentPage("PC-align"),
    AlignmentPage("A-align"),
    AlignmentPage("SC-align"),
    AlignmentPage("MC-align"),
    AlignmentPage("LC-align"),
    AlignmentPage("S-align"),
]


# --------------------------------------------------------------------------
# Reading the source files
# --------------------------------------------------------------------------
#
# Everything is read out of feathers-aggregate-conslidated.svg. Each feather is
# a <g id="X"> nested in a prefix group (<g id="P">, <g id="B">, ...), holding
# the outline and two data attributes standing in for the source file's root
# <svg>:
#
#   data-wh   the file's width and height   (placed size / scale)
#   data-vb   the file's viewBox            (x0 y0 W H -- the frame the outline
#                                            was drawn in, which right_transform
#                                            and mirror_check need)
#
# The eight alignment guides and the whole-wing silhouette live together in
# <g id="outline-toplines">, which is the placement page's source. The overlays
# are a separate layer: each is <g id="X-align"> inside <g id="align">, carrying
# its silhouette and its numbered origin arrows, and each is read by its own
# manifest name rather than from a list kept here.
#
# Nothing in this file enumerates the items: SECTIONS (the manifest) names every
# item the pipeline prints, and each name is read by what the aggregate says it
# is -- the outline-toplines group is the placement template, an id ending in
# "-align" is an overlay, anything else with geometry is a feather.

_AGG_CACHE = {}


def aggregate_by_id():
    """{id: element} for the whole aggregate, parsed once."""
    if "index" not in _AGG_CACHE:
        root = ET.parse(AGG_SVG).getroot()
        _AGG_CACHE["index"] = {el.get("id"): el for el in root.iter()
                               if el.get("id")}
    return _AGG_CACHE["index"]


def _frame(name, el):
    """(x0, y0, W, H) from a def group's data attributes.

    They have to agree with each other: data-wh is the file's own width/height
    and data-vb its viewBox, and a discrepancy means the frame was mis-recorded
    -- which would silently move the outline rather than fail."""
    wh = (el.get("data-wh") or "").split()
    vb = el.get("data-vb") or ""
    assert len(wh) == 2 and len(vb.split()) == 4, (
        f"{name}: def group needs data-wh and data-vb")
    W, H = (parse_mm(v) for v in wh)
    x0, y0, vw, vh = (float(v) for v in vb.split())
    assert abs(vw - W) < 1e-3 and abs(vh - H) < 1e-3, (
        f"{name}: data-vb {vw}x{vh} != data-wh {W}x{H} -- not identity")
    return x0, y0, W, H


def _def_group(name):
    """The group holding `name`'s geometry.

    The consolidated aggregate drops the "-def" suffix -- the geometry group is
    simply <g id="X">, because there are no <use> placements left for it to
    collide with. Both spellings are accepted so the script keeps working
    against either aggregate."""
    index = aggregate_by_id()
    for gid in (name, f"{name}-def"):
        el = index.get(gid)
        if el is not None:
            return el
    raise AssertionError(f"{name}: no <g id=\"{name}\"> or <g id=\"{name}-def\"> "
                         f"in {AGG_SVG.name}")


def _path_d(name, el):
    path_el = el.find(f".//{SVG_NS}path")
    assert path_el is not None, f"{name}: def group has no <path>"
    return " ".join(path_el.get("d").split())   # normalise internal whitespace


def read_feather(name):
    """One feather as a Feather, read by id.

    The B group is stored with its long axis horizontal and must be rotated 90
    deg clockwise; that is a property of the arrangement, not of the item, so it
    stays a name-prefix rule rather than a declaration."""
    el = _def_group(name)
    x0, y0, W, H = _frame(name, el)
    d = _path_d(name, el)
    return Feather(name, W, H, x0, y0, d, rotate90=name.startswith("B"))


def placement_group():
    """The <g id="outline-toplines"> the guides and the silhouette live in."""
    el = aggregate_by_id().get(PLACEMENT_GROUP)
    assert el is not None, f"no <g id=\"{PLACEMENT_GROUP}\"> in {AGG_SVG.name}"
    return el


# --------------------------------------------------------------------------
# Pair geometry
# --------------------------------------------------------------------------

def placed_size(f):
    """Width x height of the outline after any rotation (the local pair half)."""
    return (f.H, f.W) if f.rotate90 else (f.W, f.H)


def right_transform(f):
    """Transform string that puts the outline in its local [0,W]x[0,H] frame."""
    if f.rotate90:
        cx = f.x0 + f.W / 2.0
        cy = f.y0 + f.H / 2.0
        return (f"translate({fmt(f.H / 2.0)} {fmt(f.W / 2.0)}) rotate(90) "
                f"translate({fmt(-cx)} {fmt(-cy)})")
    return f"translate({fmt(-f.x0)} {fmt(-f.y0)})"


def feather_item(f):
    """Turn a Feather into an Item: right-half body at placed size."""
    Wp, Hp = placed_size(f)
    rt = right_transform(f)
    body = f'<g transform="{rt}"><path class="outline" d="{f.d}"/></g>'
    return Item(f.name, Wp, Hp, body, inside_label=True)


def guide_label(item):
    """The upright label a non-mirrored guide carries, drawn along its line
    (rotated 90 deg about the guide's centre)."""
    size = fmt(min(6.0, max(3.0, item.W / 12.0)))
    cx, cy = item.W / 2.0, item.H / 2.0
    return (f'<text class="label" font-size="{size}" x="{fmt(cx)}" y="{fmt(cy)}" '
            f'transform="rotate(90 {fmt(cx)} {fmt(cy)})">{item.name}</text>')


def build_pair(item):
    """Return (fragment, w, h) in the local frame.

    A mirrored item is a left/right pair; a non-mirrored item (the toplines) is
    a single fragment with one label and no left/right distinction."""
    W, H = item.W, item.H
    if not item.mirror:
        return item.body + guide_label(item), W, H

    if item.inside_label:
        size = fmt(label_size(W, H))
        y = H / 2.0
    else:
        size = fmt(min(6.0, max(3.0, W / 12.0)))
        y = 3.0

    # left wing = mirror of the source, placed at [0, W]; right wing = source
    # as-is, placed at [W+GAP, 2W+GAP]. Labels sit outside the mirror so they
    # read upright.
    left_geom = f'<g transform="translate({fmt(W)} 0) scale(-1 1)">{item.body}</g>'
    right_geom = f'<g transform="translate({fmt(W + GAP)} 0)">{item.body}</g>'
    left_label = (f'<text class="label" font-size="{size}" x="{fmt(W / 2.0)}" '
                  f'y="{fmt(y)}">{item.name} left</text>')
    right_label = (f'<text class="label" font-size="{size}" x="{fmt(W + GAP + W / 2.0)}" '
                   f'y="{fmt(y)}">{item.name} right</text>')

    frag = (f'<g id="{item.name}-pair">'
            f'<g id="{item.name}-left">{left_geom}{left_label}</g>'
            f'<g id="{item.name}-right">{right_geom}{right_label}</g>'
            f'</g>')
    return frag, 2.0 * W + GAP, H


# --------------------------------------------------------------------------
# Independent transform evaluator
# --------------------------------------------------------------------------
#
# Two callers with different needs share one evaluator: mirror_check(), which
# only ever feeds it translate and centred rotate, and the overlay reader, whose
# groups carry matrix(...) and rotate(angle, cx, cy). So this composes the full
# 2x3 affine matrix of an SVG transform list rather than pattern-matching three
# operations -- the old version ignored rotate's centre arguments entirely, which
# is exactly the form the overlays use.

_IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _mul(A, B):
    """The matrix that applies B first, then A (so: A after B)."""
    a1, b1, c1, d1, e1, f1 = A
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _ops(tstr):
    """[(kind, [float, ...]), ...] -- an SVG transform list, strings to numbers."""
    out = []
    for kind, args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", tstr or ""):
        vals = [float(v) for v in re.split(r"[\s,]+", args.strip()) if v]
        if kind == "matrix":
            out.append((kind, vals))
        elif kind == "translate":
            out.append((kind, vals + [0.0] * (2 - len(vals))))
        elif kind == "scale":
            out.append((kind, vals + vals[:1] * (2 - len(vals))))
        elif kind == "rotate":
            # rotate(a) is rotate(a, 0, 0); the centre arguments are not optional
            # to get right -- dropping them is what the old evaluator did.
            cx, cy = (vals[1], vals[2]) if len(vals) >= 3 else (0.0, 0.0)
            a = math.radians(vals[0])
            cos, sin = math.cos(a), math.sin(a)
            out.append(("matrix", [cos, sin, -sin, cos,
                                   cx - cos * cx + sin * cy,
                                   cy - sin * cx - cos * cy]))
        elif kind == "skewX":
            out.append(("matrix", [1.0, 0.0, math.tan(math.radians(vals[0])), 1.0, 0.0, 0.0]))
        elif kind == "skewY":
            out.append(("matrix", [1.0, math.tan(math.radians(vals[0])), 0.0, 1.0, 0.0, 0.0]))
        else:
            raise AssertionError(f"unsupported transform {kind!r} in {tstr!r}")
    return out


def transform_matrix(*tstrs):
    """The 2x3 matrix of a concatenated transform list (leftmost applies last)."""
    m = _IDENT
    for tstr in tstrs:
        for kind, vals in _ops(tstr):
            if kind == "matrix":
                m = _mul(m, tuple(vals))
            elif kind == "translate":
                m = _mul(m, (1.0, 0.0, 0.0, 1.0, vals[0], vals[1]))
            elif kind == "scale":
                m = _mul(m, (vals[0], 0.0, 0.0, vals[1], 0.0, 0.0))
    return m


def _apply_matrix(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def apply_transform(tstr, points):
    """Apply an SVG transform string to points (any affine transform)."""
    m = transform_matrix(tstr)
    return [_apply_matrix(m, x, y) for (x, y) in points]


def bbox(pts):
    """(x0, y0, x1, y1) of a point list; None for an empty list."""
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def mirror_check(f):
    """Assert the left half is an exact mirror of the right half, true size."""
    Wp, Hp = placed_size(f)
    rt = right_transform(f)
    right_t = f"translate({fmt(Wp + GAP)} 0)"
    left_t = f"translate({fmt(Wp)} 0) scale(-1 1)"
    corners = [(f.x0, f.y0), (f.x0 + f.W, f.y0),
               (f.x0, f.y0 + f.H), (f.x0 + f.W, f.y0 + f.H)]
    rbox = bbox(apply_transform(right_t + " " + rt, corners))
    lbox = bbox(apply_transform(left_t + " " + rt, corners))

    ok = (
        abs(rbox[0] - (Wp + GAP)) < 1e-3 and abs(rbox[1] - 0.0) < 1e-3
        and abs(rbox[2] - (2.0 * Wp + GAP)) < 1e-3 and abs(rbox[3] - Hp) < 1e-3
        and abs(lbox[0] - 0.0) < 1e-3 and abs(lbox[1] - 0.0) < 1e-3
        and abs(lbox[2] - Wp) < 1e-3 and abs(lbox[3] - Hp) < 1e-3
    )
    return ok, (rbox, lbox)


# --------------------------------------------------------------------------
# Template items (placement + alignment overlays)
# --------------------------------------------------------------------------

_INK_THRESHOLD = 128


def measure_ink(svg, dpi=150, req_margin=0.0):
    """Render an SVG and return its ink bounding box (x0, y0, x1, y1) in mm.

    `req_margin` is the clear space in mm the ink must leave on every edge of the
    rendered page. It is how a *fitted* harness proves it did not clip: a clipped
    render does not fail, it quietly returns a smaller ink box, and a smaller ink
    box means a page that is too short with geometry hanging outside it. Asking
    for a margin turns that into an error instead."""
    pdf_bytes = cairosvg.svg2pdf(bytestring=svg.encode())
    img = pdfium.PdfDocument(pdf_bytes)[0].render(scale=dpi / 72.0).to_pil().convert("L")
    # Threshold then getbbox(): the same ink test as walking every pixel, in C.
    # The pixel walk this replaced ran twice over the whole raster in Python --
    # 3.1 M px at 150 dpi over a 300 mm harness, which is why 300 mm was also the
    # practical ceiling on the harness size.
    ink = img.point(lambda v: 255 if v < _INK_THRESHOLD else 0).getbbox()
    if ink is None:
        raise SystemExit("rendered SVG produced no ink")
    PPM = dpi / 25.4
    x0, y0, x1, y1 = (v / PPM for v in ink)
    if req_margin:
        for edge, gap in (("left", x0), ("top", y0),
                          ("right", (img.size[0] / PPM) - x1),
                          ("bottom", (img.size[1] / PPM) - y1)):
            assert gap >= req_margin, (
                f"ink {gap:.2f} mm from the {edge} edge of the harness: the "
                f"harness is clipping the geometry")
    # minus one: PIL's getbbox() returns a half-open box, so the outermost ink
    # pixel is at x1-1, not x1. read_placement() has always measured that way.
    return (x0, y0, (ink[2] - 1) / PPM, (ink[3] - 1) / PPM)


def _group_content(g):
    """Serialise a guide <g>'s children as normalised geometry (path + marker)."""
    out = []
    for el in g:
        if el.tag == f"{SVG_NS}path":
            t = el.get("transform")
            tr = f' transform="{t}"' if t else ""
            out.append(f'<path class="guide" d="{el.get("d")}"{tr}/>')
        elif el.tag == f"{SVG_NS}circle":
            out.append(f'<circle cx="{el.get("cx")}" cy="{el.get("cy")}" '
                       f'r="{el.get("r")}" fill="#000000" stroke="none"/>')
    return "".join(out)


# --- the alignment overlays -------------------------------------------------
#
# An overlay is <g id="X-align"> holding one silhouette <path class="outline">
# and its origin arrows, <path class="arrow numN">. Two things about it differ
# from a guide in <g id="outline-toplines">, and both are why it needs its own
# reader rather than _group_content():
#
#   * the arrows are the *source's* answer to a marker -- a stroked hairline that
#     the source points at a numbered <marker> -- and this pipeline copies no CSS
#     and no marker defs out of the aggregate. So the reader reproduces the one
#     thing the marker draws: the digit, as text of its own.
#   * the group's transform is a full matrix() or rotate(a, cx, cy). The digits
#     are placed through it, which is why the evaluator above is matrix-based.

# The fallback origin glyph: the shape of the source's own unnumbered-arrow
# marker, a diamond, used when an arrow carries no number to print. It is centred
# on its origin the way the marker's contents are, so a mirrored page can simply
# move it.
_DIAMOND_PTS = ((0.0, -1.8), (0.9, 0.0), (0.0, 1.8), (-0.9, 0.0))
_DIGIT_PT = 4.0 / 3.7795    # the source's numeral font-size, px -> mm


# Command letter -> how many numbers one segment of it takes. "m" is special-
# cased in _path_points(): its first pair is a moveto and any pairs after it are
# implicit linetos.
_PATH_NUMS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2,
              "a": 7, "z": 0}
# A number must contain at least one digit, or the command letters match too --
# that is not hypothetical, the first cut of this did exactly that and read the
# path as if it had no commands at all.
_NUMBER = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")


def _path_points(d):
    """The points a `d` string passes through, in the path's own frame.

    Only endpoints and control points are returned -- never the arc flags or the
    implied reflection of `s`/`t` -- but every point a curve can reach is the
    convex combination of those, so their bbox contains the drawn path. That is
    all this is for: sizing the harness that measures the ink, where a
    conservative box is what is wanted.

    This has to track the current point: the overlays are drawn with RELATIVE
    commands (`m` followed by implicit linetos, and relative cubics), so the
    numbers are deltas, not positions. Pairing the numbers up positionally --
    which is what this did first -- reads a relative path as an absolute one and
    silently reports a bbox several times too large."""
    toks = _NUMBER.findall(d or "")
    i, n = 0, len(toks)
    letter, x, y = None, 0.0, 0.0
    start = (0.0, 0.0)
    pts = []

    def take(k):
        nonlocal i
        vals = [float(t) for t in toks[i:i + k]]
        i += k
        return vals

    while i < n:
        if toks[i].isalpha():
            letter = toks[i]
            i += 1
            if letter in "zZ":
                x, y = start
                continue
        elif letter is None:
            raise AssertionError(f"path data without a command: {d!r}")

        c = letter.lower()
        rel = letter.islower()
        k = _PATH_NUMS[c]
        if k == 0:
            continue
        v = take(k)
        if c == "h":
            x = x + v[0] if rel else v[0]
            pts.append((x, y))
        elif c == "v":
            y = y + v[0] if rel else v[0]
            pts.append((x, y))
        elif c == "a":
            # the endpoint is the last pair; the radii and flags are not points
            ex, ey = v[5], v[6]
            x, y = (x + ex, y + ey) if rel else (ex, ey)
            pts.append((x, y))
        else:
            pairs = [(v[j], v[j + 1]) for j in range(0, len(v), 2)]
            if rel:
                pairs = [(x + px, y + py) for (px, py) in pairs]
            pts.extend(pairs)
            x, y = pairs[-1]
            if c == "m":
                start = (x, y)
        if c in "ml":                      # an implicit repeat is another line
            letter = "l" if rel else "L"
    return pts


def _path_points_of(el, *transforms, kind=None):
    """Every path point in a group, in the frame `transforms` put it in.

    Each path's own transform is applied on top of `transforms`, in that order --
    an overlay's arrows carry one and its silhouette does not, so ignoring it
    would measure the arrows in the wrong place entirely. The overlays' arrows
    are the loud case: they are drawn already in placement space with a rotation
    that cancels their group's, which is exactly the sort of thing a reader that
    skips a transform cannot tell from one that applies it."""
    out = []
    for child in el:
        if child.tag != f"{SVG_NS}path" or (kind and _path_kind(child) != kind):
            continue
        m = transform_matrix(*transforms, child.get("transform") or "")
        out += [_apply_matrix(m, x, y) for (x, y) in _path_points(child.get("d"))]
    return out


def _path_kind(el):
    """Which of an overlay's two kinds of <path> this is: the silhouette or an
    origin. The source says so in the class; the length of the path is the
    fallback, since an origin arrow is a two-point stub and the silhouette is
    not."""
    if el.tag != f"{SVG_NS}path":
        return None
    cls = el.get("class") or ""
    if "arrow" in cls:
        return "arrow"
    if "outline" in cls:
        return "outline"
    return "outline" if len(_path_points(el.get("d"))) > 2 else "arrow"


def _path_child(el, cls):
    """One overlay <path> as SVG, keeping its own transform and its class."""
    t = el.get("transform")
    tr = f' transform="{t}"' if t else ""
    return f'<path class="{cls}" d="{el.get("d")}"{tr}/>'


def _origin_digit(cls):
    """The number in an arrow's class ("" when it has none)."""
    m = re.search(r"\bnum(\d+)\b", cls or "")
    return m.group(1) if m else ""


def _diamond(x, y):
    """The fallback glyph, centred on (x, y)."""
    pts = " ".join(f"{fmt(x + dx)},{fmt(y + dy)}" for dx, dy in _DIAMOND_PTS)
    return f'<polygon class="arrowhead" points="{pts}"/>'


def _align_paths(el, kind, cls, transform=True):
    """The overlay's `<path>`s of one kind: "outline" (the silhouette) or "arrow"
    (an origin), wrapped in the transform that applies to the kind.

    `transform` is False for the silhouette: it is placed by the group wrappers
    around it (the read_align() frame and then the placement-space transform), so
    folding the transform in here as well would apply it twice."""
    tr = f' transform="{el.get("transform")}"' if transform and el.get("transform") else ""
    return f'<g{tr}>{"".join(_path_child(c, cls) for c in el if _path_kind(c) == kind)}</g>'


def _origin_anchors(el, matrix):
    """One entry per origin arrow: (child, anchor point), in document order.

    The anchor is the arrow's first vertex: that is where the source's own marker
    puts its content, because refX/refY are 0 against a viewBox centred on the
    origin, so the marker -- diamond or number -- is centred on the path's start
    point. `_origin_marks()` draws there, and read_align() sizes the page from
    these, so both agree by construction."""
    out = []
    for child in el:
        if _path_kind(child) != "arrow":
            continue
        pts = _path_points(child.get("d"))
        if not pts:
            continue
        out.append((child, _apply_matrix(
            transform_matrix(matrix, child.get("transform") or ""), *pts[0])))
    return out


def _origin_marks(el, matrix, mirror=None):
    """One glyph per origin: the number the source gives the arrow, or the
    diamond when it carries none.

    The glyph goes at the arrow's anchor (see _origin_anchors). It is drawn
    upright whatever the transform does, like the source's marker, which is
    unrotated (orient="0").

    `mirror` maps a placement-space x to its mirrored x. The page mirror is an
    enclosing group, which would flip the digit back to front; re-placing it and
    preflipping it about its own axis composes with that mirror to a plain
    translation, so the digit lands in the mirrored position still reading
    upright. (The diamond needs neither: it is symmetric about its origin.)"""
    marks = []
    for child, (x, y) in _origin_anchors(el, matrix):
        if digit := _origin_digit(child.get("class")):
            if mirror is not None:
                x = mirror(x)
                tr = f'transform="translate({fmt(2.0 * x)} 0) scale(-1 1)" '
            else:
                tr = ""
            # class="label", not "num": .label is the shared stylesheet's text
            # class, and the page then needs no CSS of its own. dominant-baseline
            # is set here rather than in .label because an inline attribute wins
            # over the stylesheet -- .label's own value must stand for the labels
            # every other page already has.
            marks.append(f'<text class="label" {tr}x="{fmt(x)}" y="{fmt(y)}" '
                         f'font-size="{fmt(_DIGIT_PT)}" '
                         f'dominant-baseline="central">{digit}</text>')
        else:
            if mirror is not None:
                x = mirror(x)
            marks.append(_diamond(x, y))
    return "".join(marks)


def _geometry_svg(w, h, content):
    """A render harness of exactly w x h mm whose user units are millimetres.

    The viewBox is `0 0 w h`, so content must be in that frame; read_align()
    translates it there before calling this, which also means the ink comes back
    measured in the harness's own (and so the page's) frame."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(w)}mm" '
            f'height="{fmt(h)}mm" viewBox="0 0 {fmt(w)} {fmt(h)}">'
            f'<style>{CSS}</style>'
            f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="#fff"/>'
            f'{content}</svg>')


def read_align(name, el):
    """One alignment overlay as an Item: silhouette + numbered origins.

    Same contract as read_placement(): wrap the group in its own transform, copy
    its geometry serially, measure the ink, then re-origin so the ink sits in
    [0,W]x[0,H] at true scale. Unlike read_placement() there is no data-wh /
    data-vb frame to read -- the overlay is drawn in placement space and its size
    *is* what it measures."""
    content = _align_paths(el, "outline", "outline") + _align_paths(el, "arrow", "arrow")

    # Size the harness to the content instead of using a fixed 300 x 300 mm:
    # P-align is 424 mm tall, so the old fixed harness would have clipped 220 mm
    # off it -- and a clipped render returns a *smaller* ink box, i.e. a silently
    # short page. The analytic path bbox is already in placement space, so it is
    # measured there and only has to be shifted into the harness's viewBox.
    #
    # The frame is the union of the geometry and the DIGITS' anchor points, plus a
    # digit's half-height of slack: an origin arrow points away from the
    # silhouette, so its number can sit outside the silhouette's own bbox (on
    # LC-align it does), and a page sized from the paths alone would cut it off.
    SLOP = 5.0                                  # mm, so the harness cannot clip
    matrix = el.get("transform") or ""
    anchors = [pt for _, pt in _origin_anchors(el, matrix)]
    pts = _path_points_of(el, matrix) + anchors
    assert pts, f"{name}: overlay group has no path geometry"
    gx0, gy0, gx1, gy1 = bbox(pts)
    half = _DIGIT_PT / 2.0                      # a digit's radius, roughly
    gx0, gy0, gx1, gy1 = gx0 - half, gy0 - half, gx1 + half, gy1 + half
    ox, oy = gx0 - SLOP, gy0 - SLOP            # harness viewBox origin
    w = max((gx1 - gx0) + 2.0 * SLOP, 20.0)
    h = max((gy1 - gy0) + 2.0 * SLOP, 20.0)
    framed = (f'<g transform="translate({fmt(-ox)} {fmt(-oy)})">{content}</g>')
    svg = _geometry_svg(w, h, framed)

    # The requested margin is what proves the harness did not clip.
    bx0, by0, bx1, by1 = measure_ink(svg, req_margin=SLOP / 2.0)

    m = 1.0                                     # 1 mm margin, like the feathers
    W = (bx1 - bx0) + 2.0 * m
    H = (by1 - by0) + 2.0 * m
    body = (f'<g transform="translate({fmt(-(bx0 - m))} {fmt(-(by0 - m))})">'
            f'{framed}</g>')

    # The glyphs are placed in the SAME frame as the geometry, by wrapping them in
    # the same group rather than re-deriving their coordinates. Two frames nest
    # here: `framed` moves placement space into the harness, and `body` moves the
    # ink's corner to (m, m). Skipping the second -- which this did first -- leaves
    # every digit at its placement-space y, hundreds of millimetres below a page
    # only 139 mm tall, where cairosvg clips it away and it simply disappears.
    #
    # On the mirrored page the enclosing group flips everything, so the digit is
    # re-placed at W minus its page x and preflipped about its own axis: mirror of
    # mirror is a translation, and the digit stays upright instead of back to
    # front.
    # The glyphs are emitted inside `screen`, so `mirror` must return the x that
    # lands, after screen, on the mirrored page -- not the mirrored page position
    # itself. Derive it from the page map rather than juggling offsets (getting
    # this wrong does not nudge the digit, it throws it off the page):
    #
    #   screen(x) = x - ox             the group in `origins`
    #   page(x)   = screen(x) - (bx0 - m)    and body's frame around it
    #   so  screen(mirror(x)) == W - page(x)   =>   mirror(x) = W - x - (ox + bx0 - m)
    matrix = el.get("transform") or ""
    shift = ox + (bx0 - m)              # page(x) = x - shift
    screen_shift = f'<g transform="translate({fmt(-ox)} {fmt(-oy)})">'
    mirror = lambda x: W - x + shift
    return Item(name, W, H, body, inside_label=False, mirror=False,
                origins=screen_shift + f'{_origin_marks(el, matrix)}</g>',
                origins_flipped=screen_shift
                                + f'{_origin_marks(el, matrix, mirror)}</g>',
                # The glyphs' total move is the sum of the two translations that
                # wrap them -- `screen` and body's own frame -- so read it straight
                # off those two numbers rather than re-deriving it. Both are
                # already computed above; a sign slip here is invisible in the
                # page and silently wrong in anything that asks where a digit is.
                page_offset=(-ox - (bx0 - m), -oy - (by0 - m)),
                ink_box=(-(bx0 - m), -(by0 - m), W - (bx0 - m) - 2.0 * m,
                         H - (by0 - m) - 2.0 * m))


def read_placement():
    """The whole-wing placement template as an Item.

    It used to be a document of its own (outline-toplines.svg) built from
    <use>s into sibling files, then the aggregate's placement-* groups whose
    <use>s pointed at the inlined *-topline defs. The consolidated aggregate has
    no <use>s left: the guides and the silhouette sit together in one group and
    are read from it directly.

    That group is placed with its own transform, exactly as the two groups it
    replaced were -- both carried the same matrix, so wrapping the pair once is
    the same geometry as wrapping each."""
    g = placement_group()
    parts = []
    for child in g:
        if child.tag != f"{SVG_NS}g":
            continue
        ct = child.get("transform") or ""
        parts.append(f'<g transform="{ct}">{_group_content(child)}</g>')
    content = f'<g transform="{g.get("transform") or ""}">{"".join(parts)}</g>'

    # Deliberately still the fixed 300 x 300 mm harness. This page's W and H are
    # pixel-quantized (0.169 mm per pixel at 150 dpi), so moving it to the fitted
    # harness above would move both placement pages -- which the acceptance test
    # forbids. 249 x 196 mm fits 300 mm by luck; it is not a coincidence to
    # disturb.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="300mm" height="300mm" '
           f'viewBox="0 0 300 300"><style>{CSS}</style>'
           f'<rect width="300" height="300" fill="#fff"/>{content}</svg>')
    bx0, by0, bx1, by1 = measure_ink(svg)

    m = 1.0                                     # 1 mm margin, like the feathers
    W = (bx1 - bx0) + 2.0 * m
    H = (by1 - by0) + 2.0 * m
    body = (f'<g transform="translate({fmt(-(bx0 - m))} {fmt(-(by0 - m))})">'
            f'{content}</g>')
    return Item("outline-toplines", W, H, body, inside_label=False)


def verify_body(item):
    """Render an item's right-half body and confirm it lands in [0,W]x[0,H]."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(item.W)}mm" '
           f'height="{fmt(item.H)}mm" viewBox="0 0 {fmt(item.W)} {fmt(item.H)}">'
           f'<style>{CSS}</style>'
           f'<rect width="{fmt(item.W)}" height="{fmt(item.H)}" fill="#fff"/>'
           f'{item.body}</svg>')
    x0, y0, x1, y1 = measure_ink(svg)
    ok = x0 >= -0.5 and y0 >= -0.5 and x1 <= item.W + 0.5 and y1 <= item.H + 0.5
    return ok, (x0, y0, x1, y1)


# --------------------------------------------------------------------------
# Logical-page assembly
# --------------------------------------------------------------------------

def page_svg(title, content, w, h, extra_css=""):
    """Wrap page content in a self-contained SVG with an explicit size.

    `extra_css` is page-specific presentation. Only the overlay pages pass it, so
    the stylesheet every earlier page carries is unchanged byte for byte."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(w)}mm" '
            f'height="{fmt(h)}mm" viewBox="0 0 {fmt(w)} {fmt(h)}">\n'
            f'<title>{title}</title>\n'
            f'<style type="text/css">{CSS}{extra_css}</style>\n'
            f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="#ffffff"/>\n'
            f'{content}\n</svg>\n')


def rotated_bbox(w, h, deg):
    """(RW, RH) — bbox of a w x h rect rotated deg degrees about its centre."""
    rad = math.radians(deg)
    return (w * abs(math.cos(rad)) + h * abs(math.sin(rad)),
            w * abs(math.sin(rad)) + h * abs(math.cos(rad)))


def placed_transform(w, h, deg, x, y):
    """Transform that rotates a [0,w]x[0,h] box by deg about its centre and puts
    the rotated box's top-left at (x, y)."""
    if deg == 0.0:
        return f"translate({fmt(x)} {fmt(y)})"
    cx, cy = w / 2.0, h / 2.0
    RW, RH = rotated_bbox(w, h, deg)
    tx = x - cx + RW / 2.0
    ty = y - cy + RH / 2.0
    return f"translate({fmt(tx)} {fmt(ty)}) rotate({fmt(deg)} {fmt(cx)} {fmt(cy)})"


def shelf(names, frags, rotate, pad):
    """Lay named fragments out left-to-right, wrapping at MAX_WIDTH.

    Returns (content, MAX_WIDTH, page_height); the page is the union of the
    placed boxes. `rotate` is clockwise about each fragment's centre; `pad` is
    the gap between neighbours (the wrap gap is always PAD)."""
    placed = []
    x = y = 0.0
    row_h = 0.0
    max_y = 0.0
    for name in names:
        frag, w, h = frags[name]
        RW, RH = rotated_bbox(w, h, rotate)
        if x > 0 and x + RW > MAX_WIDTH:      # no room in this row -> wrap
            y += row_h + PAD
            x = 0.0
            row_h = 0.0
        placed.append((frag, placed_transform(w, h, rotate, x, y)))
        x += RW + pad
        row_h = max(row_h, RH)
        max_y = max(max_y, y + RH)
    content = "".join(f'<g transform="{tr}">{frag}</g>' for frag, tr in placed)
    return content, MAX_WIDTH, max_y


def side_note(text, w, y=3.0):
    """The explicit left/right marker a whole-page drawing carries: a label
    centred across the top of the page."""
    size = fmt(min(6.0, max(3.0, w / 12.0)))
    return (f'<text class="label" font-size="{size}" x="{fmt(w / 2)}" '
            f'y="{fmt(y)}">{text}</text>')


def placement_halves(item):
    """A whole-wing drawing gets no side-by-side pair: the right and left
    versions are two separate whole pages (right first, then left)."""
    W, H = item.W, item.H
    size = fmt(min(6.0, max(3.0, W / 12.0)))
    right = (item.body
             + f'<text class="label" font-size="{size}" x="{fmt(W / 2)}" y="{fmt(3)}">'
               f'{item.name} right</text>')
    left = (f'<g transform="translate({fmt(W)} 0) scale(-1 1)">{item.body}</g>'
            + f'<text class="label" font-size="{size}" x="{fmt(W / 2)}" y="{fmt(3)}">'
              f'{item.name} left</text>')
    return [Page(f"{item.name}-right", right, MAX_WIDTH, H),
            Page(f"{item.name}-left", left, MAX_WIDTH, H)]


def cover_page():
    """The cover: dual-unit calibration bars, as a logical page."""
    COVER_W, COVER_H = MAX_WIDTH, 205.9
    e = []
    e.append(f'<text class="title" x="{fmt(COVER_W / 2)}" y="25">'
             'Feather templates \u2014 mirrored pairs</text>')
    e.append(f'<text class="note" x="{fmt(COVER_W / 2)}" y="36">'
             'Print at 100% / actual size. Do not fit or scale. '
             'Verify with the bars below.</text>')

    def bar(y, length, major_step, majors, minor_step, minors, labels, unit):
        x0 = 40.0
        e.append(f'<line class="cal" x1="{fmt(x0)}" y1="{fmt(y)}" '
                 f'x2="{fmt(x0 + length)}" y2="{fmt(y)}"/>')
        for k in range(minors + 1):
            x = x0 + k * minor_step
            e.append(f'<line class="minor" x1="{fmt(x)}" y1="{fmt(y - 1.2)}" '
                     f'x2="{fmt(x)}" y2="{fmt(y + 1.2)}"/>')
        for k in range(majors + 1):
            x = x0 + k * major_step
            e.append(f'<line class="major" x1="{fmt(x)}" y1="{fmt(y - 3)}" '
                     f'x2="{fmt(x)}" y2="{fmt(y + 3)}"/>')
            e.append(f'<text class="num" x="{fmt(x)}" y="{fmt(y + 7)}">'
                     f'{labels[k]}</text>')
        e.append(f'<text class="caltext" x="{fmt(x0 + length / 2)}" '
                 f'y="{fmt(y - 9)}">{unit}</text>')

    bar(70.0, 100.0, 10.0, 10, 1.0, 100, [str(i * 10) for i in range(11)], "100 mm")
    bar(115.0, 101.6, 25.4, 4, 25.4 / 8.0, 32, ["0", "1", "2", "3", "4"],
        "4 in  (101.6 mm)")
    return Page("cover", "".join(e), COVER_W, COVER_H)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    # Read every item the manifest names, dispatching on what the aggregate
    # says each one is, and build it -> (frag, w, h), verifying as we go.
    # `raw` keeps the source Item too, which MirroredWholePage and AlignmentPage
    # need and MirroredPairs does not.
    listed = [name for section in SECTIONS for name in section.items]
    assert len(listed) == len(set(listed)), "the manifest lists an item twice"

    frags = {}
    raw = {}
    for name in listed:
        if name == PLACEMENT_GROUP:
            # The placement template: read the group the guides also come from.
            item = read_placement()
            ok, box = verify_body(item)
            assert ok, f"{item.name}: body outside its box {box}"
            raw[name] = item                      # no pair fragment: its own pages
            continue

        if name.endswith("-align"):
            # An overlay: read it by manifest name straight out of the align
            # layer, like a feather is read by name out of its family group.
            el = _def_group(name)
            assert (el.get("class") or "") == "align", (
                f"{name}: expected an <g class=\"align\">, got class "
                f"{el.get('class')!r}")
            item = read_align(name, el)
            ok, box = verify_body(item)
            assert ok, f"{item.name}: body outside its box {box}"
            raw[name] = item                      # no pair fragment: its own pages
            continue

        f = read_feather(name)
        ok, boxes = mirror_check(f)
        assert ok, f"{f.name}: mirror check failed {boxes}"
        item = feather_item(f)

        ok, box = verify_body(item)
        assert ok, f"{item.name}: body outside its box {box}"
        frag, w, h = build_pair(item)
        frags[name] = (frag, w, h)
        raw[name] = item

    # Every item the manifest names must have been read. The old assertion also
    # checked the other direction (nothing read that the manifest omits), which
    # cannot happen now: the manifest is what drives the reading.
    assert set(listed) == set(raw), f"manifest mismatch: {set(listed) ^ set(raw)}"

    ctx = Context(frags=frags, raw=raw)
    pages = [page for section in SECTIONS for page in section.pages(ctx)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Only clear pages this run is about to rewrite, instead of every
    # page-*.svg in the directory: a wrong OUT_DIR should leave stray files,
    # never delete someone else's output.
    stale = {f"page-{i:03d}.svg" for i in range(1, len(pages) + 1)}
    for p in OUT_DIR.glob("page-*.svg"):
        if p.name in stale:
            p.unlink()

    for i, page in enumerate(pages, 1):
        path = OUT_DIR / f"page-{i:03d}.svg"
        # Bytes, not write_text(encoding="utf-8"). Three things have to be pinned
        # down, and only writing the bytes pins all three:
        #   * no BOM -- write_text(encoding="utf-8") writes one on this platform,
        #     which changes every retained page's bytes;
        #   * the cover's em dash must be UTF-8 -- leaving the encoding implicit
        #     writes cp1252, which is not even valid UTF-8;
        #   * LF, not the CRLF that write_text() translates to on Windows.
        # The pages the committed PDF was built from have all three properties.
        svg = page_svg(page.title, page.content, page.w, page.h, page.extra_css)
        assert "\r" not in svg
        path.write_bytes(svg.encode("utf-8"))

    print(f"wrote {len(pages)} logical pages -> {OUT_DIR}")
    for i, page in enumerate(pages, 1):
        print(f"  page-{i:03d}  {page.w:7.1f} x {page.h:7.1f} mm  {page.title}")


if __name__ == "__main__":
    main()
