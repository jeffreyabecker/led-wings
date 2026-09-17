"""Validate the generated template PDF with pypdf (an independent parser).

Checks page count, per-page media boxes and that every page's text layer carries
the identification for each pair it holds.

Usage: python tools/_verify_pdf_pypdf.py <pdf> [--max-rows N] [--scale S]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
from make_feather_template_pdf import (  # noqa: E402
    MAX_PAGE_HEIGHT_MM,
    PT_PER_MM,
    layout_page,
    plan_pages,
)

PAGE_WIDTH_LIMIT_MM = 273.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--src", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "mechanical/templates/as-built/vectors/individuals")
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-page-height", type=float,
                    default=MAX_PAGE_HEIGHT_MM, metavar="MM")
    ap.add_argument("--spacing", type=float, default=None)
    args = ap.parse_args()

    if args.spacing is not None:
        import make_feather_template_pdf as gen

        gen.DENSE_GAP_MM = args.spacing

    from make_feather_template_pdf import discover

    reader = PdfReader(str(args.pdf))
    feathers = [load_feather(p) for p in discover(args.src, args.only)]
    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]
    failures: list[str] = []

    print(f"{args.pdf.name}: pypdf read {len(reader.pages)} pages "
          f"(expected {len(layouts)})")
    print(f"  metadata: {dict(reader.metadata or {})}")
    if len(reader.pages) != len(layouts):
        failures.append(f"page count {len(reader.pages)} != {len(layouts)}")

    total_text = 0
    for i, (page, layout) in enumerate(zip(reader.pages, layouts), start=1):
        box = page.mediabox
        w_mm = float(box.width) / PT_PER_MM
        h_mm = float(box.height) / PT_PER_MM
        if abs(w_mm - layout.page_w) > 0.01 or abs(h_mm - layout.page_h) > 0.01:
            failures.append(
                f"page {i}: mediabox {w_mm:.3f}x{h_mm:.3f} mm "
                f"!= {layout.page_w:.3f}x{layout.page_h:.3f} mm")
        if w_mm > PAGE_WIDTH_LIMIT_MM + 0.01:
            failures.append(f"page {i}: {w_mm:.2f} mm is over the width limit")

        text = page.extract_text() or ""
        total_text += len(text)
        if args.scale == 1.0:
            expected = [layout.title, "1:1", "verify before cutting"]
        else:
            # a reduced print states the scale instead of drawing a 50 mm bar
            expected = [layout.title, "reduced", "not full size"]
        expected.append(f"page {i} of {len(layouts)}")
        expected.extend(slot.name for slot in layout.slots)
        # one ID per half, with the side suffix
        expected.extend(f"{slot.name} L" for slot in layout.slots)
        expected.extend(f"{slot.name} R" for slot in layout.slots)
        for needle in expected:
            if needle not in text:
                failures.append(f"page {i}: missing text {needle!r}")
        if "LEFT - mirror" in text or "RIGHT - as built" in text:
            failures.append(f"page {i}: obsolete side caption still present")
        if "\uFFFD" in text:
            failures.append(f"page {i}: replacement characters in extracted text")

        content = page.get_contents()
        raw = content.get_data() if content is not None else b""
        if b" m " not in raw or b" l " not in raw:
            failures.append(f"page {i}: content stream has no path operators")
        # each half is drawn three times (halo stroke, fill, cut stroke)
        closes = raw.count(b"h\n")
        want_closes = 6 * len(layout.slots)
        if closes != want_closes:
            failures.append(
                f"page {i}: {closes} close operators, expected {want_closes} "
                f"(3 passes x 2 halves x {len(layout.slots)} pairs)")

        print(f"  page {i:2} {len(layout.slots)} pair(s) {w_mm:7.2f} x {h_mm:7.2f} mm "
              f"  {len(text):4d} chars  {len(raw) / 1024:7.1f} KiB  "
              f"[{', '.join(layout.names)}]")

    print(f"  extracted {total_text} text characters in total")
    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:40]:
            print("  " + f)
        return 1
    print("pypdf validation passed: pages, media boxes, labels and geometry present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
