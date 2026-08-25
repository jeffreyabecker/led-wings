"""Feasibility: combined foreground mask (dark dev + warm chroma) on flight feathers.

Goal: capture the FULL vane width of the dark flight/primaries, then trace.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from contour import closed_contour

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
OUT = r"C:\ode\wings-pcbs\investigations\feather-outline\out"
img = Image.open(SRC).convert("RGB")
rgb = np.asarray(img, dtype=np.float32)
gray = np.asarray(img.convert("L"), dtype=np.float32)
R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
RB = R - B
bg = ndi.median_filter(gray, size=61)
dev = gray - bg

# foreground = clearly darker than bg OR clearly warm
fore = (dev < -14) | (RB > 9)
fore = ndi.binary_opening(fore, structure=np.ones((3, 3)))
fore = ndi.binary_closing(fore, structure=np.ones((5, 5)))
fore = ndi.binary_fill_holes(fore)

Image.fromarray((fore * 255).astype(np.uint8)).save(OUT + r"\fore_combined.png")

# Focus on primaries region and label
region = np.zeros_like(fore)
region[220:520, 20:250] = True
fmask = fore & region
lab, n = ndi.label(fmask)
sizes = ndi.sum(fmask, lab, range(1, n + 1))
print("primaries-region components:", n)

base = Image.open(SRC).convert("RGB")
draw = ImageDraw.Draw(base)
colors = [(255, 0, 0), (0, 200, 255), (0, 255, 0), (255, 0, 255), (255, 180, 0), (120, 0, 255), (0, 255, 255)]
picked = []
for i in range(1, n + 1):
    if sizes[i - 1] < 1500:
        continue
    ys, xs = np.nonzero(lab == i)
    h, w = ys.max() - ys.min(), xs.max() - xs.min()
    if h > 90 and h > 1.2 * w:
        picked.append((i, int(sizes[i - 1]), h, w))
print("tall primaries:", len(picked))
for k, (i, area, h, w) in enumerate(sorted(picked, key=lambda c: -c[1])[:6]):
    blob = lab == i
    poly = closed_contour(blob, simplify_eps=1.2, smooth_k=4)
    print("  id %d area=%d h=%d w=%d contour=%d" % (i, area, h, w, len(poly)))
    if len(poly) > 3:
        xy = [(x, y) for (x, y) in poly]
        draw.line(xy + [xy[0]], fill=colors[k % len(colors)], width=2)

base.save(OUT + r"\trace_combined.png")
print("saved trace_combined.png")
