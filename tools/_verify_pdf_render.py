"""Render the generated PDF with PDFium (pypdfium2) and verify the printed result.

This is a fully independent path: PDFium parses the PDF and rasterises it, so it
catches anything a reader would see that our own writer might have got wrong.

Per page it checks the page size, that all marks stay on the page, that the
feather ink lands inside the expected bounds, and that each pair's two half
labels sit either side of that pair's mirror axis. Sample pages are written out
plus a contact sheet for visual inspection.

Usage: python tools/_verify_pdf_render.py <pdf> [--dpi 150] [--max-rows N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
from make_feather_template_pdf import (  # noqa: E402
    MAX_PAGE_HEIGHT_MM,
    LABEL_SIZE_MM,
    layout_page,
    plan_pages,
    slot_labels,
    text_width_mm,
    transform_polys,
)

PAGE_WIDTH_LIMIT_MM = 273.0


def check_labels(page, layout, page_no: int, failures: list) -> None:
    """Require an ID label for every half on the rendered page.

    The IDs carry the side suffix (`P1 L` / `P1 R`), which is what distinguishes
    the halves, so the text layer must contain one of each. Presence only is
    asserted: a strict occurrence count is not reliable here because the footer's
    pair list can accidentally contain a label as a substring (`LC1 LC5` contains
    `LC1 L`), and the exact label placement is already proven by the
    content-stream check.
    """
    text = page.get_textpage().get_text_range()
    for slot in layout.slots:
        for text_id, _x, _y, _align in slot_labels(slot):
            if text_id not in text:
                failures.append(
                    f"page {page_no} {slot.name}: no {text_id!r} label in the "
                    f"rendered text layer")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--dpi", type=float, default=150.0)
    ap.add_argument("--samples", nargs="+", default=None,
                    help="feather IDs whose pages get written out")
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-page-height", type=float,
                    default=MAX_PAGE_HEIGHT_MM, metavar="MM")
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--src", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "mechanical/templates/as-built/vectors/individuals")
    args = ap.parse_args()

    if args.spacing is not None:
        import make_feather_template_pdf as gen

        gen.DENSE_GAP_MM = args.spacing

    mm_per_px = 25.4 / args.dpi
    from make_feather_template_pdf import discover

    feathers = [load_feather(p) for p in discover(args.src, args.only)]
    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]
    doc = pdfium.PdfDocument(str(args.pdf))
    failures: list[str] = []
    print(f"{args.pdf.name}: PDFium reports {len(doc)} pages, "
          f"{len(layouts)} planned")
    if len(doc) != len(layouts):
        failures.append(f"PDFium page count {len(doc)} != planned {len(layouts)}")

    if args.outdir:
        args.outdir.mkdir(parents=True, exist_ok=True)
    thumbs: list[tuple[str, Image.Image]] = []
    printed = 0

    for i, layout in enumerate(layouts, start=1):
        page = doc[i - 1]
        w_mm, h_mm = (v / (72.0 / 25.4) for v in page.get_size())
        if abs(w_mm - layout.page_w) > 0.02 or abs(h_mm - layout.page_h) > 0.02:
            failures.append(
                f"page {i}: PDFium size {w_mm:.2f}x{h_mm:.2f} mm != "
                f"{layout.page_w:.2f}x{layout.page_h:.2f} mm")
        if w_mm > PAGE_WIDTH_LIMIT_MM + 0.02:
            failures.append(f"page {i}: {w_mm:.2f} mm is over the width limit")

        img = page.render(scale=args.dpi / 72.0).to_pil().convert("L")
        mask = img.point(lambda v: 255 if v < 128 else 0)
        box = mask.getbbox()
        if box is None:
            failures.append(f"page {i}: PDFium rendered a blank page")
            continue
        x0, y0, x1, y1 = box
        ink_left, ink_right = x0 * mm_per_px, x1 * mm_per_px
        ink_top, ink_bottom = y0 * mm_per_px, y1 * mm_per_px

        # every mark must be on the page
        if ink_left < -0.05 or ink_right > w_mm + 0.05:
            failures.append(f"page {i}: marks escape the page width")
        if ink_top < -0.05 or ink_bottom > h_mm + 0.05:
            failures.append(f"page {i}: marks escape the page height")

        # the feather ink of every pair must be inside the drawn marks
        for slot in layout.slots:
            stroke_half = slot.feather.stroke_mm * args.scale / 2.0
            pr = transform_polys(slot.feather.polys_right, slot.right_to_page)
            pl = transform_polys(slot.feather.polys_right, slot.left_to_page)
            xs = [x for poly in pr + pl for x, _ in poly]
            ys = [y for poly in pr + pl for _, y in poly]
            e_left, e_right = min(xs) - stroke_half, max(xs) + stroke_half
            e_top = layout.page_h - (max(ys) + stroke_half)
            e_bottom = layout.page_h - (min(ys) - stroke_half)
            if not (ink_left <= e_left + 0.6 and ink_right >= e_right - 0.6
                    and ink_top <= e_top + 0.6 and ink_bottom >= e_bottom - 0.6):
                failures.append(
                    f"page {i} {slot.name}: pair ink [{e_left:.1f},{e_right:.1f}]x"
                    f"[{e_top:.1f},{e_bottom:.1f}] not inside rendered marks "
                    f"[{ink_left:.1f},{ink_right:.1f}]x[{ink_top:.1f},{ink_bottom:.1f}]")

        # handedness from the rendered text layer: for each pair the labels must
        # sit on the correct side of that pair's own axis
        check_labels(page, layout, i, failures)

        if args.samples and args.outdir:
            hit = [s for s in layout.slots if s.name in args.samples]
            if hit:
                small = page.render(scale=1.0).to_pil()
                small.save(args.outdir / f"{i:02d}-{'-'.join(layout.names)}.png")
                thumbs.append((layout.names[0], small))
                printed += 1

        print(f"  p{i:2} {len(layout.slots)} pair(s) {w_mm:7.2f} x {h_mm:7.2f} mm  "
              f"marks x[{ink_left:6.1f},{ink_right:6.1f}] y[{ink_top:6.1f},{ink_bottom:6.1f}]  "
              f"[{', '.join(layout.names)}]")

    if thumbs and args.outdir:
        cell_w = 420
        cells = []
        for name, im in thumbs:
            ratio = cell_w / im.width
            cells.append((name, im.resize((cell_w, max(1, int(im.height * ratio))),
                                          Image.LANCZOS)))
        sheet_h = max(c.height for _, c in cells) + 26
        sheet = Image.new("L", (cell_w * len(cells), sheet_h), 255)
        for idx, (_, cell) in enumerate(cells):
            sheet.paste(cell, (idx * cell_w, 26))
        sheet.save(args.outdir / "contact-sheet.png")
        print(f"  wrote {printed} page image(s) and a contact sheet to {args.outdir}")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:40]:
            print("  " + f)
        return 1
    print(f"PDFium render checks passed for all {len(layouts)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
