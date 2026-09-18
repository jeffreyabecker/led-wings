"""Report how much clear margin a page has at its edges.

Poster tiling depends on this: Acrobat's "Tile only large pages" cuts the sheet
into tiles joined with an overlap, so any ink nearer the trim than that overlap
cannot be registered against its neighbour.
"""
import sys
from pathlib import Path

import pypdfium2 as pdfium

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
import make_feather_template_pdf as gen  # noqa: E402

MM = 25.4 / 72.0


def report(pdf, label, **plan_kwargs):
    gen.ROTATED_FAMILIES = tuple(plan_kwargs.pop("rotate", ()))
    max_h = plan_kwargs.pop("max_page_h", gen.MAX_PAGE_HEIGHT_MM)
    feathers = [load_feather(p) for p in gen.discover(gen.DEFAULT_SRC, None)]
    layouts = [gen.layout_page(g, r, b, 1.0)
               for g, r, b in gen.plan_pages(feathers, 1.0, max_h)]
    doc = pdfium.PdfDocument(str(pdf))
    print(f"=== {label} ===")
    worst = (999.0, None)
    for i, layout in enumerate(layouts, start=1):
        page = doc[i - 1]
        img = page.render(scale=1.0).to_pil().convert("L")
        mask = img.point(lambda v: 255 if v < 128 else 0)
        box = mask.getbbox()
        if box is None:
            # a page with no ink at all would be a bug, not a margin
            print(f"  page {i:2}: BLANK")
            continue
        x0, y0, x1, y1 = (v * MM for v in box)
        w, h = (v * MM for v in page.get_size())
        left, top, right, bottom = x0, y0, w - x1, h - y1
        m = min(left, top, right, bottom)
        if m < worst[0]:
            worst = (m, (i, left, top, right, bottom))
    i, l, t, r, b = worst[1]
    print(f"  {len(layouts)} pages; tightest edge margin {worst[0]:.2f} mm (page {i})")
    print(f"    page {i}: left {l:.1f}  top {t:.1f}  right {r:.1f}  bottom {b:.1f} mm")
    print()


report(Path(r"C:\ode\wings-pcbs\mechanical\templates\as-built\print\feathers-mirrored-pairs.pdf"),
       "feathers-mirrored-pairs.pdf (16 pages)")
report(Path(r"C:\ode\wings-pcbs\mechanical\templates\as-built\print\feathers-200mm-rotated.pdf"),
       "feathers-200mm-rotated.pdf (37 pages)",
       max_page_h=200.0, rotate=("SC", "PC", "A"))
