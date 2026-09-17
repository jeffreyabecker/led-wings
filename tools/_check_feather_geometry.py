"""Verify parsed feather geometry against the declared SVG page sizes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feather_geometry import load_feather  # noqa: E402

DIR = Path(r"C:\ode\wings-pcbs\mechanical\templates\as-built\vectors\individuals")

print(f"{'name':5} {'bbox W':>8} {'decl W':>8} {'dW':>7} {'bbox H':>8} {'decl H':>8} {'dH':>7} "
      f"{'stroke':>7} {'verts':>6} {'polys':>5} {'closed':>6}")
worst = 0.0
for f in sorted(DIR.glob("*.svg")):
    fe = load_feather(f)
    dw = fe.width - fe.declared_size_mm[0]
    dh = fe.height - fe.declared_size_mm[1]
    worst = max(worst, abs(dw), abs(dh))
    nverts = sum(len(p) for p in fe.polys_right)
    closed = all(
        abs(p[0][0] - p[-1][0]) < 1e-6 and abs(p[0][1] - p[-1][1]) < 1e-6
        for p in fe.polys_right
    )
    print(f"{fe.name:5} {fe.width:8.3f} {fe.declared_size_mm[0]:8.3f} {dw:7.3f} "
          f"{fe.height:8.3f} {fe.declared_size_mm[1]:8.3f} {dh:7.3f} "
          f"{fe.stroke_mm:7.3f} {nverts:6d} {len(fe.polys_right):5d} {str(closed):>6}")

print()
print(f"worst bbox-vs-declared deviation: {worst:.4f} mm")
print("(deviation should be at most ~stroke/2 + declaration rounding of 0.01 mm)")
