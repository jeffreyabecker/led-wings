"""Locate the 54cm scale bar (the tall black vertical bar at right of plate).

The bar is near-black on the white margin, tall and thin. We scan the right-side
white margin region for dark columns to find its x-extent, and within those
columns find the y-extent (top..bottom) of contiguous dark pixels.
"""
import numpy as np
from PIL import Image

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
img = Image.open(SRC).convert("L")
a = np.asarray(img, dtype=np.uint8)
H, W = a.shape
print(f"image {W}x{H}")

# The plate (gray feathers region) ends before the white margin. Scan x >= W-200.
dark = a < 60  # near-black bar
# count dark pixels per column in the right half
cols = dark[:, W//2:].sum(axis=0)
xs = np.where(cols > 0)[0] + W//2
print("dark columns (right half), x range:", xs.min() if len(xs) else None, xs.max() if len(xs) else None)

# The bar is tall: find columns where dark count is large (near column height)
tall_cols = np.where(cols > 0.5 * H)[0] + W//2
if len(tall_cols):
    print("tall dark columns:", tall_cols.min(), tall_cols.max(), "count", len(tall_cols))
    bar_x0, bar_x1 = int(tall_cols.min()), int(tall_cols.max())
    sub = dark[:, bar_x0:bar_x1+1]
    ys = np.where(sub.any(axis=1))[0]
    print("bar y-extent:", ys.min(), ys.max(), "px_height", int(ys.max()-ys.min()+1))
    print("bar x-extent:", bar_x0, bar_x1, "px_width", int(bar_x1-bar_x0+1))
else:
    # fall back: report thickest dark run region
    print("no tall columns; max dark col count:", cols.max())
