"""Segmentation exploration: local-background subtraction to isolate feathers.

We model the gray plate background per-pixel with a large median filter (window
larger than a feather width), then foreground = pixels that deviate from that
local background. Dark feathers deviate negative (darker), pale ones positive
(brighter). This handles the illumination gradient across the plate.

Writes a set of debug PNGs to the out/ dir so we can tune thresholds.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
OUT = r"C:\ode\wings-pcbs\investigations\feather-outline\out"
os.makedirs(OUT, exist_ok=True)

img = Image.open(SRC).convert("L")
a = np.asarray(img, dtype=np.float32)
H, W = a.shape

# Scale bar / white margin are not plate. The plate is roughly x in [0, 930] here.
# We'll operate on full image but background median handles the white margin as
# "bright background", so pale feathers rarely appear there. Keep focused.

# Local background via large median filter
bg = ndi.median_filter(a, size=61)
dev = a - bg            # +ve = brighter than local bg (pale feather/base), -ve darker (dark feather)

# Dark-feather foreground: clearly darker than local background
for t in (18, 25, 32, 40):
    dark = dev < -t
    dark = ndi.binary_opening(dark, structure=np.ones((3, 3)))
    dark = ndi.binary_closing(dark, structure=np.ones((3, 3)))
    lab, n = ndi.label(dark)
    sizes = ndi.sum(dark, lab, range(1, n + 1))
    big = int((sizes > 400).sum())
    Image.fromarray((dark * 255).astype(np.uint8)).save(os.path.join(OUT, f"dark_t{t}.png"))
    print(f"dark t={t}: components={n} big(>400px)={big}")

# Pale-feather foreground: clearly brighter than local background
for t in (18, 25, 32):
    pale = dev > t
    pale = ndi.binary_opening(pale, structure=np.ones((3, 3)))
    pale = ndi.binary_closing(pale, structure=np.ones((3, 3)))
    lab, n = ndi.label(pale)
    sizes = ndi.sum(pale, lab, range(1, n + 1))
    big = int((sizes > 400).sum())
    Image.fromarray((pale * 255).astype(np.uint8)).save(os.path.join(OUT, f"pale_t{t}.png"))
    print(f"pale t={t}: components={n} big(>400px)={big}")

print("wrote debug masks to", OUT)
