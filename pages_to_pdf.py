#!/usr/bin/env python3
"""
pages_to_pdf.py
===============

Script 2 of the print pipeline: take the logical-page SVGs (from
make_logical_pages.py) in filename order and build one PDF of US Letter
LANDSCAPE sheets.

For each page:
  - fits the printable area  -> one sheet, page placed at the margin;
  - bigger than the printable -> tiled across cols x rows sheets with overlap
    and crop marks, so the pieces can be joined after printing.

This script knows nothing about feathers or templates -- it only reads page
width/height and a <title> label. The two scripts are fully independent.

Output: mechanical/templates/print/feathers-letter-landscape.pdf
"""

import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# --------------------------------------------------------------------------
# Paths + cairo
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
PAGES_DIR = ROOT / "mechanical" / "templates" / "print" / "logical-pages"
PRINT_DIR = ROOT / "mechanical" / "templates" / "print"
SHEETS_DIR = PRINT_DIR / "sheets"          # intermediates (gitignored)
OUT_PDF = PRINT_DIR / "feathers-letter-landscape.pdf"
CONTACT_PNG = PRINT_DIR / "contact-sheet.png"

CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
os.environ["CAIRO_PATH"] = CAIRO_BIN

import cairosvg
import pypdf
import pypdfium2 as pdfium
from PIL import Image

# --------------------------------------------------------------------------
# Paper constants (US Letter landscape)
# --------------------------------------------------------------------------

PAPER_W, PAPER_H = 279.4, 215.9   # mm
MARGIN = 5.0                       # unprintable border, mm
OVERLAP = 12.0                     # printed twice on adjacent tiles, mm

pw = PAPER_W - 2.0 * MARGIN        # printable width  = 269.4 mm
ph = PAPER_H - 2.0 * MARGIN        # printable height = 205.9 mm
stride_x = pw - OVERLAP            # 257.4 mm
stride_y = ph - OVERLAP            # 193.9 mm

SVG_NS = "{http://www.w3.org/2000/svg}"

# Script 2's own styling: crop marks and tile notes. (The page content carries
# its own <style> from Script 1; these class names are distinct.)
CSS = """
.crop      { stroke: #999999; stroke-width: 0.25; }
.tile-note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
"""

CLIP_DEF = (f'<defs><clipPath id="clip">'
            f'<rect x="{MARGIN}" y="{MARGIN}" width="{pw}" height="{ph}"/>'
            f'</clipPath></defs>')


def fmt(x):
    """A millimetre value as a compact decimal (no trailing zeros)."""
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def parse_mm(s):
    return float(str(s).replace("mm", "").strip())


# --------------------------------------------------------------------------
# Reading logical pages
# --------------------------------------------------------------------------

def read_page(path):
    """Return (title, W, H, content) for one logical page."""
    root = ET.parse(path).getroot()
    W = parse_mm(root.get("width"))
    H = parse_mm(root.get("height"))
    title_el = root.find(f"{SVG_NS}title")
    title = (title_el.text or "").strip() if title_el is not None else ""
    # Everything except the <title> (metadata) is drawable content. Script 1
    # emits clean SVGs (default namespace only), so re-serialising children is
    # safe; cairosvg reads the ns prefixes ET adds without trouble.
    content = "".join(
        ET.tostring(child, encoding="unicode")
        for child in root
        if child.tag != f"{SVG_NS}title"
    )
    return title, W, H, content


# --------------------------------------------------------------------------
# Sheet assembly
# --------------------------------------------------------------------------

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


def sheet_svg(content_inside, tiled=False, note=""):
    """Wrap placed content in a Letter sheet. Tiled sheets get crop marks and a
    margin note; fitting pages get neither."""
    parts = [
        f'<style type="text/css">{CSS}</style>',
        f'<rect width="{fmt(PAPER_W)}" height="{fmt(PAPER_H)}" fill="#ffffff"/>',
        content_inside,
    ]
    if tiled:
        parts.append(corner_ticks())
        parts.append(f'<text class="tile-note" x="{fmt(PAPER_W / 2)}" '
                     f'y="{fmt(PAPER_H - 2.5)}">{note}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{fmt(PAPER_W)}mm" height="{fmt(PAPER_H)}mm" '
            f'viewBox="0 0 {fmt(PAPER_W)} {fmt(PAPER_H)}">\n'
            + "\n".join(parts) + "\n</svg>\n")


def tiled_sheets(title, content, W, H):
    """One sheet per tile of a page too big for one printable area."""
    cols = 1 if W <= pw else math.ceil((W - pw) / stride_x) + 1
    rows = 1 if H <= ph else math.ceil((H - ph) / stride_y) + 1
    sheets = []
    for r in range(rows):
        for c in range(cols):
            tx = MARGIN - c * stride_x
            ty = MARGIN - r * stride_y
            idx = r * cols + c + 1
            inside = (f'<g clip-path="url(#clip)">'
                      f'<g transform="translate({fmt(tx)} {fmt(ty)})">{content}</g>'
                      f'</g>')
            note = f'{title} \u00b7 tile {idx}/{cols * rows} \u00b7 {cols}x{rows}'
            sheets.append(sheet_svg(inside, tiled=True, note=note))
    return sheets


# --------------------------------------------------------------------------
# Rendering + merge
# --------------------------------------------------------------------------

def render_sheets(sheets):
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
    """Rasterise the cover (sheet 1) at 300 dpi and measure both bars back.

    The cover's bars sit at x=40..140/141.6, y=70 and y=115 within the cover
    page; Script 2 places that page at the 5 mm margin, so on the sheet they are
    at y=75 and y=120, x from 45 mm."""
    doc = pdfium.PdfDocument(str(OUT_PDF))
    img = doc[0].render(scale=300.0 / 72.0).to_pil().convert("L")
    px = img.load()
    W, H = img.size
    PPM = 300.0 / 25.4

    def measure(y_mm, x0_mm, length_mm):
        yc = int(round(y_mm * PPM))
        half = 12
        xs = []
        for yy in range(max(0, yc - half), min(H, yc + half)):
            for xx in range(int((x0_mm - 2) * PPM), int((x0_mm + length_mm + 2) * PPM)):
                if px[xx, yy] < 128:
                    xs.append(xx)
        return None if not xs else (max(xs) - min(xs)) / PPM

    mm_len = measure(75.0, 45.0, 100.0)
    in_len = measure(120.0, 45.0, 101.6)
    return mm_len, in_len


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    pages = sorted(PAGES_DIR.glob("page-*.svg"))
    if not pages:
        raise SystemExit(f"no pages found in {PAGES_DIR} — run make_logical_pages.py first")

    sheets = []
    for path in pages:
        title, W, H, content = read_page(path)
        if W <= pw + 1e-6 and H <= ph + 1e-6:
            inside = f'<g transform="translate({fmt(MARGIN)} {fmt(MARGIN)})">{content}</g>'
            sheets.append(sheet_svg(inside))
        else:
            sheets.extend(tiled_sheets(title, content, W, H))

    n = render_sheets(sheets)
    print(f"wrote {n} sheets -> {OUT_PDF}")

    contact_sheet(n)
    print(f"contact sheet -> {CONTACT_PNG}")

    mm_len, in_len = verify_scale()
    print("\nverification:")
    ok_mm = mm_len is not None and abs(mm_len - 100.0) < 1.0
    ok_in = in_len is not None and abs(in_len - 101.6) < 1.0
    print(f"  cover 100 mm bar measured {mm_len} mm   -> {'OK' if ok_mm else 'FAIL'}")
    print(f"  cover 4 in  bar measured {in_len} mm   -> {'OK' if ok_in else 'FAIL'}")
    assert ok_mm and ok_in, "scale verification FAILED"

    print(f"\n{len(pages)} logical pages -> {n} sheets; all checks passed")


if __name__ == "__main__":
    main()
