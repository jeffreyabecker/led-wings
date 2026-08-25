"""Check whether chroma (R-B / saturation) separates feathers from the gray backdrop.

Background is neutral gray (R~=G~=B). Brown feathers are warm (R > B).
"""
import numpy as np
from PIL import Image

SRC = r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png"
img = Image.open(SRC).convert("RGB")
a = np.asarray(img, dtype=np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]

# neutral gray: channels approx equal; warm: R-B big
RB = R - B
RG = R - G
print("R-B: min=%.1f max=%.1f mean=%.1f" % (RB.min(), RB.max(), RB.mean()))
print("R-G: min=%.1f max=%.1f mean=%.1f" % (RG.min(), RG.max(), RG.mean()))

# Sample background patches (neutral gray) vs feather cores (warm brown)
grey_pts = [(130, 800), (110, 770), (90, 780), (0, 0), (0, 500), (700, 700)]
print("background R-B samples:")
for (y, x) in grey_pts:
    print("  (%d,%d) RGB=%s R-B=%.0f" % (x, y, a[y, x].astype(int).tolist(), RB[y, x]))

# feather cores: a couple known dark plumage pixels
feat_pts = [(400, 60), (390, 100), (380, 150), (420, 240), (430, 500), (280, 600)]
print("feather R-B samples:")
for (y, x) in feat_pts:
    print("  (%d,%d) RGB=%s R-B=%.0f" % (x, y, a[y, x].astype(int).tolist(), RB[y, x]))

# Histogram of R-B on neutral-gray plate vs elsewhere. Foreground = warm.
from scipy import ndimage as ndi
bg = ndi.median_filter(np.asarray(Image.open(SRC).convert("L"), dtype=np.float32), size=61)
# report warm pixel fraction at thresholds
for t in (5, 8, 10, 12, 15):
    print("R-B > %d  frac=%.4f" % (t, (RB > t).mean()))
