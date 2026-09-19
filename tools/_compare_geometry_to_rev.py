"""Compare every feather's geometry against an earlier git revision.

Reports bounding-box and vertex differences, so a source edit can be judged by
whether it actually changes the printed output.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402

REPO = Path(r"C:\ode\wings-pcbs")
SRC = REPO / "mechanical/templates/as-built/vectors/individuals"
BASE = sys.argv[1] if len(sys.argv) > 1 else "0ae0e52"

tmp = Path(tempfile.mkdtemp())
changed = []
for cur in sorted(SRC.glob("*.svg")):
    name = cur.stem
    rel = f"mechanical/templates/as-built/vectors/individuals/{cur.name}"
    old = subprocess.run(["git", "show", f"{BASE}:{rel}"],
                         capture_output=True, cwd=REPO).stdout
    if not old:
        continue
    old_path = tmp / cur.name
    old_path.write_bytes(old)
    a = load_feather(cur)
    b = load_feather(old_path)
    box_same = all(abs(x - y) < 1e-9 for x, y in zip(a.box, b.box))
    vert_same = (len(a.polys_right) == len(b.polys_right)
                 and all(abs(p[0] - q[0]) < 1e-9 and abs(p[1] - q[1]) < 1e-9
                         for pa, qa in zip(a.polys_right, b.polys_right)
                         for p, q in zip(pa, qa)))
    if not (box_same and vert_same):
        changed.append(name)
        print(f"  {name:5} bbox {tuple(round(v,3) for v in a.box)}  vs  "
              f"{tuple(round(v,3) for v in b.box)}   verts_same={vert_same}")

print()
if changed:
    print(f"{len(changed)} file(s) change geometry: {', '.join(changed)}")
else:
    print("no file changes geometry - print output unaffected")
