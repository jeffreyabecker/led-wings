#!/usr/bin/env python3
"""
contact_sheet.py -- render a folder of sheet-NNN.svg to one grid PNG.

Dumb, like sheets_to_pdf.py: it knows nothing about the spec or tiling. It
renders every sheet-*.svg in file-name order and tiles the thumbnails into a
grid, for a quick visual of the whole print layout.
"""

import argparse
import io
import os
from pathlib import Path

CAIRO_BIN = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
os.environ["PATH"] = CAIRO_BIN + os.pathsep + os.environ.get("PATH", "")
os.environ["CAIRO_PATH"] = CAIRO_BIN

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parent
PRINT_DIR = ROOT / "templates" / "print"
SHEETS_DIR = PRINT_DIR / "sheets"
OUT_PNG = PRINT_DIR / "contact-sheet.png"


def main():
    ap = argparse.ArgumentParser(description="Tile sheet SVGs into a contact-sheet PNG.")
    ap.add_argument("--in-dir", default=str(SHEETS_DIR), help="folder of sheet-*.svg")
    ap.add_argument("--out", default=str(OUT_PNG), help="output PNG path")
    ap.add_argument("--cols", type=int, default=6, help="thumbnails per row")
    ap.add_argument("--scale", type=float, default=0.25, help="cairosvg scale (96 dpi x this)")
    args = ap.parse_args()

    svgs = sorted(Path(args.in_dir).glob("sheet-*.svg"))
    assert svgs, f"no sheet-*.svg files in {args.in_dir}"

    thumbs = []
    for svg in svgs:
        png_bytes = cairosvg.svg2png(url=str(svg), scale=args.scale)
        thumbs.append(Image.open(io.BytesIO(png_bytes)))

    tw, th = thumbs[0].size
    cols = args.cols
    rows = (len(thumbs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tw, rows * th), "white")
    for i, im in enumerate(thumbs):
        r, c = divmod(i, cols)
        canvas.paste(im, (c * tw, r * th))

    # Atomic replace: a viewer holding the PNG open blocks a truncating save.
    tmp = Path(args.out).with_name(f"{Path(args.out).stem}.tmp.png")
    canvas.save(tmp)
    os.replace(tmp, args.out)
    print(f"wrote {len(thumbs)} thumbnails ({cols}x{rows}) -> {args.out}")


if __name__ == "__main__":
    main()
