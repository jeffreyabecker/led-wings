#!/usr/bin/env python3
"""Pass 2: add each individual's quill centre line to its feather group in the aggregate.

The centre line was hand-authored in ``individuals/<LABEL>.svg`` as
``<path id="{LABEL}-center-line">``. Its ``d`` is in that file's own viewBox space, while an
aggregate feather group lives in the catalog's frame, so the raw ``d`` cannot be copied across:
dropped in as-is the line lands beside its feather. The two files' outlines are the same curve,
though, and the outline points give an exact correspondence between the two spaces (checked per
feather, worst residual 0.00000 mm), so the same map is applied to the line:

* rotate the line onto the aggregate outline's long axis (the B feathers are a quarter turn from
  the individuals' upright form);
* scale its length to the aggregate outline's, and align the two area centroids;
* write the result as one absolute cubic in the aggregate group's frame, so the added ``<path>``
  needs no ``transform`` of its own and stays 1:1 mm;
* ``style`` and ``sodipodi:nodetypes`` come across verbatim; the point count and curve shape are
  the source's, only the position and size change.

Usage
-----
    python add-feather-centerlines.py --check     # report only, write nothing
    python add-feather-centerlines.py
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AGG = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
DEFAULT_IND = os.path.join(HERE, "as-built", "vectors", "individuals")
SVG_NS = "http://www.w3.org/2000/svg"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_NS = "http://www.w3.org/1999/xlink"
for _prefix, _uri in (("", SVG_NS), ("sodipodi", SODIPODI_NS),
                      ("inkscape", INKSCAPE_NS), ("xlink", XLINK_NS)):
    ET.register_namespace(_prefix, _uri)


def load_builder():
    path = os.path.join(HERE, "build-feather-aggregate.py")
    spec = importlib.util.spec_from_file_location("build_feather_aggregate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def local(tag):
    return tag.split("}")[-1]


def area_centroid(pts):
    a = cx = cy = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(a) < 1e-9:
        return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    return (cx / (3 * a), cy / (3 * a))


def map_line(line, ind_out, agg_out, b):
    """The centre line, moved from the individual's space into the aggregate group's frame."""
    ab, ib, lb = b.bbox_of(agg_out), b.bbox_of(ind_out), b.bbox_of(line)
    agg_tall = (ab[3] - ab[1]) >= (ab[2] - ab[0])
    line_tall = (lb[3] - lb[1]) >= (lb[2] - lb[0])
    deg = 0.0 if agg_tall == line_tall else 90.0
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    moved = [(c * p[0] - s * p[1], s * p[0] + c * p[1]) for p in line]
    mb = b.bbox_of(moved)
    k = ((ab[3] - ab[1]) / (mb[3] - mb[1])) if agg_tall else ((ab[2] - ab[0]) / (mb[2] - mb[0]))
    moved = [(p[0] * k, p[1] * k) for p in moved]
    ccx, ccy = area_centroid(moved)
    acx, acy = area_centroid(agg_out)
    return [(p[0] + acx - ccx, p[1] + acy - ccy) for p in moved], deg, k


def as_path_d(pts, precision=4):
    """A single absolute cubic through the given samples, from the first point."""
    n = len(pts)
    out = [f"M {pts[0][0]:.{precision}f},{pts[0][1]:.{precision}f}"]
    for i in range(n - 1):
        p0, p1 = pts[i], pts[i + 1]
        c1 = (p0[0] + (p1[0] - p0[0]) / 3.0, p0[1] + (p1[1] - p0[1]) / 3.0)
        c2 = (p0[0] + 2.0 * (p1[0] - p0[0]) / 3.0, p0[1] + 2.0 * (p1[1] - p0[1]) / 3.0)
        out.append(f"C {c1[0]:.{precision}f},{c1[1]:.{precision}f} "
                   f"{c2[0]:.{precision}f},{c2[1]:.{precision}f} "
                   f"{p1[0]:.{precision}f},{p1[1]:.{precision}f}")
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregate", default=DEFAULT_AGG,
                    help=f"aggregate to update (default {DEFAULT_AGG})")
    ap.add_argument("--individuals", default=DEFAULT_IND,
                    help=f"folder of individual feather SVGs (default {DEFAULT_IND})")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    b = load_builder()
    with open(args.aggregate, encoding="utf-8", newline="") as fh:
        text = fh.read()
    root = ET.fromstring(text)

    names = sorted(f for f in os.listdir(args.individuals) if f.endswith(".svg"))
    added, already, missing, report = [], [], [], []
    for name in names:
        label = os.path.splitext(name)[0]
        ag = next((g for g in root.iter(f"{{{SVG_NS}}}g") if g.get("id") == label), None)
        if ag is None:
            missing.append(f"{label} (no group)")
            continue
        if any((p.get("id") or "") == f"{label}-center-line" for p in ag.iter(f"{{{SVG_NS}}}path")):
            already.append(label)
            continue
        aout = next((e for e in ag if (e.get("id") or "") == f"{label}-outline"), None)
        if aout is None:
            missing.append(f"{label} (no outline)")
            continue

        ir = ET.parse(os.path.join(args.individuals, name)).getroot()
        ig = next((g for g in ir.iter(f"{{{SVG_NS}}}g") if g.get("id") == label), None)
        if ig is None:
            missing.append(f"{label} (no group in the individual)")
            continue
        iout = next((e for e in ig if (e.get("id") or "") == f"{label}-outline"), None)
        icl = next((e for e in ig if (e.get("id") or "") == f"{label}-center-line"), None)
        if icl is None:
            missing.append(f"{label} (no centre line in the individual)")
            continue

        agg_out = b.path_points(aout.get("d"))
        ind_out = [b.mat_apply(b.parse_transform(iout.get("transform")), p)
                   for p in b.path_points(iout.get("d"))]
        line = [b.mat_apply(b.parse_transform(icl.get("transform")), p)
                for p in b.path_points(icl.get("d"))]
        pts, deg, k = map_line(line, ind_out, agg_out, b)

        attrs = {"id": f"{label}-center-line"}
        if icl.get("style"):
            attrs["style"] = icl.get("style")
        for ns in (f"{{{SODIPODI_NS}}}nodetypes",):
            if icl.get(ns):
                attrs[ns] = icl.get(ns)
        el = ET.Element(f"{{{SVG_NS}}}path", attrs)
        el.set("d", as_path_d(pts))
        added.append((label, el))
        report.append((label, deg, k, b.bbox_of(pts), b.bbox_of(agg_out)))

    print(f"{os.path.basename(args.aggregate)}: {len(names)} individuals, "
          f"{len(added)} centre lines to add"
          + (f", {len(already)} already present" if already else ""))
    for label, deg, k, lb, ab in report:
        fits = (lb[0] >= ab[0] - 1 and lb[2] <= ab[2] + 1)
        print(f"  {label:5s} rotate {deg:3.0f} deg  scale {k:6.3f}  "
              f"line x {lb[0]:7.1f}..{lb[2]:7.1f} vs outline x {ab[0]:7.1f}..{ab[2]:7.1f}"
              + ("" if fits else "   <-- wider than the feather"))
    if missing:
        print("  ! not added: " + ", ".join(missing))

    if args.check:
        print("(--check: nothing written)")
        return 1 if missing else 0
    if not added:
        print("nothing to do")
        return 1 if missing else 0

    for g in root.iter(f"{{{SVG_NS}}}g"):
        for i, el in enumerate(g):
            if local(el.tag) == "path" and (el.get("id") or "").endswith("-outline"):
                for label, new in added:
                    if g.get("id") == label:
                        g.insert(i + 1, new)
                        break
                break

    ET.indent(root, space="  ")
    new_text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                + ET.tostring(root, encoding="unicode") + "\n")
    check = ET.fromstring(new_text)
    for label, el in added:
        g = next(g for g in check.iter(f"{{{SVG_NS}}}g") if g.get("id") == label)
        got = [p for p in g.iter(f"{{{SVG_NS}}}path") if (p.get("id") or "") == f"{label}-center-line"]
        if len(got) != 1 or got[0].get("d") != el.get("d"):
            raise SystemExit(f"{label}: added line does not match; nothing written")

    with open(args.aggregate, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    print(f"wrote {args.aggregate}: +{len(added)} centre lines")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
