"""Feasibility pipeline: extract feather outlines from the reference image.

Steps:
 1. Load image, model local background (median filter), compute luminance dev
    + warm chroma (R-B) to build a foreground mask (feathers appear as full
    silhouettes on the neutral-gray backdrop).
 2. Clean the mask (open/close/fill holes), remove the scale-bar & text region.
 3. Label connected components and pick feather candidates.
 4. Trace each candidate's outer contour (marching squares) and simplify/smooth.
 5. Scale pixel coords to cm using the detected 54cm scale bar.
 6. Optionally write SVG + DXF per feather using the generator's serializers.

Run from the investigations/feather-outline dir (imports contour.py) with the
generator's .pytest-deps on the path for DXF.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from contour import closed_contour

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
OUT = r"C:\ode\wings-pcbs\investigations\feather-outline\out"
os.makedirs(OUT, exist_ok=True)

# --- step 1: foreground mask ------------------------------------------------
img = Image.open(SRC).convert("RGB")
rgb = np.asarray(img, dtype=np.float32)
gray = np.asarray(img.convert("L"), dtype=np.float32)
R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
RB = R - B
bg = ndi.median_filter(gray, size=61)
dev = gray - bg

fore = (dev < -14) | (RB > 9)
fore = ndi.binary_opening(fore, structure=np.ones((3, 3)))
fore = ndi.binary_closing(fore, structure=np.ones((5, 5)))
fore = ndi.binary_fill_holes(fore)

# Crop to the plate (feathers area) so we don't catch the white margin/scale bar.
H, W = fore.shape
plate = np.zeros_like(fore)
plate[:, :928] = True   # feathers live left of the vertical scale bar (x~1040)
mask = fore & plate

# --- step 2: detect scale bar (54 cm) ----------------------------------------
dark = gray < 60
cols = dark[:, W // 2:].sum(axis=0)
tall = np.where(cols > 0.5 * H)[0] + W // 2
bar_y0 = bar_y1 = 0
if len(tall):
    bx0, bx1 = int(tall.min()), int(tall.max())
    ys = np.where(dark[:, bx0:bx1 + 1].any(axis=1))[0]
    bar_y0, bar_y1 = int(ys.min()), int(ys.max())
bar_px_h = bar_y1 - bar_y0
scale_cm_per_px = 54.0 / bar_px_h if bar_px_h else 0
print(f"scale bar px height={bar_px_h}  cm/px={scale_cm_per_px:.6f}")

# --- step 3: label & find feathers ------------------------------------------
lab, n = ndi.label(mask)
sizes = ndi.sum(mask, lab, range(1, n + 1))
print(f"components={n}")

# Feather candidate: reasonably large, tall (aspect >= 1.3), in plate.
feathers = []
for i in range(1, n + 1):
    if sizes[i - 1] < 900:
        continue
    ys, xs = np.nonzero(lab == i)
    h = ys.max() - ys.min()
    w = xs.max() - xs.min()
    if h < 90:
        continue
    if h < 1.1 * w:      # not feather-like (too round) unless small
        continue
    # skip the giant merged blob if it dwarfs everything (overlap row) — keep for now
    feathers.append({
        "id": i, "area": int(sizes[i - 1]),
        "x0": int(xs.min()), "x1": int(xs.max()),
        "y0": int(ys.min()), "y1": int(ys.max()),
        "h": int(h), "w": int(w),
    })
feathers.sort(key=lambda f: f["area"], reverse=True)
print(f"feather candidates={len(feathers)}")

# --- step 4+5: trace & scale --------------------------------------------------
results = []
base = Image.open(SRC).convert("RGB")
draw = ImageDraw.Draw(base)
palette = [(255, 0, 0), (0, 200, 255), (0, 255, 0), (255, 0, 255),
           (255, 180, 0), (120, 0, 255), (0, 255, 255), (255, 96, 96)]
for k, f in enumerate(feathers):
    blob = lab == f["id"]
    pts = closed_contour(blob, simplify_eps=1.2, smooth_k=4)
    if len(pts) < 4:
        # fall back to bbox-ish contour
        continue
    pts_cm = [(x * scale_cm_per_px, y * scale_cm_per_px) for (x, y) in pts]
    w_cm = max(p[0] for p in pts_cm) - min(p[0] for p in pts_cm)
    h_cm = max(p[1] for p in pts_cm) - min(p[1] for p in pts_cm)
    results.append({
        "mask_id": f["id"], "area_px": f["area"], "n_pts": len(pts_cm),
        "bbox_cm": {"w": round(w_cm, 2), "h": round(h_cm, 2)},
        "x0_px": f["x0"], "x1_px": f["x1"], "y0_px": f["y0"], "y1_px": f["y1"],
        "outline_cm": [(round(px, 4), round(py, 4)) for (px, py) in pts_cm],
    })
    col = palette[k % len(palette)]
    if k < 8:
        xy = [(x, y) for (x, y) in pts]
        draw.line(xy + [xy[0]], fill=col, width=2)

base.save(os.path.join(OUT, "overlay_scaled.png"))

# --- step 6: serialize via the generator's writers --------------------------
def write_svg(outline, path, title=""):
    from feathergen.serialize import _bbox, SVG_VIEWBOX_SIZE, SVG_PAD
    min_x, min_y, max_x, max_y = _bbox(outline)
    w, h = max_x - min_x, max_y - min_y
    scale = (SVG_VIEWBOX_SIZE - 2 * SVG_PAD) / max(w, h)
    ox, oy = SVG_PAD - min_x * scale, SVG_PAD - min_y * scale
    def pt(p): return f"{p[0] * scale + ox:.3f},{p[1] * scale + oy:.3f}"
    d = "M " + pt(outline[0]) + " " + " ".join(f"L {pt(p)}" for p in outline[1:]) + " Z"
    t = f"<title>{title}</title>" if title else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_VIEWBOX_SIZE} {SVG_VIEWBOX_SIZE}">{t}'
           f'<path d="{d}" fill="none" stroke="black" stroke-width="0.5"/></svg>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)


def write_dxf(outline, layer, path):
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    if layer not in doc.layers:
        doc.layers.add(layer)
    msp.add_lwpolyline(list(outline), close=True, dxfattribs={"layer": layer})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.saveas(path)


svg_dir = os.path.join(OUT, "svg")
dxf_dir = os.path.join(OUT, "dxf")
for r in results[:8]:
    o = r["outline_cm"]
    name = f"feather_{r['mask_id']}"
    write_svg(o, os.path.join(svg_dir, name + ".svg"), title=name)
    try:
        write_dxf(o, "EXTRACT", os.path.join(dxf_dir, name + ".dxf"))
    except Exception as e:
        print(f"  dxf skip {name}: {e}")

json.dump(results, open(os.path.join(OUT, "outlines.json"), "w"), indent=2)
print(f"traced {len(results)} feathers; wrote overlay_scaled.png, outlines.json, svg/, dxf/")
