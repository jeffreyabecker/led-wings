#!/usr/bin/env python3
"""
make_logical_pages.py
=====================

Script 1 of the print pipeline: build the mirrored-pair content and lay it out
into LOGICAL page SVGs.

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
IND_DIR = ROOT / "mechanical" / "templates" / "individuals"
OUT_DIR = ROOT / "mechanical" / "templates" / "print" / "logical-pages"

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
TOP_LINE_PAD = 25.0  # mm, horizontal space between the (non-mirrored) toplines

# Hard-coded item ids (right-hand orientation; the mirror is added by build_pair).
FEATHERS = [
    "P1", "P2", "P3", "P4", "P5",
    "S1", "S2", "S3", "S4",
    "A1", "A2", "A3",
    "PC1", "PC2",
    "SC1", "SC2", "SC3", "SC4",
    "MC1", "MC2", "MC3", "MC4",
    "LC1", "LC2", "LC3",
    "B1", "B2", "B3",
]
TOPLINES = [
    "A-topline", "B-topline", "LC-topline", "MC-topline",
    "P-topline", "PC-topline", "S-topline", "SC-topline",
]

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


class AlignmentGuides(Shelf):
    """The *-topline strip: wider spacing between the guides.

    Emits 2 pages: the strip, then the whole strip mirrored left to right (so
    the guide order reverses too). Each label is pre-flipped about its own axis
    so the page mirror leaves it at the mirrored position reading upright."""

    pad = TOP_LINE_PAD

    def pages(self, ctx):
        title = "/".join(self.items)
        right, w, h = shelf(self.items, ctx.frags, self.rotate, self.pad)

        # The mirrored strip is laid out in the same slots and then flipped as a
        # whole page, so the layout order reverses with the geometry.
        flipped = {}
        for name in self.items:
            item = ctx.raw[name]
            _, fw, fh = ctx.frags[name]
            flipped[name] = (item.body + preflip(guide_label(item), item.W / 2.0),
                             fw, fh)
        content, _, _ = shelf(self.items, flipped, self.rotate, self.pad)
        left = f'<g transform="translate({fmt(w)} 0) scale(-1 1)">{content}</g>'

        return [Page(f"{title}-right", right, w, h),
                Page(f"{title}-left", left, w, h)]


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
    # Print order for the guides strip (deliberately not TOPLINES' read order).
    AlignmentGuides("A-topline", "PC-topline", "SC-topline", "LC-topline",
                    "MC-topline", "B-topline", "P-topline", "S-topline"),
]


# --------------------------------------------------------------------------
# Reading the source files
# --------------------------------------------------------------------------

def read_feathers():
    feathers = []
    for name in FEATHERS:
        path = IND_DIR / f"{name}.svg"
        root = ET.parse(path).getroot()
        W = parse_mm(root.get("width"))
        H = parse_mm(root.get("height"))
        x0, y0, vw, vh = (float(v) for v in root.get("viewBox").split())

        # Identity mapping (width/height == viewBox extent) is what makes the
        # file true-scale: 1 user unit == 1 mm. Assert it, never assume it.
        assert abs(vw - W) < 1e-3 and abs(vh - H) < 1e-3, (
            f"{name}: viewBox {vw}x{vh} != width/height {W}x{H} — not identity")

        path_el = root.find(f".//{SVG_NS}path")
        d = " ".join(path_el.get("d").split())   # normalise any internal whitespace

        # B group is stored with its long axis horizontal; rotate 90 CW.
        rotate90 = name.startswith("B")

        feathers.append(Feather(name, W, H, x0, y0, d, rotate90))
    return feathers


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


def preflip(label, cx):
    """Mirror a label about x=cx.

    Composing this with an enclosing page mirror (translate(W 0) scale(-1 1))
    leaves only a translation, so the label lands at the mirrored position still
    reading upright instead of back to front."""
    return f'<g transform="translate({fmt(2.0 * cx)} 0) scale(-1 1)">{label}</g>'


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
# Independent transform evaluator (mirror check only)
# --------------------------------------------------------------------------

def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def apply_transform(tstr, points):
    """Apply an SVG transform string to points (translate/rotate/scale)."""
    ops = re.findall(r"(translate|rotate|scale)\(([^)]+)\)", tstr)
    out = []
    for (x, y) in points:
        for kind, args in reversed(ops):   # rightmost transform applies first
            vals = [float(v) for v in args.replace(",", " ").split()]
            if kind == "translate":
                x, y = x + vals[0], y + vals[1]
            elif kind == "rotate":
                a = math.radians(vals[0])
                x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            elif kind == "scale":
                sx, sy = vals[0], (vals[1] if len(vals) > 1 else vals[0])
                x, y = x * sx, y * sy
        out.append((x, y))
    return out


def mirror_check(f):
    """Assert the left half is an exact mirror of the right half, true size."""
    Wp, Hp = placed_size(f)
    rt = right_transform(f)
    right_t = f"translate({fmt(Wp + GAP)} 0)"
    left_t = f"translate({fmt(Wp)} 0) scale(-1 1)"
    corners = [(f.x0, f.y0), (f.x0 + f.W, f.y0),
               (f.x0, f.y0 + f.H), (f.x0 + f.W, f.y0 + f.H)]
    rbox = _bbox(apply_transform(right_t + " " + rt, corners))
    lbox = _bbox(apply_transform(left_t + " " + rt, corners))

    ok = (
        abs(rbox[0] - (Wp + GAP)) < 1e-3 and abs(rbox[1] - 0.0) < 1e-3
        and abs(rbox[2] - (2.0 * Wp + GAP)) < 1e-3 and abs(rbox[3] - Hp) < 1e-3
        and abs(lbox[0] - 0.0) < 1e-3 and abs(lbox[1] - 0.0) < 1e-3
        and abs(lbox[2] - Wp) < 1e-3 and abs(lbox[3] - Hp) < 1e-3
    )
    return ok, (rbox, lbox)


# --------------------------------------------------------------------------
# Template items (placement + alignment guides)
# --------------------------------------------------------------------------

def measure_ink(svg, dpi=150):
    """Render an SVG and return its ink bounding box (x0, y0, x1, y1) in mm."""
    pdf_bytes = cairosvg.svg2pdf(bytestring=svg.encode())
    img = pdfium.PdfDocument(pdf_bytes)[0].render(scale=dpi / 72.0).to_pil().convert("L")
    px = img.load()
    Wpx, Hpx = img.size
    PPM = dpi / 25.4
    xs = [x for y in range(Hpx) for x in range(Wpx) if px[x, y] < 128]
    ys = [y for y in range(Hpx) for x in range(Wpx) if px[x, y] < 128]
    if not xs:
        raise SystemExit("rendered SVG produced no ink")
    return (min(xs) / PPM, min(ys) / PPM, max(xs) / PPM, max(ys) / PPM)


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


def read_topline(name):
    """One *-topline.svg alignment guide as an Item (line + origin marker)."""
    root = ET.parse(IND_DIR / f"{name}.svg").getroot()
    W = parse_mm(root.get("width"))
    H = parse_mm(root.get("height"))
    x0, y0, vw, vh = (float(v) for v in root.get("viewBox").split())
    assert abs(vw - W) < 1e-3 and abs(vh - H) < 1e-3, (
        f"{name}: viewBox {vw}x{vh} != width/height {W}x{H} — not identity")

    g = root.find(f".//{SVG_NS}g")
    body = (f'<g transform="translate({fmt(-x0)} {fmt(-y0)})">'
            f'{_group_content(g)}</g>')
    return Item(name, W, H, body, inside_label=False, mirror=False)


def read_placement():
    """outline-toplines.svg — the whole-wing placement template — as an Item."""
    root = ET.parse(IND_DIR / "outline-toplines.svg").getroot()
    parts = []
    for g in root.findall(f".//{SVG_NS}g"):
        gt = g.get("transform") or ""
        inner = []
        for child in g:
            if child.tag == f"{SVG_NS}use":
                href = child.get("href") or ""
                fname, frag = href.split("#", 1)
                ref = ET.parse(IND_DIR / fname).getroot()
                target = ref.find(f".//*[@id='{frag}']")
                ut = child.get("transform")
                wrap = f' transform="{ut}"' if ut else ""
                inner.append(f'<g{wrap}>{_group_content(target)}</g>')
        parts.append(f'<g transform="{gt}">{"".join(inner)}</g>')
    content = "".join(parts)

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

def page_svg(title, content, w, h):
    """Wrap page content in a self-contained SVG with an explicit size."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(w)}mm" '
            f'height="{fmt(h)}mm" viewBox="0 0 {fmt(w)} {fmt(h)}">\n'
            f'<title>{title}</title>\n'
            f'<style type="text/css">{CSS}</style>\n'
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
    # Build every item -> (frag, w, h), verifying as we go. `raw` keeps the
    # source Item too, which MirroredWholePage needs to rebuild its halves.
    frags = {}
    raw = {}
    for f in read_feathers():
        ok, boxes = mirror_check(f)
        assert ok, f"{f.name}: mirror check failed {boxes}"
        item = feather_item(f)
        frag, w, h = build_pair(item)
        frags[f.name] = (frag, w, h)
        raw[f.name] = item

    for n in TOPLINES:
        t = read_topline(n)
        ok, box = verify_body(t)
        assert ok, f"{t.name}: body outside its box {box}"
        frag, w, h = build_pair(t)
        frags[t.name] = (frag, w, h)
        raw[t.name] = t

    t = read_placement()
    ok, box = verify_body(t)
    assert ok, f"{t.name}: body outside its box {box}"
    raw[t.name] = t

    # The manifest must list every item exactly once.
    listed = [name for section in SECTIONS for name in section.items]
    assert len(listed) == len(set(listed)), "the manifest lists an item twice"
    assert set(listed) == set(raw), f"manifest mismatch: {set(raw) ^ set(listed)}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob("page-*.svg"):
        p.unlink()

    ctx = Context(frags=frags, raw=raw)
    pages = [page for section in SECTIONS for page in section.pages(ctx)]

    for i, page in enumerate(pages, 1):
        path = OUT_DIR / f"page-{i:03d}.svg"
        path.write_text(page_svg(page.title, page.content, page.w, page.h),
                        encoding="utf-8")

    print(f"wrote {len(pages)} logical pages -> {OUT_DIR}")
    for i, page in enumerate(pages, 1):
        print(f"  page-{i:03d}  {page.w:7.1f} x {page.h:7.1f} mm  {page.title}")


if __name__ == "__main__":
    main()
