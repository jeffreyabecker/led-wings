"""Test the marching-squares contour tracer on known shapes + real blobs."""
import numpy as np
from scipy import ndimage as ndi
from contour import _marching_squares, contour_polygons, closed_contour

# 1) Solid rectangle
rect = np.zeros((40, 50), dtype=bool)
rect[5:35, 5:45] = True
polys = contour_polygons(rect)
print("rect: loops=", len(polys), "len=", len(polys[0]))
arr = polys[0]
print("  y range:", arr[:, 0].min(), arr[:, 0].max(), "x range:", arr[:, 1].min(), arr[:, 1].max())
assert len(polys) == 1

# 2) Rectangle with a notch (concave)
notch = np.zeros((40, 50), dtype=bool)
notch[5:35, 5:45] = True
notch[20:25, 20:30] = False
polys = contour_polygons(notch)
print("notch: loops=", len(polys), "len=", len(polys[0]))

# 3) Two separate rectangles -> two loops
two = np.zeros((60, 60), dtype=bool)
two[5:25, 5:25] = True
two[35:55, 35:55] = True
polys = contour_polygons(two)
print("two: loops=", len(polys), "lens=", sorted(len(p) for p in polys))

# 4) Real blob: candidate 146 (a clean primary)
from PIL import Image
img = Image.open(r"C:\ode\wings-pcbs\investigations\feather-outline\reference_feathers.png").convert("L")
a = np.asarray(img, dtype=np.float32)
bg = ndi.median_filter(a, size=61)
dev = a - bg
dark = dev < -25
dark = ndi.binary_opening(dark, structure=np.ones((3, 3)))
dark = ndi.binary_closing(dark, structure=np.ones((3, 3)))
lab, n = ndi.label(dark)
blob = lab == 146
poly = closed_contour(blob)
print("real blob 146: contour pts=", len(poly))
ys = [p[1] for p in poly]; xs = [p[0] for p in poly]
print("  bbox x:", min(xs), max(xs), "y:", min(ys), max(ys))
