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

# Ordered pages. Each entry is ONE logical page: a list of item specs.
# An item spec is a bare name, or a (name, rotation, x, y) tuple:
#   "P1"                -> auto-layout, no rotation
#   ("S4", 90)          -> auto-layout, rotated 90 deg clockwise
#   ("S3", 0, 10, 20)   -> placed at x=10, y=20 mm (top-left), no rotation
#   ("S3", 90, 10, 20)  -> placed at x=10, y=20, rotated 90 deg
# rotation: degrees clockwise about the pair's centre. x/y: None -> auto row
# layout (wrap at MAX_WIDTH); a number -> place exactly there. The cover is
# always page 1. Every item appears exactly once.
PAGES = [
    ["P1"], ["P2"], ["P3"], ["P4"], ["P5"],
    ["S1"], ["S2"], ["S3"], ["S4"], 
    ["B1"], ["B2"], ["B3"],
    ["A1", "A2", "A3"], ["PC1", "PC2"],
    ["SC1", "SC2"], ["SC3"], ["SC4"],
    ["MC1", "MC2"], ["MC3", "MC4"], 
    ["LC1", "LC2", "LC3"], 

    ["outline-toplines"],
    
    ["A-topline", "PC-topline", "SC-topline","LC-topline", "MC-topline", "B-topline", "P-topline",  "S-topline" ],
]

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


def build_pair(item):
    """Return (fragment, w, h) in the local frame.

    A mirrored item is a left/right pair; a non-mirrored item (the toplines) is
    a single fragment with one label and no left/right distinction."""
    W, H = item.W, item.H
    if item.inside_label:
        size = fmt(label_size(W, H))
        y = H / 2.0
    else:
        size = fmt(min(6.0, max(3.0, W / 12.0)))
        y = 3.0

    if not item.mirror:
        # single guide line; label runs along it (rotated 90 deg about its centre)
        cx, cy = W / 2.0, H / 2.0
        label = (f'<text class="label" font-size="{size}" x="{fmt(cx)}" y="{fmt(cy)}" '
                 f'transform="rotate(90 {fmt(cx)} {fmt(cy)})">{item.name}</text>')
        return item.body + label, W, H

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


def placement_halves(item):
    """outline-toplines gets no side-by-side pair: the left and right versions are
    two separate single-half pages (right first, then left)."""
    W, H = item.W, item.H
    size = fmt(min(6.0, max(3.0, W / 12.0)))
    right = (item.body
             + f'<text class="label" font-size="{size}" x="{fmt(W / 2)}" y="{fmt(3)}">'
               f'outline-toplines right</text>')
    left = (f'<g transform="translate({fmt(W)} 0) scale(-1 1)">{item.body}</g>'
            + f'<text class="label" font-size="{size}" x="{fmt(W / 2)}" y="{fmt(3)}">'
              f'outline-toplines left</text>')
    return [("outline-toplines-right", right, MAX_WIDTH, H),
            ("outline-toplines-left", left, MAX_WIDTH, H)]


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


def normalize_item(spec):
    """A bare name -> (name, 0, None, None); a tuple -> (name, rotation, x, y)."""
    if isinstance(spec, str):
        return (spec, 0.0, None, None)
    name = spec[0]
    rot = float(spec[1])
    x = spec[2] if len(spec) >= 4 else None
    y = spec[3] if len(spec) >= 4 else None
    return (name, rot, x, y)


def layout_group(specs, items):
    """Place pairs (rotation + optional x/y) and return (content, w, h).

    x/y None -> auto row layout (wrap at MAX_WIDTH, using the rotated size);
    x/y given -> placed exactly there. Rotation is clockwise degrees about the
    pair's centre. Page size is the union of the placed boxes."""
    placed = []
    x = y = 0.0
    row_h = 0.0
    max_y = 0.0
    for spec in specs:
        name, rot, px, py = normalize_item(spec)
        frag, w, h = items[name]
        RW, RH = rotated_bbox(w, h, rot)
        pad = TOP_LINE_PAD if name.endswith("-topline") else PAD
        if px is None and py is None:
            if x > 0 and x + RW > MAX_WIDTH:
                y += row_h + PAD
                x = 0.0
                row_h = 0.0
            px, py = x, y
            x += RW + pad
            row_h = max(row_h, RH)
        placed.append((frag, placed_transform(w, h, rot, px, py)))
        max_y = max(max_y, py + RH)
    content = "".join(f'<g transform="{tr}">{frag}</g>' for frag, tr in placed)
    return content, MAX_WIDTH, max_y


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
    return "cover", "".join(e), COVER_W, COVER_H


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    # Build every item -> (frag, w, h), verifying as we go.
    items = {}
    for f in read_feathers():
        ok, boxes = mirror_check(f)
        assert ok, f"{f.name}: mirror check failed {boxes}"
        item = feather_item(f)
        frag, w, h = build_pair(item)
        items[f.name] = (frag, w, h)

    for n in TOPLINES:
        t = read_topline(n)
        ok, box = verify_body(t)
        assert ok, f"{t.name}: body outside its box {box}"
        frag, w, h = build_pair(t)
        items[t.name] = (frag, w, h)

    t = read_placement()
    ok, box = verify_body(t)
    assert ok, f"{t.name}: body outside its box {box}"
    halves = placement_halves(t)   # left + right, each its own page

    # PAGES must list every item exactly once.
    listed = [normalize_item(s)[0] for page in PAGES for s in page]
    expected = set(FEATHERS) | set(TOPLINES) | {"outline-toplines"}
    assert len(listed) == len(set(listed)), "PAGES has a duplicate item"
    assert set(listed) == expected, f"PAGES mismatch: {expected ^ set(listed)}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in OUT_DIR.glob("page-*.svg"):
        p.unlink()

    pages = [cover_page()]
    for group in PAGES:
        specs = [normalize_item(s) for s in group]
        if len(specs) == 1 and specs[0][0] == "outline-toplines":
            pages.extend(halves)   # two dedicated pages: right, then left
            continue
        title = "/".join(s[0] for s in specs)
        content, pw, ph = layout_group(specs, items)
        pages.append((title, content, pw, ph))

    for i, (title, content, pw, ph) in enumerate(pages, 1):
        path = OUT_DIR / f"page-{i:03d}.svg"
        path.write_text(page_svg(title, content, pw, ph), encoding="utf-8")

    print(f"wrote {len(pages)} logical pages -> {OUT_DIR}")
    for i, (title, _, pw, ph) in enumerate(pages, 1):
        print(f"  page-{i:03d}  {pw:7.1f} x {ph:7.1f} mm  {title}")


if __name__ == "__main__":
    main()
