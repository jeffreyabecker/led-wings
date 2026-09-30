#!/usr/bin/env python3
"""
sheets_to_pdf.py -- render a folder of sheet-NNN.svg to PDF and merge them in
file-name order.

Very dumb: it knows nothing about the spec, tiling, paper geometry, or scale.
assemble_sheets.py does the heavy lifting and names the sheets so that filename
order is print order.
"""

import argparse
import os
from pathlib import Path

# cairosvg needs the cairo DLL that ships inside GStreamer. Point at it
# explicitly so the build does not depend on GStreamer staying on PATH.
CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
os.environ["CAIRO_PATH"] = CAIRO_BIN

import cairosvg
import pypdf

ROOT = Path(__file__).resolve().parent
PRINT_DIR = ROOT / "templates" / "print"
SHEETS_DIR = PRINT_DIR / "sheets"
OUT_PDF = PRINT_DIR / "feathers-letter-landscape.pdf"


def main():
    ap = argparse.ArgumentParser(description="Merge a folder of sheet SVGs into one PDF.")
    ap.add_argument("--in-dir", default=str(SHEETS_DIR), help="folder of sheet-*.svg")
    ap.add_argument("--out", default=str(OUT_PDF), help="merged PDF path")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    svgs = sorted(in_dir.glob("sheet-*.svg"))
    assert svgs, f"no sheet-*.svg files in {in_dir}"

    for svg in svgs:
        cairosvg.svg2pdf(url=str(svg), write_to=str(svg.with_suffix(".pdf")))

    writer = pypdf.PdfWriter()
    for svg in svgs:
        writer.append(str(svg.with_suffix(".pdf")))

    writer.write(str(args.out))
    print(f"merged {len(svgs)} sheets -> {args.out}")


if __name__ == "__main__":
    main()
