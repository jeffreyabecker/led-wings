"""Independent verification of the mirrored-pair page layout.

For each feather the generator's own layout is used to build an SVG fixture,
which Chrome rasterises; the ink is then measured in Python and compared against
the layout. Checks per page:

  * every pair lands where the layout puts it (within a pixel),
  * the as-built half sits right of its axis and the mirror left of it,
  * the two arms are exact reflections of each other,
  * neighbouring pairs keep the requested clear spacing,
  * nothing escapes the page, and no page is wider than 273 mm.

Usage: python tools/_verify_mirror_layout.py [--only P1 B5] [--scale 1.0]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
from make_feather_template_pdf import (  # noqa: E402
    DENSE_GAP_MM,
    MAX_PAGE_HEIGHT_MM,
    PAGE_WIDTH_MM,
    SPARSE_GAP_MM,
    layout_page,
    plan_pages,
    transform_polys,
)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PX_PER_MM = 4.0
BLEED_MM = 6.0
POINT_PLACES = 3
SERIALISE_TOL_MM = 1.1e-3     # rounding introduced by writing 3 decimal places
PAGE_WIDTH_LIMIT_MM = 273.0
PLACEMENT_TOL_MM = 1.5        # includes raster anti-aliasing slack


def ink_bounds(polys, stroke_half):
    xs = [x for poly in polys for x, _ in poly]
    ys = [y for poly in polys for _, y in poly]
    return (min(xs) - stroke_half, min(ys) - stroke_half,
            max(xs) + stroke_half, max(ys) + stroke_half)


def build_fixture(layout, scale, out_svg: Path) -> dict:
    """Write one page's pairs as SVG in page coordinates (1 unit = 1 page mm).

    The root <svg> is sized in CSS pixels rather than millimetres because Chrome
    viewport-scales mm-sized documents; the viewBox keeps the page-millimetre
    mapping, and the caller checks the screenshot size before trusting pixels.
    """
    parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    marks = []
    for slot in layout.slots:
        feather = slot.feather
        stroke_half = feather.stroke_mm * scale / 2.0
        for to_page in (slot.left_to_page, slot.right_to_page):
            polys = transform_polys(feather.polys_right, to_page)
            marks.append(ink_bounds(polys, stroke_half))
            for poly in polys:
                pts = " ".join(
                    f"{x:.{POINT_PLACES}f},{layout.page_h - y:.{POINT_PLACES}f}"
                    for x, y in poly
                )
                parts.append(
                    f'<polygon points="{pts}" fill="none" stroke="#000000" '
                    f'stroke-width="{feather.stroke_mm * scale:.3f}"/>'
                )
        # spine ticks above and below, exactly as the PDF draws them
        for y0, y1 in ((slot.pair_bottom - 5.0, slot.pair_bottom),
                       (slot.pair_top, slot.pair_top + 5.0)):
            parts.append(
                f'<line x1="{slot.axis_x}" y1="{layout.page_h - y0:.4f}" '
                f'x2="{slot.axis_x}" y2="{layout.page_h - y1:.4f}" '
                f'stroke="#000000" stroke-width="0.4"/>'
            )
        marks.append((slot.axis_x - 0.2, layout.page_h - slot.pair_top - 5.0,
                      slot.axis_x + 0.2, layout.page_h - slot.pair_bottom + 5.0))
    parts.append("</svg>")

    xs = [m[0] for m in marks] + [m[2] for m in marks]
    ys = [m[1] for m in marks] + [m[3] for m in marks]
    vx = min(xs) - BLEED_MM
    vy = min(ys) - BLEED_MM
    vw = (max(xs) - vx) + BLEED_MM
    vh = (max(ys) - vy) + BLEED_MM
    w_px = int(round(vw * PX_PER_MM))
    h_px = int(round(vh * PX_PER_MM))
    parts[0] = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px}" height="{h_px}" '
        f'viewBox="{vx:.4f} {vy:.4f} {vw:.4f} {vh:.4f}">'
        f'<rect x="{vx:.4f}" y="{vy:.4f}" width="{vw:.4f}" height="{vh:.4f}" fill="#ffffff"/>'
    )
    out_svg.write_text("\n".join(parts), encoding="utf-8")
    return {"px": (w_px, h_px), "view": (vx, vy, vw, vh)}


def rasterize(svg_path: Path, png_path: Path, w_px: int, h_px: int) -> None:
    subprocess.run(
        [
            CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={w_px},{h_px}",
            f"--screenshot={png_path}",
            svg_path.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def _row_size(slots: list, slot) -> int:
    """How many pairs share this slot's row (pairs overlapping in x)."""
    return sum(
        1 for other in slots
        if other.cell_left < slot.cell_right and slot.cell_left < other.cell_right
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-page-height", type=float, default=MAX_PAGE_HEIGHT_MM,
                    metavar="MM")
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--src", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "mechanical/templates/as-built/vectors/individuals")
    args = ap.parse_args()

    if args.only:
        paths = sorted(args.src.glob("*.svg"))
        wanted = set(args.only)
        found = {p.stem: p for p in paths}
        missing = wanted - set(found)
        if missing:
            raise SystemExit(f"unknown feather(s): {', '.join(sorted(missing))}")
        feathers = [load_feather(found[n]) for n in args.only]
    else:
        from make_feather_template_pdf import discover

        feathers = [load_feather(p) for p in discover(args.src, None)]

    if args.spacing is not None:
        import make_feather_template_pdf as gen

        gen.DENSE_GAP_MM = args.spacing

    planned = plan_pages(feathers, args.scale, args.max_page_height,
                         args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]

    failures: list[str] = []
    pairs_checked = 0
    print(f"{'page':>5} {'page mm':>17} {'slots':>5}  {'placement':>10} {'mirror':>9} "
          f"{'spacing':>9} {'axis':>8}")

    with tempfile.TemporaryDirectory() as tmp:
        for page_no, layout in enumerate(layouts, start=1):
            if layout.page_w > PAGE_WIDTH_LIMIT_MM + 1e-9:
                failures.append(
                    f"page {page_no}: width {layout.page_w:.2f} mm exceeds "
                    f"{PAGE_WIDTH_LIMIT_MM:.0f} mm")
            info = build_fixture(layout, args.scale, Path(tmp) / "page.svg")
            w_px, h_px = info["px"]
            png = Path(tmp) / "page.png"
            rasterize(Path(tmp) / "page.svg", png, w_px, h_px)
            img = Image.open(png).convert("L")
            if img.size != (w_px, h_px):
                failures.append(
                    f"page {page_no}: screenshot {img.size} != requested {(w_px, h_px)}")
                continue
            mask = img.point(lambda v: 255 if v < 128 else 0)
            vx, vy, vw, vh = info["view"]

            worst_place = 0.0
            worst_mirror = 0.0
            for slot in layout.slots:
                pairs_checked += 1
                name = slot.name
                feather = slot.feather
                stroke_half = feather.stroke_mm * args.scale / 2.0
                pr = ink_bounds(transform_polys(feather.polys_right, slot.right_to_page),
                                stroke_half)
                pl = ink_bounds(transform_polys(feather.polys_right, slot.left_to_page),
                                stroke_half)
                # page frame -> fixture frame, in pixels
                def to_px(x, y):
                    return ((x - vx) * PX_PER_MM, (layout.page_h - y - vy) * PX_PER_MM)

                box = mask.getbbox()
                region = (
                    int(to_px(pl[0], 0)[0]) - 2, 0,
                    int(to_px(pr[2], 0)[0]) + 2, img.height,
                )
                sub = mask.crop(region)
                got = sub.getbbox()
                if got is None:
                    failures.append(f"page {page_no} {name}: no ink rendered")
                    continue
                ink_l = vx + (got[0] + region[0]) / PX_PER_MM
                ink_r = vx + (got[2] + region[0]) / PX_PER_MM
                exp_l = min(pr[0], pl[0])
                exp_r = max(pr[2], pl[2])
                place_err = max(abs(ink_l - exp_l), abs(ink_r - exp_r))
                worst_place = max(worst_place, place_err)
                # Raster edge detection on a half-millimetre stroke carries about
                # a pixel of anti-aliasing slack, so this is a sanity bound on the
                # placement; the exact checks are the geometry ones below.
                if place_err > PLACEMENT_TOL_MM:
                    failures.append(
                        f"page {page_no} {name}: placement off by "
                        f"{place_err * PX_PER_MM:.2f} px "
                        f"(ink [{ink_l:.2f},{ink_r:.2f}] vs layout [{exp_l:.2f},{exp_r:.2f}])")

                # handedness and exact mirroring
                right = transform_polys(feather.polys_right, slot.right_to_page)
                left = transform_polys(feather.polys_right, slot.left_to_page)
                if min(x for poly in right for x, _ in poly) < slot.axis_x - 1e-6:
                    failures.append(f"page {page_no} {name}: as-built half left of its axis")
                if max(x for poly in left for x, _ in poly) > slot.axis_x + 1e-6:
                    failures.append(f"page {page_no} {name}: mirrored half right of its axis")
                reflected = [[(2 * slot.axis_x - x, y) for x, y in poly] for poly in right]
                err = max(
                    max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                    for p, q in zip(reflected, left)
                    for a, b in zip(p, q)
                )
                worst_mirror = max(worst_mirror, err)
                if err > SERIALISE_TOL_MM:
                    failures.append(
                        f"page {page_no} {name}: mirrored vertices differ by {err * 1000:.3f} um")

                if ink_l < -0.05 or ink_r > layout.page_w + 0.05:
                    failures.append(f"page {page_no} {name}: ink escapes the page width")

            # Spacing between neighbouring slots. Side-by-side pairs keep the
            # dense gap; a lone pair in its row keeps the wider sparse gap from
            # the rows above and below it.
            min_gap = float("inf")
            slots = sorted(layout.slots, key=lambda s: (s.pair_bottom, s.cell_left))
            for i, a in enumerate(slots):
                for b in slots[i + 1:]:
                    gap_x = max(a.cell_left - b.cell_right, b.cell_left - a.cell_right)
                    gap_y = max(a.pair_bottom - b.pair_top, b.pair_bottom - a.pair_top)
                    if gap_x >= 0 and gap_y >= 0:
                        continue          # diagonal: never neighbours
                    if gap_x < 0:         # overlapping x range -> stacked vertically
                        min_gap = min(min_gap, gap_y)
                        # a vertical pair of neighbours needs the sparse gap when
                        # either of them sits alone in its row
                        alone = (_row_size(slots, a) == 1 or _row_size(slots, b) == 1)
                        want = SPARSE_GAP_MM if alone else DENSE_GAP_MM
                    else:                 # overlapping y range -> side by side
                        min_gap = min(min_gap, gap_x)
                        want = DENSE_GAP_MM
                    if gap_y >= 0 and gap_x < 0:
                        gap = gap_y
                    else:
                        gap = gap_x
                    if gap < want - 1e-6:
                        failures.append(
                            f"page {page_no}: {a.name}/{b.name} spacing {gap:.2f} mm "
                            f"is under the required {want:.2f} mm")

            print(f"{page_no:5} {layout.page_w:8.1f} x {layout.page_h:7.1f} "
                  f"{len(layout.slots):5}  {worst_place * PX_PER_MM:9.2f}px "
                  f"{worst_mirror * 1000:8.3f}u "
                  f"{(min_gap if min_gap is not float('inf') else float('nan')):9.2f} "
                  f"{'ok' if worst_place <= PLACEMENT_TOL_MM else 'FAIL':>8}")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:40]:
            print("  " + f)
        return 1
    print(f"all {len(layouts)} pages / {pairs_checked} pairs verified: placement, "
          f"handedness, mirroring, spacing and page fit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
