"""Run the full contour test on the 5 cleanest primaries and overlay for review."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from contour import closed_contour

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
OUT = r"C:\ode\wings-pcbs\investigations\feather-outline\out"
img = Image.open(SRC).convert("L")
a = np.asarray(img, dtype=np.float32)
bg = ndi.median_filter(a, size=61)
dev = a - bg

dark = dev < -25
dark = ndi.binary_opening(dark, structure=np.ones((3, 3)))
dark = ndi.binary_closing(dark, structure=np.ones((3, 3)))
lab, n = ndi.label(dark)
sizes = ndi.sum(dark, lab, range(1, n + 1))

# filter to the primaries region
region = np.zeros_like(dark)
region[220:470, 30:230] = True
cands = []
for i in range(1, n + 1):
    if sizes[i - 1] < 800:
        continue
    ys, xs = np.nonzero(lab == i)
    if region[ys, xs].mean() > 0.5:
        h = ys.max() - ys.min()
        w = xs.max() - xs.min()
        if h > 100 and h > 1.3 * w:
            cands.append((i, int(sizes[i - 1]), int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))

print("primaries found:", len(cands))
for c in sorted(cands, key=lambda c: -c[1])[:6]:
    print("  id=%d area=%d x=%d..%d y=%d..%d" % c)

base = Image.open(SRC).convert("RGB")
draw = ImageDraw.Draw(base)
colors = [(255, 0, 0), (0, 200, 255), (0, 255, 0), (255, 0, 255), (255, 180, 0), (120, 0, 255), (0, 255, 255)]
for k, c in enumerate(sorted(cands, key=lambda c: -c[1])[:6]):
    i = c[0]
    blob = lab == i
    poly = closed_contour(blob, simplify_eps=1.2, smooth_k=4)
    col = colors[k % len(colors)]
    print(f"  id {i}: contour pts={len(poly)}")
    if len(poly) > 3:
        xy = [(x, y) for (x, y) in poly]
        draw.line(xy + [xy[0]], fill=col, width=2)
        # centroid dot
        cx = sum(p[0] for p in xy) / len(xy); cy = sum(p[1] for p in xy) / len(xy)
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=col)

base.save(OUT + r"\trace_primaries.png")
print("saved trace_primaries.png")
