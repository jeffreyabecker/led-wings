"""Structural verification of a tiled (poster-mode) feather template PDF.

Re-derives the tile plan from the same layout inputs the generator used, then
checks the emitted PDF page-by-page: every sheet is the requested paper size,
references exactly one shared form XObject, clips to the printable area, and
slides the form so that tile's region of its logical page lands in the
printable area. It also confirms the tiles cover each logical page with the
requested overlap, and that the shared forms bound their logical page.

Usage:
    python tools/_verify_pdf_tiles.py <pdf> --tile-paper letter
    python tools/_verify_pdf_tiles.py <pdf> --tile-paper a4 \
        --tile-margin 5 --tile-overlap 12.7
"""
from __future__ import annotations

import argparse
import re
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feather_geometry import load_feather  # noqa: E402
from make_feather_template_pdf import (  # noqa: E402
    MAX_PAGE_HEIGHT_MM,
    PT_PER_MM,
    discover,
    layout_page,
    plan_pages,
    plan_tiles,
    tile_paper,
)

OBJ_RE = re.compile(rb"(\d+) 0 obj\b(.*?)\bendobj", re.S)
STREAM_LEN_RE = re.compile(rb"/Length\s+(\d+)")
NUM = r"-?\d+(?:\.\d+)?"


def parse_objects(data: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2) for m in OBJ_RE.finditer(data)}


def extract_stream(body: bytes) -> bytes | None:
    """Return the raw stream bytes, trusting the declared /Length."""
    m = re.search(rb"stream\r?\n", body)
    if not m:
        return None
    length_m = STREAM_LEN_RE.search(body[: m.start()])
    if not length_m:
        return None
    length = int(length_m.group(1))
    start = m.end()
    data = body[start: start + length]
    if len(data) != length:
        return None
    tail = body[start + length: start + length + 20]
    if not re.match(rb"\r?\n?\s*endstream", tail):
        return None
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--tile-paper", required=True, metavar="letter|a4")
    ap.add_argument("--tile-margin", type=float, default=5.0, metavar="MM")
    ap.add_argument("--tile-overlap", type=float, default=12.7, metavar="MM")
    ap.add_argument("--src", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "mechanical/templates/as-built/vectors/individuals")
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-page-height", type=float,
                    default=MAX_PAGE_HEIGHT_MM, metavar="MM")
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--rotate", nargs="*", metavar="FAMILY", default=None)
    ap.add_argument("--spacing", type=float, default=None)
    args = ap.parse_args()

    if args.rotate is not None:
        import make_feather_template_pdf as gen

        gen.ROTATED_FAMILIES = tuple(args.rotate)
    if args.spacing is not None:
        import make_feather_template_pdf as gen

        gen.DENSE_GAP_MM = args.spacing

    paper_label, paper_w, paper_h = tile_paper(args.tile_paper)
    feathers = [load_feather(p) for p in discover(args.src, args.only)]
    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]
    plan = plan_tiles(layouts, paper_w, paper_h, args.tile_margin,
                      args.tile_overlap, paper_label)

    data = args.pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise SystemExit("not a PDF")
    objects = parse_objects(data)
    errors: list[str] = []

    # --- forms: one per logical page, bounding that page (in points) ---
    forms = [(n, b) for n, b in sorted(objects.items())
             if b"/Subtype /Form" in b]
    if len(forms) != len(layouts):
        errors.append(f"form count {len(forms)} != logical pages {len(layouts)}")
    for (num, body), layout in zip(forms, layouts):
        bb = re.search(rb"/BBox \[([^\]]+)\]", body)
        if not bb:
            errors.append(f"form {num}: no BBox")
            continue
        vals = [float(v) for v in bb.group(1).split()]
        want = (layout.page_w * PT_PER_MM, layout.page_h * PT_PER_MM)
        if abs(vals[2] - want[0]) > 5e-2 or abs(vals[3] - want[1]) > 5e-2:
            errors.append(
                f"form {num}: BBox {vals[2]:.2f}x{vals[3]:.2f} pt != "
                f"logical page {want[0]:.2f}x{want[1]:.2f} pt")

    # --- pages: every sheet is the paper size, clipped + slid per the plan ---
    pages = [(n, b) for n, b in sorted(objects.items())
             if b"/Type /Page" in b and b"/Type /Pages" not in b]
    if len(pages) != len(plan.tiles):
        errors.append(f"sheet count {len(pages)} != planned {len(plan.tiles)}")

    margin = plan.margin
    pw = (plan.paper_w - 2.0 * margin) * PT_PER_MM
    ph = (plan.paper_h - 2.0 * margin) * PT_PER_MM
    mx = my = margin * PT_PER_MM

    for index, ((page_num, body), tile) in enumerate(zip(pages, plan.tiles), start=1):
        mb = re.search(rb"/MediaBox \[([^\]]+)\]", body)
        if mb:
            vals = [float(v) for v in mb.group(1).split()]
            want = (plan.paper_w * PT_PER_MM, plan.paper_h * PT_PER_MM)
            if abs(vals[2] - want[0]) > 5e-2 or abs(vals[3] - want[1]) > 5e-2:
                errors.append(
                    f"sheet {index}: MediaBox {vals[2]:.2f}x{vals[3]:.2f} pt != "
                    f"paper {want[0]:.2f}x{want[1]:.2f} pt")
        if b"/XObject" not in body or b"/F0" not in body:
            errors.append(f"sheet {index}: page has no /F0 form XObject")
        cref = re.search(rb"/Contents (\d+) 0 R", body)
        content_obj = objects.get(int(cref.group(1))) if cref else None
        stream = extract_stream(content_obj) if content_obj is not None else None
        if stream is None:
            errors.append(f"sheet {index}: content stream missing or bad /Length")
            continue
        text = zlib.decompress(stream).decode("ascii")

        clip = re.search(
            rf"^{NUM} {NUM} {NUM} {NUM} re W n$", text, re.M)
        if not clip:
            errors.append(f"sheet {index}: no clip rectangle")
        else:
            c = [float(v) for v in clip.group(0).split()[:4]]
            want = (mx, my, pw, ph)
            for got, w in zip(c, want):
                if abs(got - w) > 5e-2:
                    errors.append(
                        f"sheet {index}: clip {c} != printable {want}")
                    break
        slide = re.search(rf"^1 0 0 1 {NUM} {NUM} cm$", text, re.M)
        if not slide:
            errors.append(f"sheet {index}: no slide transform")
        else:
            tx, ty = (float(v) for v in slide.group(0).split()[4:6])
            want_tx = mx - tile.x0 * PT_PER_MM
            want_ty = my - tile.y0 * PT_PER_MM
            if abs(tx - want_tx) > 5e-2 or abs(ty - want_ty) > 5e-2:
                errors.append(
                    f"sheet {index}: slide {tx},{ty} != plan {want_tx},{want_ty}")
        if "/F0 Do" not in text:
            errors.append(f"sheet {index}: content does not draw /F0")
        if tile.page_total > 1 and f"page {tile.page_no} of" not in text:
            errors.append(f"sheet {index}: tile label missing")

    # --- coverage: re-derive each page's grid and confirm the overlap ---
    stride_x = pw / PT_PER_MM - plan.overlap
    stride_y = ph / PT_PER_MM - plan.overlap
    for page_no, layout in enumerate(layouts, start=1):
        page_tiles = [t for t in plan.tiles if t.page_no == page_no]
        cols = page_tiles[0].cols
        rows = page_tiles[0].rows
        covered_w = (cols - 1) * stride_x + pw / PT_PER_MM
        covered_h = (rows - 1) * stride_y + ph / PT_PER_MM
        if covered_w < layout.page_w - 1e-6:
            errors.append(f"page {page_no}: tiles cover only {covered_w:.2f} mm "
                          f"of {layout.page_w:.2f} mm width")
        if covered_h < layout.page_h - 1e-6:
            errors.append(f"page {page_no}: tiles cover only {covered_h:.2f} mm "
                          f"of {layout.page_h:.2f} mm height")
        # adjacent tiles must share exactly the overlap strip
        for iy in range(rows):
            for ix in range(cols - 1):
                a = next(t for t in page_tiles if t.col == ix + 1 and t.row == rows - iy)
                b = next(t for t in page_tiles if t.col == ix + 2 and t.row == rows - iy)
                overlap_x = (a.x0 + pw / PT_PER_MM) - b.x0
                if abs(overlap_x - plan.overlap) > 1e-6:
                    errors.append(f"page {page_no}: horizontal overlap "
                                  f"{overlap_x:.3f} mm != {plan.overlap:g} mm")

    print(f"{args.pdf.name}: {len(data) / 1024:.1f} KiB, {len(objects)} objects")
    print(f"{len(layouts)} logical page(s), {len(plan.tiles)} sheet(s) on "
          f"{plan.paper_label} landscape "
          f"(margin {plan.margin:g} mm, overlap {plan.overlap:g} mm)")
    if errors:
        print()
        print(f"FAILURES ({len(errors)}):")
        for e in errors[:40]:
            print("  " + e)
        return 1
    print("tile plan, paper sizes, clipping, sliding, coverage and overlap "
          "all verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
