#!/usr/bin/env python3
"""
make_print_sheets.py
====================

Script 2 of the print pipeline: lay the LOGICAL page SVGs out onto print sheets,
one sheet per tile, targeting a chosen print page size.

Reads templates/print/logical-pages/page-NNN.svg in filename order and emits one
sheet SVG per tile. For each page:

  - fits the printable area -> one sheet, the page placed whole at the margin;
  - bigger than the printable area -> tiled across `cols x rows` sheets with
    overlap and crop marks.

This script knows nothing about feathers or templates: it only sees a page's
width/height and its <title>. The pipeline scripts meet only at the filesystem.

The paper size, margin, overlap, fit slack and cut-guide bleed are command-line
flags (see templates/split-pdf-script-plan.md §2a), with US Letter landscape as
the default, so a second page size is reachable without editing the script.
`pw`/`ph`/`stride_x`/`stride_y` stay *derived*, never passed, so a caller cannot
hand in a combination the tiling formula disagrees with.

Output:
  templates/print/sheets/sheet-NNN.svg      # per-sheet intermediates (gitignored)
  templates/print/sheets/manifest.json      # what sheets_to_pdf.py needs
"""

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRINT_DIR = ROOT / "templates" / "print"
PAGES_DIR = PRINT_DIR / "logical-pages"
SHEETS_DIR = PRINT_DIR / "sheets"          # intermediates (gitignored)
MANIFEST = SHEETS_DIR / "manifest.json"

# --------------------------------------------------------------------------
# Paper + tiling geometry. The defaults are US Letter landscape; the values are
# module-level so build_sheets()/verify_tiling() read them by name, but main()
# overwrites them from the --paper/--margin/--overlap/--slack/--bleed flags via
# _set_geometry() before any sheet is built. The derived values (pw, ph,
# stride_x, stride_y, CLIP_DEF) are recomputed there too, never taken from the
# caller, so a flag combination the tiling formula disagrees with is rejected
# rather than silently drifted (that is exactly what verify_tiling() re-checks).
# --------------------------------------------------------------------------

PAPER_W, PAPER_H = 279.4, 215.9   # US Letter, landscape (mm)
MARGIN = 5.0                       # unprintable border (the printer cannot ink here)
OVERLAP = 12.0                     # printed twice on adjacent tiles
FIT_SLACK = 2.0                    # mm, overshoot that still gets one sheet
BLEED = 0.0                        # mm, extra inset (inside the margin) for the cut guides

# Derived — set by _set_geometry():
pw = ph = stride_x = stride_y = None
CLIP_DEF = None


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


def _set_geometry(paper_w, paper_h, margin, overlap, slack, bleed):
    """Set the paper geometry from the command line, validating the flags.

    The assertions are the price of taking the size as flags (§2a): a margin
    that leaves no printable area, an overlap wider than the printable area, a
    slack larger than the margin (which would let a page print into the
    unprintable border), and a bleed that is negative or leaves no room for the
    cut guides must all be rejected before a sheet is built."""
    global PAPER_W, PAPER_H, MARGIN, OVERLAP, FIT_SLACK, BLEED
    global pw, ph, stride_x, stride_y, CLIP_DEF

    assert margin * 2.0 < paper_w and margin * 2.0 < paper_h, (
        f"margin {margin} mm leaves no printable area on a {paper_w}x{paper_h} mm sheet")
    printable_w = paper_w - 2.0 * margin
    printable_h = paper_h - 2.0 * margin
    assert overlap < printable_w and overlap < printable_h, (
        f"overlap {overlap} mm is wider than the printable area "
        f"{printable_w}x{printable_h} mm")
    assert slack <= margin, (
        f"slack {slack} mm is larger than the margin {margin} mm, so a page could "
        f"print into the unprintable border")
    assert bleed >= 0.0, f"bleed cannot be negative (got {bleed} mm)"
    assert 2.0 * bleed < printable_w and 2.0 * bleed < printable_h, (
        f"bleed {bleed} mm leaves no room for the cut guides in the "
        f"{printable_w}x{printable_h} mm printable area")

    PAPER_W, PAPER_H = paper_w, paper_h
    MARGIN = margin
    OVERLAP = overlap
    FIT_SLACK = slack
    BLEED = bleed

    pw = PAPER_W - 2.0 * MARGIN        # printable width
    ph = PAPER_H - 2.0 * MARGIN        # printable height
    stride_x = pw - OVERLAP
    stride_y = ph - OVERLAP

    CLIP_DEF = (f'<defs><clipPath id="clip">'
                f'<rect x="{fmt(MARGIN)}" y="{fmt(MARGIN)}" '
                f'width="{fmt(pw)}" height="{fmt(ph)}"/>'
                f'</clipPath></defs>\n')


_set_geometry(PAPER_W, PAPER_H, MARGIN, OVERLAP, FIT_SLACK, BLEED)


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
    """Wrap physical-sheet content in a paper-sized SVG, true scale."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{fmt(PAPER_W)}mm" height="{fmt(PAPER_H)}mm" '
            f'viewBox="0 0 {fmt(PAPER_W)} {fmt(PAPER_H)}">\n'
            f'<style type="text/css">{style}{CSS2}</style>\n'
            f'{defs}'
            f'<rect x="0" y="0" width="{fmt(PAPER_W)}" height="{fmt(PAPER_H)}" '
            f'fill="#ffffff"/>\n'
            f'{body}\n</svg>\n')


def corner_ticks():
    """Small L-marks at the four printable corners, for lining tiles up.

    The marks are drawn `BLEED` mm inside the printable corners (at MARGIN +
    BLEED from the paper edge) and extend inward into the printable area. That
    keeps them off the unprintable border: a printer cannot put ink within
    MARGIN mm of the paper edge, so drawing the marks outward (toward the edge)
    left them unprinted."""
    L = 5.0
    lo_x = MARGIN + BLEED
    hi_x = MARGIN + pw - BLEED
    lo_y = MARGIN + BLEED
    hi_y = MARGIN + ph - BLEED
    segs = []
    for cx in (lo_x, hi_x):
        for cy in (lo_y, hi_y):
            sx = 1.0 if cx == lo_x else -1.0    # inward, toward the sheet centre
            sy = 1.0 if cy == lo_y else -1.0
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx + sx * L)}" y2="{fmt(cy)}"/>')
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx)}" y2="{fmt(cy + sy * L)}"/>')
    return "<g>" + "".join(segs) + "</g>"


def build_sheets(page):
    """One sheet per tile (or a single sheet for a page that fits).

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


def verify_sheets(sheets):
    """Each emitted sheet declares exactly the paper size (one sheet per tile is
    already asserted in verify_tiling)."""
    for i, svg in enumerate(sheets, 1):
        om = _SVG_OPEN.search(svg)
        assert om, f"sheet-{i:03d}: no <svg> root element"
        open_tag = om.group(0)
        wm = re.search(r'\bwidth="([^"]+)"', open_tag)
        hm = re.search(r'\bheight="([^"]+)"', open_tag)
        assert wm and hm, f"sheet-{i:03d}: <svg> is missing width/height"
        w, h = parse_mm(wm.group(1)), parse_mm(hm.group(1))
        assert abs(w - PAPER_W) < 1e-6 and abs(h - PAPER_H) < 1e-6, (
            f"sheet-{i:03d}: {w}x{h} mm != paper {PAPER_W}x{PAPER_H} mm")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def _parse_paper(s):
    """'WxH' (e.g. '279.4x215.9' or '297x210') -> (W, H) floats."""
    m = re.match(r"^\s*([\d.]+)\s*[xX]\s*([\d.]+)\s*$", s)
    assert m, f"--paper must be WxH (e.g. 279.4x215.9), got {s!r}"
    return float(m.group(1)), float(m.group(2))


def _paper_label():
    """The sheet name for the summary line: Letter/A4 for the two sizes the
    pipeline is exercised with, the dimensions otherwise."""
    if (PAPER_W, PAPER_H) == (279.4, 215.9):
        return "Letter"
    if (PAPER_W, PAPER_H) == (297.0, 210.0):
        return "A4"
    return f"{fmt(PAPER_W)}x{fmt(PAPER_H)} mm"


def main():
    ap = argparse.ArgumentParser(
        description="Lay logical pages out onto print sheets (one sheet per tile).")
    ap.add_argument("--paper", default=f"{PAPER_W}x{PAPER_H}",
                    help="sheet size in mm, WxH (default: %(default)s)")
    ap.add_argument("--margin", type=float, default=MARGIN,
                    help="unprintable border, mm (default: %(default)s)")
    ap.add_argument("--overlap", type=float, default=OVERLAP,
                    help="printed twice on adjacent tiles, mm (default: %(default)s)")
    ap.add_argument("--slack", type=float, default=FIT_SLACK,
                    help="overshoot that still gets one sheet, mm (default: %(default)s)")
    ap.add_argument("--bleed", type=float, default=BLEED,
                    help="extra inset, inside the margin, for the cut guides, mm "
                         "(default: %(default)s)")
    ap.add_argument("--pages-dir", default=str(PAGES_DIR),
                    help="logical-pages source directory (default: %(default)s)")
    ap.add_argument("--out-dir", default=str(SHEETS_DIR),
                    help="sheet SVGs + manifest directory (default: %(default)s)")
    args = ap.parse_args()

    paper_w, paper_h = _parse_paper(args.paper)
    _set_geometry(paper_w, paper_h, args.margin, args.overlap, args.slack, args.bleed)

    pages_dir = Path(args.pages_dir)
    out_dir = Path(args.out_dir)

    page_paths = sorted(pages_dir.glob("page-*.svg"))
    assert page_paths, f"no logical pages found in {pages_dir} — run make_logical_pages.py first"
    pages = [read_page(p) for p in page_paths]
    print(f"read {len(pages)} logical pages from {pages_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    # Clear only this script's own output: the sheet SVGs it is about to rewrite,
    # plus its manifest. sheet-*.pdf belongs to sheets_to_pdf.py and is left alone
    # (splitting this cleanup out of the old render_sheets() is the one edit that
    # must not be a copy/paste of the old loop that unlinked both kinds).
    manifest_path = out_dir / MANIFEST.name
    for p in out_dir.glob("sheet-*.svg"):
        p.unlink()
    if manifest_path.exists():
        manifest_path.unlink()

    records = []
    sheets = []
    manifest_sheets = []
    for i, page in enumerate(pages, 1):
        page_sheets, tiles, cols, rows = build_sheets(page)
        records.append((page, page_sheets, tiles, cols, rows))
        for (tr, c, r), svg in zip(tiles, page_sheets):
            sheet_no = len(sheets) + 1
            sheets.append(svg)
            manifest_sheets.append({
                "file": f"sheet-{sheet_no:03d}.svg",
                "page": f"page-{i:03d}.svg",
                "title": page.title,
                "tile": r * cols + c + 1,
                "cols": cols,
                "rows": rows,
                "transform": tr,
            })
        where = "fit" if (cols, rows) == (1, 1) else f"tiled {cols}x{rows}"
        print(f"  page-{i:03d}  {page.W:7.1f} x {page.H:7.1f} mm  {where:10s}  {page.title}")

    verify_tiling(records)
    print("tiling structural check: OK")
    verify_sheets(sheets)
    print("sheet size check: OK")

    for sheet_no, svg in enumerate(sheets, 1):
        sp = out_dir / f"sheet-{sheet_no:03d}.svg"
        sp.write_text(svg, encoding="utf-8")
    print(f"wrote {len(sheets)} sheets -> {out_dir}")

    manifest = {
        "paper": {"w": PAPER_W, "h": PAPER_H},
        "margin": MARGIN,
        "stride": {"x": stride_x, "y": stride_y},
        "sheets": manifest_sheets,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    n_tiled = sum(1 for _, s, t, c, r in records if (c, r) != (1, 1))
    print(f"\n{len(pages)} logical pages -> {len(sheets)} {_paper_label()} sheets "
          f"({n_tiled} tiled, {len(pages) - n_tiled} fit)")
    print("all checks passed")


if __name__ == "__main__":
    main()
