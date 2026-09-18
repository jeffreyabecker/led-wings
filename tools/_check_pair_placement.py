"""Verify a pair's placement directly, for both orientations.

Run standalone to sanity-check make_slot without going through the PDF.

Upright: the halves are side by side across a vertical mirror axis, separated by
the partner gap horizontally.
Rotated: the halves are stacked across a horizontal mirror axis, separated by the
partner gap vertically.
Either way each half keeps its own feather's dimensions (rotated: swapped), the
pair fills its cell, and the two halves are exact reflections of one another.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
import make_feather_template_pdf as gen  # noqa: E402

gen.ROTATED_FAMILIES = ("SC", "PC", "A")

names = ["SC1", "SC3", "SC6", "PC1", "PC3", "A1", "A4", "LC1", "MC1"]
failures = []
for name in names:
    f = load_feather(Path(gen.DEFAULT_SRC) / f"{name}.svg")
    cell_left, cell_bottom = 51.63, 24.60
    slot = gen.make_slot(f, cell_left, cell_bottom, 1.0)
    cut = f.cut_box
    fw = cut[2] - cut[0]          # across the feather
    fh = cut[3] - cut[1]          # along the feather
    gap = gen.partner_gap(f)
    rb, lb = slot.right_box, slot.left_box
    rw, rh = rb[2] - rb[0], rb[3] - rb[1]
    lw, lh = lb[2] - lb[0], lb[3] - lb[1]

    print(f"{name:4} rotated={str(slot.rotated):5} "
          f"cell {slot.cell_right - slot.cell_left:6.1f} x {slot.pair_top - slot.pair_bottom:6.1f}  "
          f"half {rw:6.1f} x {rh:6.1f}")

    def check(label, ok, detail=""):
        print(f"      {'OK  ' if ok else 'FAIL'} {label}{('  ' + detail) if detail else ''}")
        if not ok:
            failures.append(f"{name}: {label} {detail}")

    if slot.rotated:
        want_w, want_h = fh, fw
        check("half is the feather turned (w==feather h)", abs(rw - want_w) < 1e-6,
              f"{rw:.3f} vs {want_w:.3f}")
        check("half is the feather turned (h==feather w)", abs(rh - want_h) < 1e-6,
              f"{rh:.3f} vs {want_h:.3f}")
        # stacked: identical x extents, separated in y by the gap
        check("halves share x extent",
              abs(lb[0] - rb[0]) < 1e-6 and abs(lb[2] - rb[2]) < 1e-6)
        lower, upper = (lb, rb) if lb[1] < rb[1] else (rb, lb)
        vgap = upper[1] - lower[3]
        check(f"vertical gap == {gap:.0f}", abs(vgap - gap) < 1e-6, f"{vgap:.3f}")
        check("as-built half is below the axis (R)", rb[3] <= slot.axis_y + 1e-6,
              f"rb top {rb[3]:.2f} vs axis {slot.axis_y:.2f}")
        check("mirrored half is above the axis (L)", lb[1] >= slot.axis_y - 1e-6,
              f"lb bottom {lb[1]:.2f} vs axis {slot.axis_y:.2f}")
        # exact reflection about the horizontal axis
        right = gen.transform_polys(f.polys_right, slot.right_to_page)
        left = gen.transform_polys(f.polys_right, slot.left_to_page)
        refl = [[(x, 2 * slot.axis_y - y) for x, y in poly] for poly in right]
        err = max(abs(a[0] - b[0]) + abs(a[1] - b[1])
                  for p, q in zip(refl, left) for a, b in zip(p, q))
        check("vertices are exact reflections", err < 1e-9, f"err {err:.2e}")
    else:
        check("half width == feather width", abs(rw - fw) < 1e-6)
        check("half height == feather height", abs(rh - fh) < 1e-6)
        check("halves share y extent",
              abs(lb[1] - rb[1]) < 1e-6 and abs(lb[3] - rb[3]) < 1e-6)
        hgap = rb[0] - lb[2]
        check(f"horizontal gap == {gap:.0f}", abs(hgap - gap) < 1e-6, f"{hgap:.3f}")
        right = gen.transform_polys(f.polys_right, slot.right_to_page)
        left = gen.transform_polys(f.polys_right, slot.left_to_page)
        refl = [[(2 * slot.axis_x - x, y) for x, y in poly] for poly in right]
        err = max(abs(a[0] - b[0]) + abs(a[1] - b[1])
                  for p, q in zip(refl, left) for a, b in zip(p, q))
        check("vertices are exact reflections", err < 1e-9, f"err {err:.2e}")

    # the pair must fill, and not spill out of, its cell
    check("inside cell",
          slot.cell_left - 1e-6 <= min(lb[0], rb[0])
          and max(lb[2], rb[2]) <= slot.cell_right + 1e-6
          and slot.pair_bottom - 1e-6 <= min(lb[1], rb[1])
          and max(lb[3], rb[3]) <= slot.pair_top + 1e-6)

print()
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f_ in failures:
        print("  " + f_)
    sys.exit(1)
print(f"all {len(names)} pairs placed correctly")
