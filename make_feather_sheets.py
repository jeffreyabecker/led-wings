#!/usr/bin/env python3
"""
make_feather_sheets.py
======================

Generate a true-scale printable PDF of the feather templates.

Reads the 28 individual feather SVGs in mechanical/templates/individuals/
(each is a single outline path, right-hand orientation, millimetre units) and
writes one US Letter LANDSCAPE PDF where every feather appears as a mirrored
pair: the right-hand outline and its left-hand mirror, side by side.

Feathers too big for one sheet are tiled across multiple sheets with an overlap
so they can be joined after printing. The rest are packed several to a sheet.
Page 1 is a cover sheet with a calibration bar in both inches and millimetres.

This script is single-use scaffolding: written for clarity, run once, then
deleted. Output goes to mechanical/templates/print/.

True scale is guaranteed by never scaling anything: every value is millimetres
and each sheet's viewBox is the sheet size, so 1 SVG user unit == 1 mm.

Nothing here is reused from the earlier (deleted) generator.
"""

import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
IND_DIR = ROOT / "mechanical" / "templates" / "individuals"
PRINT_DIR = ROOT / "mechanical" / "templates" / "print"
SHEETS_DIR = PRINT_DIR / "sheets"          # intermediates (gitignored)
OUT_PDF = PRINT_DIR / "feathers-letter-landscape.pdf"
CONTACT_PNG = PRINT_DIR / "contact-sheet.png"

# cairosvg needs the cairo DLL that ships inside GStreamer. Point at it
# explicitly so the build does not depend on GStreamer staying on PATH.
CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"

# --------------------------------------------------------------------------
# Constants (all in one place — see print-plan.md §5)
# --------------------------------------------------------------------------

LETTER_IN_W, LETTER_IN_H = 8.5, 11.0                 # paper, inches (portrait)
LAND_W = LETTER_IN_H * 25.4                          # 279.4 mm  landscape width
LAND_H = LETTER_IN_W * 25.4                          # 215.9 mm  landscape height
MARGIN = 5.0                                         # unprintable border, mm
OVERLAP = 12.0                                       # printed twice on adjacent tiles
GAP = 10.0                                           # clear space between the two halves
PAD = 8.0                                            # space between neighbouring pairs

pw = LAND_W - 2.0 * MARGIN                           # printable width  = 269.4 mm
ph = LAND_H - 2.0 * MARGIN                           # printable height = 205.9 mm
stride_x = pw - OVERLAP                              # 257.4 mm
stride_y = ph - OVERLAP                              # 193.9 mm

# Hard-coded feather order (family-grouped). IDs map to individuals/<ID>.svg.
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

SVG_NS = "{http://www.w3.org/2000/svg}"

# NOTE: stroke-width and font-size are UNITLESS on purpose. Our user units are
# millimetres, so "0.5" means 0.5 mm. Writing "0.5mm" would trip a cairosvg
# quirk: it converts explicit CSS length units through a 96-dpi px scale and
# then misreads those px as user units, inflating them ~3.78x (0.5mm -> 1.78mm).
CSS = """
.outline { stroke: #000000; stroke-width: 0.5; fill: none; }
.label   { font-family: sans-serif; fill: #000000; text-anchor: middle; dominant-baseline: middle; }
.crop    { stroke: #999999; stroke-width: 0.25; }
.note    { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
.title   { font-family: sans-serif; fill: #000000; font-size: 9; text-anchor: middle; font-weight: bold; }
.cal     { stroke: #000000; stroke-width: 0.5; }
.minor   { stroke: #000000; stroke-width: 0.15; }
.major   { stroke: #000000; stroke-width: 0.5; }
.num     { font-family: sans-serif; fill: #000000; font-size: 3.5; text-anchor: middle; }
.caltext { font-family: sans-serif; fill: #000000; font-size: 6; text-anchor: middle; font-weight: bold; }
"""

CLIP_DEF = (f'<defs><clipPath id="clip">'
            f'<rect x="{MARGIN}" y="{MARGIN}" width="{pw}" height="{ph}"/>'
            f'</clipPath></defs>\n')


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

        # The identity mapping (width/height == viewBox extent) is what makes
        # the file true-scale: 1 user unit == 1 mm. Assert it, never assume it.
        assert abs(vw - W) < 1e-3 and abs(vh - H) < 1e-3, (
            f"{name}: viewBox {vw}x{vh} != width/height {W}x{H} — not identity")

        path_el = root.find(f".//{SVG_NS}path")
        d = " ".join(path_el.get("d").split())   # normalise any internal whitespace

        # B group is stored with its long axis horizontal; rotate 90 CW (§7).
        rotate90 = name.startswith("B")

        feathers.append(Feather(name, W, H, x0, y0, d, rotate90))
    return feathers


# --------------------------------------------------------------------------
# Pair geometry (print-plan.md §7)
# --------------------------------------------------------------------------

def placed_size(f):
    """Width x height of the outline after any rotation (the local pair half)."""
    return (f.H, f.W) if f.rotate90 else (f.W, f.H)


def right_transform(f):
    """Transform string that puts the outline in its local [0,W]x[0,H] frame."""
    if f.rotate90:
        # rotate 90 deg clockwise about the viewBox centre, then slide the
        # rotated box's top-left corner to the local origin.
        cx = f.x0 + f.W / 2.0
        cy = f.y0 + f.H / 2.0
        return (f"translate({fmt(f.H / 2.0)} {fmt(f.W / 2.0)}) rotate(90) "
                f"translate({fmt(-cx)} {fmt(-cy)})")
    return f"translate({fmt(-f.x0)} {fmt(-f.y0)})"


def build_pair(f):
    """Return (fragment, pair_w, pair_h) in the pair's local frame."""
    Wp, Hp = placed_size(f)
    rt = right_transform(f)
    size = fmt(label_size(Wp, Hp))

    right = f'<g transform="{rt}"><path class="outline" d="{f.d}"/></g>'
    # Mirror about the vertical axis at x = Wp + GAP/2:
    #   translate(2*Wp + GAP, 0) scale(-1, 1)  then the same right placement.
    left = (f'<g transform="translate({fmt(2.0 * Wp + GAP)} 0) scale(-1 1)">'
            f'<g transform="{rt}"><path class="outline" d="{f.d}"/></g></g>')

    labels = (
        f'<text class="label" font-size="{size}" '
        f'x="{fmt(Wp / 2.0)}" y="{fmt(Hp / 2.0)}">{f.name}</text>'
        f'<text class="label" font-size="{size}" '
        f'x="{fmt(Wp + GAP + Wp / 2.0)}" y="{fmt(Hp / 2.0)}">{f.name}</text>'
    )

    return right + left + labels, 2.0 * Wp + GAP, Hp


# --------------------------------------------------------------------------
# Independent transform evaluator (used only to verify the mirror is exact)
# --------------------------------------------------------------------------

def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def apply_transform(tstr, points):
    """Apply an SVG transform string to points. Handles the exact forms this
    script emits: translate(...), rotate(...), scale(...), chained."""
    ops = re.findall(r"(translate|rotate|scale)\(([^)]+)\)", tstr)
    out = []
    for (x, y) in points:
        # SVG applies the rightmost transform first, then leftward.
        for kind, args in reversed(ops):
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
    """Assert the left half is an exact mirror of the right half, true size.

    Applies the emitted transforms to the outline's viewBox corners and checks
    the right half lands on [0,W]x[0,H] and the left on its mirror across the
    axis, GAP clear of it. This re-derives the geometry from the emitted
    strings, so it is an independent check rather than restating the formula.
    """
    Wp, Hp = placed_size(f)
    rt = right_transform(f)
    left_t = f"translate({fmt(2.0 * Wp + GAP)} 0) scale(-1 1)"
    corners = [(f.x0, f.y0), (f.x0 + f.W, f.y0),
               (f.x0, f.y0 + f.H), (f.x0 + f.W, f.y0 + f.H)]
    rbox = _bbox(apply_transform(rt, corners))
    lbox = _bbox(apply_transform(left_t + " " + rt, corners))

    ok = (
        abs(rbox[0] - 0.0) < 1e-3 and abs(rbox[1] - 0.0) < 1e-3
        and abs(rbox[2] - Wp) < 1e-3 and abs(rbox[3] - Hp) < 1e-3
        and abs(lbox[0] - (Wp + GAP)) < 1e-3
        and abs(lbox[2] - (2.0 * Wp + GAP)) < 1e-3
        and abs(lbox[1] - 0.0) < 1e-3 and abs(lbox[3] - Hp) < 1e-3
    )
    return ok, (rbox, lbox)


# --------------------------------------------------------------------------
# Sheet assembly
# --------------------------------------------------------------------------

def sheet_svg(parts, defs=""):
    body = "\n".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{fmt(LAND_W)}mm" height="{fmt(LAND_H)}mm" '
            f'viewBox="0 0 {fmt(LAND_W)} {fmt(LAND_H)}">\n'
            f'<style type="text/css">{CSS}</style>\n'
            f'{defs}'
            f'<rect x="0" y="0" width="{fmt(LAND_W)}" height="{fmt(LAND_H)}" '
            f'fill="#ffffff"/>\n'
            f'{body}\n</svg>\n')


def corner_ticks():
    """Small L-marks at the four printable corners, for lining tiles up."""
    L = 5.0
    segs = []
    for cx in (MARGIN, MARGIN + pw):
        for cy in (MARGIN, MARGIN + ph):
            sx = -1.0 if cx == MARGIN else 1.0
            sy = -1.0 if cy == MARGIN else 1.0
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx + sx * L)}" y2="{fmt(cy)}"/>')
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx)}" y2="{fmt(cy + sy * L)}"/>')
    return "<g>" + "".join(segs) + "</g>"


def tiled_sheets(name, frag, w, h):
    """One sheet per tile of an oversized pair (print-plan.md §9)."""
    cols = 1 if w <= pw else math.ceil((w - pw) / stride_x) + 1
    rows = 1 if h <= ph else math.ceil((h - ph) / stride_y) + 1
    sheets = []
    for r in range(rows):
        for c in range(cols):
            tx = MARGIN - c * stride_x
            ty = MARGIN - r * stride_y
            idx = r * cols + c + 1
            parts = [
                '<g clip-path="url(#clip)">'
                f'<g transform="translate({fmt(tx)} {fmt(ty)})">{frag}</g>'
                '</g>',
                corner_ticks(),
                f'<text class="note" x="{fmt(LAND_W / 2)}" y="{fmt(LAND_H - 2.5)}">'
                f'{name} \u00b7 tile {idx}/{cols * rows} \u00b7 {cols}x{rows}</text>',
            ]
            sheets.append((f"{name} tile {idx}/{cols * rows}", sheet_svg(parts, CLIP_DEF)))
    return sheets


def pack_small(pairs):
    """Shelf-pack pairs that fit whole (print-plan.md §10). Returns sheets."""
    sheets = []
    cur = []
    x = MARGIN
    y = MARGIN
    row_h = 0.0
    for name, frag, w, h in pairs:
        if x + w > MARGIN + pw:                 # no room in this row -> wrap
            x = MARGIN
            y += row_h + PAD
            row_h = 0.0
        if y + h > MARGIN + ph:                 # sheet full -> flush
            sheets.append(cur)
            cur = []
            x = MARGIN
            y = MARGIN
            row_h = 0.0
        cur.append((name, frag, x, y))
        x += w + PAD
        row_h = max(row_h, h)
    if cur:
        sheets.append(cur)

    out = []
    for sheet in sheets:
        parts = [f'<g transform="translate({fmt(x)} {fmt(y)})">{frag}</g>'
                 for name, frag, x, y in sheet]
        out.append(("/".join(n for n, _, _, _ in sheet), sheet_svg(parts)))
    return out


def cover_sheet():
    """Page 1: calibration bars in mm and inches (print-plan.md §11)."""
    e = []
    e.append(f'<text class="title" x="{fmt(LAND_W / 2)}" y="25">'
             'Feather templates \u2014 mirrored pairs</text>')
    e.append(f'<text class="note" x="{fmt(LAND_W / 2)}" y="36">'
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
    return sheet_svg(e)


# --------------------------------------------------------------------------
# Rendering (SVG -> PDF via cairosvg, merged with pypdf)
# --------------------------------------------------------------------------

def render_sheets(sheets):
    os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
    os.environ["CAIRO_PATH"] = CAIRO_BIN
    import cairosvg
    import pypdf

    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    PRINT_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = []
    for i, svg in enumerate(sheets, 1):
        sp = SHEETS_DIR / f"sheet-{i:03d}.svg"
        pp = SHEETS_DIR / f"sheet-{i:03d}.pdf"
        sp.write_text(svg, encoding="utf-8")
        cairosvg.svg2pdf(url=str(sp), write_to=str(pp))
        pdfs.append(pp)

    writer = pypdf.PdfWriter()
    for p in pdfs:
        writer.append(str(p))
    writer.write(OUT_PDF)
    return len(pdfs)


def contact_sheet(n_pages):
    import pypdfium2 as pdfium
    from PIL import Image

    doc = pdfium.PdfDocument(str(OUT_PDF))
    cols = 6
    rows = math.ceil(n_pages / cols)
    thumbs = [doc[i].render(scale=1.0).to_pil() for i in range(n_pages)]
    tw, th = thumbs[0].size
    canvas = Image.new("RGB", (cols * tw, rows * th), "white")
    for i, im in enumerate(thumbs):
        r, c = divmod(i, cols)
        canvas.paste(im, (c * tw, r * th))
    canvas.save(CONTACT_PNG)


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------

def verify_scale():
    """Rasterise the cover page at 300 dpi and measure both bars back."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(OUT_PDF))
    img = doc[0].render(scale=300.0 / 72.0).to_pil().convert("L")
    px = img.load()
    W, H = img.size
    PPM = 300.0 / 25.4                       # pixels per millimetre

    def measure(y_mm, x0_mm, length_mm):
        yc = int(round(y_mm * PPM))
        half = 12                            # ~1 mm band: the bar line, not its labels
        xs = []
        for yy in range(max(0, yc - half), min(H, yc + half)):
            for xx in range(int((x0_mm - 2) * PPM), int((x0_mm + length_mm + 2) * PPM)):
                if px[xx, yy] < 128:
                    xs.append(xx)
        # Ink extent includes the 0.5 mm stroke (0.25 mm each end), so the span
        # runs ~0.5 mm longer than the geometric length; +-1 mm tolerance covers
        # that plus anti-aliasing, while still catching any real scale drift.
        return None if not xs else (max(xs) - min(xs)) / PPM

    mm_len = measure(70.0, 40.0, 100.0)
    in_len = measure(115.0, 40.0, 101.6)
    return mm_len, in_len


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    feathers = read_feathers()
    print(f"read {len(feathers)} feathers")

    # Build every pair, verify the mirror is exact, and split big / small.
    big, small = [], []
    for f in feathers:
        ok, boxes = mirror_check(f)
        assert ok, f"{f.name}: mirror check failed {boxes}"
        frag, w, h = build_pair(f)
        if w <= pw and h <= ph:
            small.append((f.name, frag, w, h))
        else:
            big.append((f.name, frag, w, h))

    # Assemble sheets: cover first, then tiled big feathers, then packed smalls.
    sheet_labels = ["cover"]
    sheets = [cover_sheet()]
    for name, frag, w, h in big:
        for label, svg in tiled_sheets(name, frag, w, h):
            sheet_labels.append(label)
            sheets.append(svg)
    for label, svg in pack_small(small):
        sheet_labels.append(label)
        sheets.append(svg)

    n = render_sheets(sheets)
    print(f"wrote {n} pages -> {OUT_PDF}")

    contact_sheet(n)
    print(f"contact sheet -> {CONTACT_PNG}")

    mm_len, in_len = verify_scale()
    print("\nverification:")
    ok_mm = mm_len is not None and abs(mm_len - 100.0) < 1.0
    ok_in = in_len is not None and abs(in_len - 101.6) < 1.0
    print(f"  cover 100 mm bar measured {mm_len} mm   -> {'OK' if ok_mm else 'FAIL'}")
    print(f"  cover 4 in  bar measured {in_len} mm   -> {'OK' if ok_in else 'FAIL'}")
    assert ok_mm and ok_in, "scale verification FAILED"

    print(f"\n{len(feathers)} feathers, {n} pages:")
    print("  tiled (oversized):", ", ".join(name for name, *_ in big) or "none")
    print("  packed (fit whole):", ", ".join(name for name, *_ in small) or "none")
    print("\nall checks passed")


if __name__ == "__main__":
    main()
