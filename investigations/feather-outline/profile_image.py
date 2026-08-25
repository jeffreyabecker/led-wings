"""Profile the reference image: grayscale stats, background estimate, contrast.

Feasibility pass - run before building the full extraction pipeline.
"""
import numpy as np
from PIL import Image

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"

img = Image.open(SRC).convert("L")
a = np.asarray(img, dtype=np.uint8)
H, W = a.shape
print(f"image {W}x{H}")
print(f"min={a.min()} max={a.max()} mean={a.mean():.1f} median={np.median(a):.0f}")

hist, edges = np.histogram(a, bins=256, range=(0, 256))
# top 5 gray levels
order = np.argsort(hist)[::-1][:8]
print("top gray levels (value:count):")
for v in order:
    print(f"  {v:3d} : {hist[v]:7d}")

# Sample a few known background patches (avoid feathers/labels/scale bar).
# Background is the flat gray between feathers. Sample corners and gaps.
patches = {
    "top-left corner": (0, 0, 120, 60),
    "top-right of gray (y~8, x~830)": (8, 815, 40, 855),
    "mid gap under 'throat'": (95, 760, 115, 800),
    "right margin of gray before white bar": (350, 830, 400, 845),
    "bottom-left corner": (660, 0, 720, 60),
}
for name, (y0, x0, y1, x1) in patches.items():
    p = a[y0:y1, x0:x1]
    print(f"{name:38s} mean={p.mean():6.1f} std={p.std():5.2f} med={np.median(p):.0f}")

# Overall: build a mask for a few thresholds, report fractions
for t in (30, 40, 50, 60, 80, 100):
    dev = np.abs(a.astype(np.int16) - int(np.median(a)))
    print(f"threshold {t:3d}: frac dev>{t} = {(dev > t).mean():.4f}")
