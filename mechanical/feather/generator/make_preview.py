"""Build a labeled contact-sheet SVG of every feather outline.

Reads feathers.json, renders each outline via feather_outline, and lays
them out in a grid on one SVG (no external deps). Output:
``generator/out/preview.svg``.

Usage: python make_preview.py [out.svg] [--adjust -5]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from feathergen.outline import feather_outline  # noqa: E402

CELL = 200      # px per cell (default; overridable via --cell)
PAD = 18        # px padding inside each cell
LABEL_H = 16    # px for the id label row


def fit_pts(outline, w, h):
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    bw = max(xs) - min(xs)
    bh = max(ys) - min(ys)
    s = min(w / bw, h / bh) if bw and bh else 1.0
    ox = (w - bw * s) / 2 - min(xs) * s
    oy = (h - bh * s) / 2 - min(ys) * s
    return [(x * s + ox, y * s + oy) for x, y in outline]


def path_d(pts):
    d = f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"
    for x, y in pts[1:]:
        d += f" L {x:.2f},{y:.2f}"
    return d + " Z"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=str(Path(__file__).parent / "out" / "preview.svg"))
    ap.add_argument("--adjust", type=float, default=0.0,
                    help="vane_ratio_adjustment (e.g. -0.05 = -5%)")
    ap.add_argument("--cell", type=float, default=200.0,
                    help="cell size in px (default 200)")
    args = ap.parse_args()

    data = json.loads((Path(__file__).parent / "feathers.json").read_text(encoding="utf-8"))
    rows = data["feathers"]

    CELL = args.cell
    cols = 12
    rows_n = (len(rows) + cols - 1) // cols
    W = cols * CELL
    H = rows_n * CELL

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'<rect width="100%" height="100%" fill="#fdfdfd"/>',
    ]
    for i, f in enumerate(rows):
        cx = (i % cols) * CELL
        cy = (i // cols) * CELL
        res = feather_outline(f, vane_ratio_adjustment=args.adjust)
        pts = fit_pts(res["outline"], CELL - 2 * PAD, CELL - 2 * PAD - LABEL_H)
        parts.append(
            f'<path d="{path_d(pts)}" fill="none" stroke="#222" stroke-width="0.6"/>'
        )
        parts.append(
            f'<text x="{cx + CELL / 2:.1f}" y="{cy + CELL - 4}" '
            f'text-anchor="middle" font-size="9" font-family="sans-serif">'
            f'{f["id"]}</text>'
        )
    parts.append("</svg>")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} feathers, {cols}x{rows_n} grid, "
          f"adjust={args.adjust})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
