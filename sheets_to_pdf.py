#!/usr/bin/env python3
"""
sheets_to_pdf.py
================

Script 3 of the print pipeline: render the print sheets to PDF and merge them
into one document.

Reads templates/print/sheets/sheet-NNN.svg in manifest order (the manifest is
written by assemble_sheets.py and records, for each sheet, its source sheet,
title, tile grid, and content transform) and emits:

  templates/print/sheets/sheet-NNN.pdf        # per-sheet raster intermediates
  templates/print/feathers-letter-landscape.pdf
  templates/print/contact-sheet.png

This script knows nothing about tiling or paper geometry: it takes the paper
size from the manifest, renders whatever same-size SVGs it is handed, and merges
them in the order they are listed. Its own checks are the input contract (every
manifest sheet exists and is paper-sized), the output contract (the merged PDF
has one page per sheet), and the calibration bars on the cover, whose sheet and
offset it reads from the manifest rather than assuming page 1 at a hardcoded
margin.
"""

import json
import math
import os
import re
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
PRINT_DIR = ROOT / "templates" / "print"
SHEETS_DIR = PRINT_DIR / "sheets"          # intermediates (gitignored)
MANIFEST = SHEETS_DIR / "manifest.json"
OUT_PDF = PRINT_DIR / "feathers-letter-landscape.pdf"
CONTACT_PNG = PRINT_DIR / "contact-sheet.png"

_SVG_OPEN = re.compile(r"<svg\b[^>]*>")


def parse_mm(s):
    return float(str(s).replace("mm", "").strip())


def _svg_size(path):
    """(width_mm, height_mm) of a sheet SVG's root element."""
    text = path.read_text(encoding="utf-8")
    om = _SVG_OPEN.search(text)
    assert om, f"{path}: no <svg> root element"
    open_tag = om.group(0)
    wm = re.search(r'\bwidth="([^"]+)"', open_tag)
    hm = re.search(r'\bheight="([^"]+)"', open_tag)
    assert wm and hm, f"{path}: <svg> is missing width/height"
    return parse_mm(wm.group(1)), parse_mm(hm.group(1))


# --------------------------------------------------------------------------
# Rendering (SVG -> PDF via cairosvg, merged with pypdf)
# --------------------------------------------------------------------------

def render_sheets(sheets_dir, files):
    """Render each named sheet SVG to PDF and merge them, in `files` order.

    Only sheet-*.pdf is cleared here: the SVGs belong to assemble_sheets.py
    and are left untouched."""
    sheets_dir.mkdir(parents=True, exist_ok=True)
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    for p in sheets_dir.glob("sheet-*.pdf"):
        p.unlink()

    pdfs = []
    for f in files:
        sp = sheets_dir / f
        pp = sheets_dir / (Path(f).stem + ".pdf")
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

def _translate_offset(transform):
    """The (dx, dy) of a 'translate(X Y)' string."""
    m = re.match(r"^\s*translate\(\s*([-\d.]+)\s+([-\d.]+)\s*\)\s*$", transform)
    assert m, f"cover transform is not a translate: {transform!r}"
    return float(m.group(1)), float(m.group(2))


def verify_scale(manifest, sheets_dir):
    """Rasterise the cover sheet at 300 dpi and measure each calibration bar back.

    Bar positions and lengths come from the manifest (`scale-bars`), written by
    assemble_sheets.py from the cover sheet's spec positions + centering offset."""
    cover = next((s for s in manifest["sheets"] if s.get("title") == "cover"), None)
    assert cover is not None, "manifest has no cover sheet"
    cover_pdf = sheets_dir / (Path(cover["file"]).stem + ".pdf")

    doc = pdfium.PdfDocument(str(cover_pdf))
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

    results = []
    for bar in manifest.get("scale-bars", []):
        results.append((bar["label"], bar["length"],
                        measure(bar["y"], bar["x"], bar["length"])))
    return results


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sheets = manifest["sheets"]
    assert sheets, "manifest lists no sheets"
    paper = manifest["paper"]
    trim = paper["trim"]
    print(f"read manifest: {len(sheets)} sheets (paper {trim['width']} x {trim['height']} mm)")

    # Input contract: the sheet SVGs on disk match the manifest exactly, in
    # order, and each declares the manifest's paper size.
    on_disk = sorted(p.name for p in SHEETS_DIR.glob("sheet-*.svg"))
    in_manifest = [s["file"] for s in sheets]
    assert on_disk == in_manifest, (
        f"sheet SVGs on disk ({len(on_disk)}) != manifest sheet list ({len(in_manifest)})")
    for s in sheets:
        w, h = _svg_size(SHEETS_DIR / s["file"])
        assert abs(w - trim["width"]) < 1e-6 and abs(h - trim["height"]) < 1e-6, (
            f"{s['file']}: {w}x{h} mm != manifest paper {trim['width']}x{trim['height']} mm")

    n = render_sheets(SHEETS_DIR, in_manifest)
    print(f"wrote {n} sheets -> {OUT_PDF}")

    # Output contract: the merged PDF has one page per sheet, in manifest order
    # (the merge loop appends in that order, so a page-count mismatch is how a
    # stale sheet set shows up).
    reader = pypdf.PdfReader(str(OUT_PDF))
    n_merged = len(reader.pages)
    assert n_merged == len(sheets), (
        f"merged PDF has {n_merged} pages, expected {len(sheets)}")

    contact_sheet(n)
    print(f"contact sheet -> {CONTACT_PNG}")

    bars = verify_scale(manifest, SHEETS_DIR)
    print("\nverification:")
    print(f"  merged {n_merged} pages == {len(sheets)} sheets -> OK")
    all_ok = True
    for label, length, measured in bars:
        ok = measured is not None and abs(measured - length) < 1.0
        all_ok = all_ok and ok
        print(f"  cover {label} bar measured {measured} mm   -> {'OK' if ok else 'FAIL'}")
    assert all_ok, "scale verification FAILED"
    print("all checks passed")


if __name__ == "__main__":
    main()
