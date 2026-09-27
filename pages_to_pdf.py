#!/usr/bin/env python3
"""
pages_to_pdf.py
===============

Script 2 of the print pipeline: assemble the LOGICAL page SVGs into one true-scale
US Letter landscape PDF.

Reads mechanical/templates/print/logical-pages/page-NNN.svg in filename order and
emits one PDF. For each page:

  - fits the printable area -> one Letter sheet, the page placed whole at the margin;
  - bigger than the printable area -> tiled across `cols x rows` sheets with overlap
    and crop marks.

This script knows nothing about feathers or templates: it only sees a page's
width/height and its <title>. The two scripts meet only at the filesystem.

Output:
  mechanical/templates/print/feathers-letter-landscape.pdf
  mechanical/templates/print/sheets/            # per-sheet intermediates (gitignored)
  mechanical/templates/print/contact-sheet.png
"""

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

# cairosvg needs the cairo DLL that ships inside GStreamer. Point at it
# explicitly so the build does not depend on GStreamer staying on PATH. The
# environment must be set BEFORE importing cairosvg (it dlopens cairo on import).
CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
os.environ["CAIRO_PATH"] = CAIRO_BIN

import cairosvg
import pypdf
import pypdfium2 as pdfium
from PIL import Image

ROOT = Path(__file__).resolve().parent
PRINT_DIR = ROOT / "mechanical" / "templates" / "print"
PAGES_DIR = PRINT_DIR / "logical-pages"
SHEETS_DIR = PRINT_DIR / "sheets"          # intermediates (gitignored)
OUT_PDF = PRINT_DIR / "feathers-letter-landscape.pdf"
CONTACT_PNG = PRINT_DIR / "contact-sheet.png"

# --------------------------------------------------------------------------
# Paper + tiling constants — owned by this script, independent of Script 1.
# No assumption is made about how big Script 1's pages are: any page bigger
# than the printable area is tiled.
# --------------------------------------------------------------------------

PAPER_W, PAPER_H = 279.4, 215.9   # US Letter, landscape (mm)
MARGIN = 5.0                       # unprintable border
OVERLAP = 12.0                     # printed twice on adjacent tiles

pw = PAPER_W - 2.0 * MARGIN        # printable width  = 269.4 mm
ph = PAPER_H - 2.0 * MARGIN        # printable height = 205.9 mm
stride_x = pw - OVERLAP            # 257.4 mm
stride_y = ph - OVERLAP            # 193.9 mm

# A page may overshoot the printable area by up to FIT_SLACK mm and still get a
# single sheet: the small overflow lands in the margin (still on the paper, short
# of the bleed) instead of triggering a wasteful 1xN tile. Keep it <= MARGIN so no
# ink ever leaves the sheet. Raise it to MARGIN for maximum tolerance at the cost
# of printing further into the unprintable border.
FIT_SLACK = 2.0                    # mm


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


# --------------------------------------------------------------------------
# Crop-mark / tile-note CSS. The page SVGs carry their own outline/label CSS
# (carried over per-sheet); this script only adds what a physical sheet needs.
# `.note` is also defined by the pages, so redefining it here is harmless and
# keeps a tiled sheet self-contained even if a future page dropped it.
# --------------------------------------------------------------------------

CSS2 = """
.crop { stroke: #999999; stroke-width: 0.25; }
.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
"""

CLIP_DEF = (f'<defs><clipPath id="clip">'
            f'<rect x="{fmt(MARGIN)}" y="{fmt(MARGIN)}" '
            f'width="{fmt(pw)}" height="{fmt(ph)}"/>'
            f'</clipPath></defs>\n')


# --------------------------------------------------------------------------
# Reading the logical pages
# --------------------------------------------------------------------------

# Script 1 emits a clean, prefix-free SVG: a single <svg> root whose children are
# <title>, <style>, a white background <rect>, then the content at absolute mm
# positions. That lets us extract the content with plain string slices and keep it
# byte-for-byte (no ElementTree re-serialisation, which would re-introduce
# namespace prefixes).
_SVG_OPEN = re.compile(r"<svg\b[^>]*>")
_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
_RECT = re.compile(r"<rect\b[^>]*/>")


@dataclass
class Page:
    title: str
    W: float
    H: float
    style: str     # the page's CSS rules (carried onto each sheet)
    content: str   # the page's inner content, still in absolute mm page coords


def read_page(path):
    """Parse one logical page into (title, W, H, style, content)."""
    text = path.read_text(encoding="utf-8")

    om = _SVG_OPEN.search(text)
    assert om, f"{path}: no <svg> root element"
    open_tag = om.group(0)
    wm = re.search(r'\bwidth="([^"]+)"', open_tag)
    hm = re.search(r'\bheight="([^"]+)"', open_tag)
    assert wm and hm, f"{path}: <svg> is missing width/height"
    W = parse_mm(wm.group(1))
    H = parse_mm(hm.group(1))

    tm = _TITLE.search(text)
    title = tm.group(1).strip() if tm else path.stem

    sm = _STYLE.search(text)
    style = sm.group(1).strip() if sm else ""

    # Everything after the opening <svg>, minus the <title>, <style>, and the
    # white background <rect>. What remains is the content at absolute mm coords.
    inner = text[om.end():text.rfind("</svg>")]
    inner = _TITLE.sub("", inner, count=1)
    inner = _STYLE.sub("", inner, count=1)
    inner = _RECT.sub("", inner, count=1)
    content = inner.strip()

    assert content, f"{path}: no content extracted"
    return Page(title, W, H, style, content)


# --------------------------------------------------------------------------
# Sheet assembly
# --------------------------------------------------------------------------

def sheet_svg(body, style="", defs=""):
    """Wrap physical-sheet content in a Letter-landscape SVG, true scale."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{fmt(PAPER_W)}mm" height="{fmt(PAPER_H)}mm" '
            f'viewBox="0 0 {fmt(PAPER_W)} {fmt(PAPER_H)}">\n'
            f'<style type="text/css">{style}{CSS2}</style>\n'
            f'{defs}'
            f'<rect x="0" y="0" width="{fmt(PAPER_W)}" height="{fmt(PAPER_H)}" '
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


def build_sheets(page):
    """One Letter sheet per tile (or a single sheet for a page that fits).

    Returns (sheets, tiles, cols, rows) where tiles is a list of
    (transform_string, c, r) -- the emitted content transform for each sheet.
    """
    w, h = page.W, page.H
    cols = 1 if w <= pw + FIT_SLACK else math.ceil((w - pw) / stride_x) + 1
    rows = 1 if h <= ph + FIT_SLACK else math.ceil((h - ph) / stride_y) + 1

    if cols == 1 and rows == 1:
        tr = f"translate({fmt(MARGIN)} {fmt(MARGIN)})"
        body = f'<g transform="{tr}">{page.content}</g>'
        return [sheet_svg(body, style=page.style)], [(tr, 0, 0)], cols, rows

    sheets = []
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tx = MARGIN - c * stride_x
            ty = MARGIN - r * stride_y
            tr = f"translate({fmt(tx)} {fmt(ty)})"
            idx = r * cols + c + 1
            body = "\n".join([
                '<g clip-path="url(#clip)">'
                f'<g transform="{tr}">{page.content}</g>'
                '</g>',
                corner_ticks(),
                f'<text class="note" x="{fmt(PAPER_W / 2)}" '
                f'y="{fmt(PAPER_H - 2.5)}">'
                f'{page.title} \u00b7 tile {idx}/{cols * rows} \u00b7 {cols}x{rows}</text>',
            ])
            sheets.append(sheet_svg(body, style=page.style, defs=CLIP_DEF))
            tiles.append((tr, c, r))
    return sheets, tiles, cols, rows


# --------------------------------------------------------------------------
# Rendering (SVG -> PDF via cairosvg, merged with pypdf)
# --------------------------------------------------------------------------

def render_sheets(sheets):
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    for p in SHEETS_DIR.glob("sheet-*.svg"):
        p.unlink()
    for p in SHEETS_DIR.glob("sheet-*.pdf"):
        p.unlink()

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
    # Save via a temp name and replace: a viewer holding the PNG open blocks the
    # truncating save (OSError EINVAL) but not the atomic replace, so this keeps a
    # stale lock from aborting the run before the scale check.
    tmp = CONTACT_PNG.with_name(f"{CONTACT_PNG.stem}.tmp.png")
    canvas.save(tmp)
    os.replace(tmp, CONTACT_PNG)


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------

def verify_tiling(records):
    """Structural check: re-derive every page's tile grid and each tile's
    transform from the paper constants, and assert the emitted sheets match.
    This catches the 'silent drift' failure mode (a tile transform that no
    longer matches the grid formula, an off-by-one in cols/rows, ...)."""
    for page, sheets, tiles, cols, rows in records:
        w, h = page.W, page.H
        exp_cols = 1 if w <= pw + FIT_SLACK else math.ceil((w - pw) / stride_x) + 1
        exp_rows = 1 if h <= ph + FIT_SLACK else math.ceil((h - ph) / stride_y) + 1
        assert (cols, rows) == (exp_cols, exp_rows), (
            f"{page.title}: emitted {cols}x{rows} != re-derived {exp_cols}x{exp_rows}")
        assert len(sheets) == cols * rows, (
            f"{page.title}: {len(sheets)} sheets != {cols}x{rows} grid")
        for (tr, c, r), svg in zip(tiles, sheets):
            tx = MARGIN - c * stride_x
            ty = MARGIN - r * stride_y
            expect = f"translate({fmt(tx)} {fmt(ty)})"
            assert tr == expect, (
                f"{page.title} tile ({c},{r}): transform {tr!r} != re-derived {expect!r}")
            assert f'<g transform="{tr}">' in svg, (
                f"{page.title} tile ({c},{r}): transform not found in emitted sheet")


def verify_scale():
    """Rasterise the cover (page 1) at 300 dpi and measure both bars back."""
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
        # that plus anti-aliasing while still catching any real scale drift.
        return None if not xs else (max(xs) - min(xs)) / PPM

    # The cover is the first logical page, placed whole at (MARGIN, MARGIN), so
    # its bars -- drawn at x0=40, y=70 / y=115 in page coords -- sit at
    # x0=40+MARGIN, y=70+MARGIN / y=115+MARGIN on the sheet.
    mm_len = measure(70.0 + MARGIN, 40.0 + MARGIN, 100.0)
    in_len = measure(115.0 + MARGIN, 40.0 + MARGIN, 101.6)
    return mm_len, in_len


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    page_paths = sorted(PAGES_DIR.glob("page-*.svg"))
    assert page_paths, f"no logical pages found in {PAGES_DIR} — run make_logical_pages.py first"
    pages = [read_page(p) for p in page_paths]
    print(f"read {len(pages)} logical pages from {PAGES_DIR}")

    records = []
    sheets = []
    for i, page in enumerate(pages, 1):
        page_sheets, tiles, cols, rows = build_sheets(page)
        records.append((page, page_sheets, tiles, cols, rows))
        sheets.extend(page_sheets)
        where = "fit" if (cols, rows) == (1, 1) else f"tiled {cols}x{rows}"
        print(f"  page-{i:03d}  {page.W:7.1f} x {page.H:7.1f} mm  {where:10s}  {page.title}")

    verify_tiling(records)
    print("tiling structural check: OK")

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

    n_tiled = sum(1 for _, s, t, c, r in records if (c, r) != (1, 1))
    print(f"\n{len(pages)} logical pages -> {n} Letter sheets "
          f"({n_tiled} tiled, {len(pages) - n_tiled} fit)")
    print("all checks passed")


if __name__ == "__main__":
    main()
