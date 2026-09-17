#!/usr/bin/env python3
"""Break the authoritative aggregate SVG back out into one file per feather.

The aggregate (``as-built/vectors/feathers-aggregate.svg``) is the source of truth: it carries the
hand edits *and* the current arrangement (per-prefix-group rotation/scale, per-feather transforms --
38 of 42 feathers are rotated). This script is the inverse of build-feather-aggregate.py: for every
feather group in the aggregate it writes ``as-built/vectors/individuals/<LABEL>.svg`` holding that
feather -- **straightened** -- plus its label.

What a file contains
--------------------
* the feather **upright**: the outline is rotated so its long axis runs down the page (the
  arrangement's rotations are undone) at the size the aggregate gives it -- the transform is the
  composed transform of every ancestor (prefix group included) times the feather group's own, minus
  its rotation. So an anisotropic group scale such as P's 1.2001x length survives, the rotation does
  not, and the shape is never re-fitted;
* ``<g id="feather">`` carries that transform and the ``<path>`` inside is copied **verbatim**
  (d, transform, style, sodipodi:nodetypes), so an outline is bit-for-bit the aggregate's;
* the label stays level: it is re-anchored onto the straightened feather and its own transform is
  solved so the net effect is the authored ``rotate(180)`` -- level and unstretched whatever the
  group's rotation or scale;
* the ``viewBox`` is ``0 0 w h`` with the feather sitting --margin-mm in from the corner, so each
  file opens 1:1 on its own feather. (A shared sheet frame is meaningless once feathers are rotated
  upright, so each file gets its own local frame.)

Usage
-----
    python split-feather-aggregate.py                  # straightened, aggregate sizes
    python split-feather-aggregate.py --check          # verify only, write nothing
    python split-feather-aggregate.py --no-straighten  # exactly as drawn in the aggregate
    python split-feather-aggregate.py --no-ancestors   # size from the feather's own transform
    python split-feather-aggregate.py --margin-mm 8

The two flags are independent: ``--no-ancestors`` drops the *prefix group's* arrangement (its
rotation and its ~1.2x length scale) and keeps only the feather's own transform; ``--no-straighten``
keeps the arrangement rotation, writing the geometry exactly as it lies in the aggregate (a lossless
dump, but most files then open rotated).

Every run self-checks: each outline must equal the aggregate's put through the same straightening
(point-for-point), the feather must come out axis-aligned and keep its length, the label must stay
level, verbatim in text, on its own feather, and the file must read back through
build-feather-aggregate.py as the same geometry.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
DEFAULT_OUT = os.path.join(HERE, "as-built", "vectors", "individuals")
MARGIN_MM = 8.0
LABEL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")
TIP_SLAB_MM = 3.0        # how far in from each end the tip test measures the vane width
TOL_MM = 1e-4            # geometry is compared through written text: 0.1 um, far below any use
UPRIGHT_TOL_DEG = 0.5    # how far the straightened long axis may sit off vertical


def load_builder():
    """Import build-feather-aggregate.py for its affine/path helpers.

    The splitter is the exact inverse of that script and must agree with it on how transforms are
    parsed and how outlines are sampled; sharing the code is what guarantees that (and its
    `load_all` is what the read-back check loads the written files with).
    """
    path = os.path.join(HERE, "build-feather-aggregate.py")
    spec = importlib.util.spec_from_file_location("build_feather_aggregate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# affine extras (mat_mul / mat_apply / parse_transform come from the builder)
# --------------------------------------------------------------------------- #
def mat_mul(m, n):
    """m @ n -- apply n first, then m. Mirrors the builder's helper."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def mat_translate(x, y):
    return (1.0, 0.0, 0.0, 1.0, x, y)


def mat_rotation(deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return (c, s, -s, c, 0.0, 0.0)


def rotation_about(deg, x, y):
    return mat_mul(mat_mul(mat_translate(x, y), mat_rotation(deg)), mat_translate(-x, -y))


def mat_inverse(m):
    a, b, c, d, e, f = m
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError(f"singular transform {m}")
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def transform_str(m):
    a, b, c, d, e, f = m
    if (a, b, c, d) == (1.0, 0.0, 0.0, 1.0):
        return f"translate({e:.4f},{f:.4f})"
    return f"matrix({a:.10g},{b:.10g},{c:.10g},{d:.10g},{e:.10g},{f:.10g})"


# --------------------------------------------------------------------------- #
# reading the aggregate
# --------------------------------------------------------------------------- #
def parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}


def ancestors(el, parents):
    out = []
    while el in parents:
        el = parents[el]
        out.append(el)
    return out


def composed_transform(el, parents, b, include_ancestors=True):
    """`el`'s own transform, optionally with every ancestor's (root last, applied first)."""
    chain = [b.parse_transform(el.get("transform"))]
    if include_ancestors:
        chain += [b.parse_transform(a.get("transform")) for a in ancestors(el, parents)]
    out = b.IDENT
    for local in reversed(chain):
        out = mat_mul(out, local)
    return out


def outline_points(group, ctm, b):
    """Absolute outline points of a feather group under a known transform."""
    pts = []
    for p in group.iter(f"{{{b.SVG_NS}}}path"):
        ptm = mat_mul(ctm, b.parse_transform(p.get("transform")))
        pts.extend(b.mat_apply(ptm, q) for q in b.path_points(p.get("d")))
    return pts


def label_net(group, ctm, b):
    """[(net transform, anchor)] per label: net maps the text's local coords into the frame."""
    out = []
    for t in group.iter(f"{{{b.SVG_NS}}}text"):
        net = mat_mul(ctm, b.parse_transform(t.get("transform")))
        anchor = b.mat_apply(net, (float(t.get("x", 0.0)), float(t.get("y", 0.0))))
        out.append((net, anchor, t))
    return out


def find_feathers(root, b):
    """[(label, group, parents)] for every <g> whose id is a feather code and holds a path."""
    parents = parent_map(root)
    found = []
    for g in root.iter(f"{{{b.SVG_NS}}}g"):
        label = g.get("id") or ""
        if not LABEL_RE.match(label) or not list(g.iter(f"{{{b.SVG_NS}}}path")):
            continue
        found.append((label, g, parents))
    return sorted(found, key=lambda t: (LABEL_RE.match(t[0]).group(1),
                                        int(LABEL_RE.match(t[0]).group(2))))


# --------------------------------------------------------------------------- #
# straightening
# --------------------------------------------------------------------------- #
def convex_hull(points):
    """Andrew's monotone chain; the hull is what the min-area box needs."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross(out[-2], out[-1], p) <= 0:
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(list(reversed(pts)))[:-1]


def min_area_box(points):
    """(angle of the long side in degrees, long, short) over the minimum-area box.

    Rotating calipers rather than PCA: PCA maximizes variance and leaves a curved feather slightly
    tilted, which would show up as a bounding box taller than it needs to be. The min-area box is
    what "upright" and "same size" both mean here.
    """
    hull = convex_hull(points)
    if len(hull) < 3:
        return 0.0, 0.0, 0.0
    best = None
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        du = [p[0] * ux + p[1] * uy for p in hull]
        dv = [p[0] * nx + p[1] * ny for p in hull]
        eu, ev = max(du) - min(du), max(dv) - min(dv)
        area = eu * ev
        if best is None or area < best[0]:
            if eu >= ev:
                best = (area, math.degrees(math.atan2(uy, ux)), eu, ev)
            else:
                best = (area, math.degrees(math.atan2(ny, nx)), ev, eu)
    return best[1] % 180.0, best[2], best[3]


def narrow_end(points, slab=TIP_SLAB_MM):
    """Which end is the tip: the narrower one, measured `slab` mm in from each end."""
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)

    def width(lo, hi):
        xs = [p[0] for p in points if lo <= p[1] <= hi]
        return (max(xs) - min(xs)) if xs else float("inf")

    return "top" if width(y0, y0 + slab) < width(y1 - slab, y1) else "bottom"


def straighten_map(points, margin):
    """(map, straightened points): rotate the long axis onto +y with the tip down, then place the
    bounding box `margin` in from the origin. Pure rotation + translation, so sizes are untouched.
    """
    angle = min_area_box(points)[0]
    psi = 90.0 - angle
    rot = mat_rotation(psi)
    pts = [b_apply(rot, p) for p in points]
    if narrow_end(pts) == "top":           # the aggregate is flipped: tips down, keep that
        rot = mat_rotation(psi + 180.0)
        pts = [b_apply(rot, p) for p in points]
    x0, y0, _, _ = bbox(pts)
    fit = mat_translate(margin - x0, margin - y0)
    return mat_mul(fit, rot), [b_apply(fit, p) for p in pts]


def b_apply(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


# --------------------------------------------------------------------------- #
# planning one file
# --------------------------------------------------------------------------- #
def copy_element(el, new_id=None, drop=(), add=None):
    attrib = {k: v for k, v in el.attrib.items() if k not in drop}
    if new_id is not None:
        attrib["id"] = new_id
    attrib.update(add or {})
    out = ET.Element(el.tag, attrib)
    out.text = el.text
    return out


def plan(label, group, base, b, margin, straighten=True):
    """Everything one file needs: its transform, its label transforms, its crop, its geometry."""
    points = outline_points(group, base, b)
    smap, spoints = straighten_map(points, margin) if straighten else (b.IDENT, points)
    g_new = mat_mul(smap, base)
    _, long_side, short_side = min_area_box(points)

    labels = []
    for net, anchor, el in label_net(group, base, b):
        if not straighten:
            # nothing is rotated away, so the label keeps its own transform untouched
            labels.append({"el": el, "x": float(el.get("x", 0.0)), "y": float(el.get("y", 0.0)),
                           "transform": None, "anchor": anchor})
            continue
        ax, ay = b_apply(smap, anchor)
        # solve the label's own transform so the net effect is the authored rotate(180): level,
        # unstretched, and anchored on the straightened feather
        net_want = rotation_about(180.0, ax, ay)
        labels.append({"el": el, "x": ax, "y": ay, "anchor": (ax, ay),
                       "transform": mat_mul(mat_inverse(g_new), net_want)})

    box = bbox(spoints)
    for lb in labels:
        size = float(re.sub(r"[^0-9.\-]", "", lb["el"].get("font-size", "6") or "6"))
        box = (min(box[0], lb["x"] - size), min(box[1], lb["y"] - size),
               max(box[2], lb["x"] + size), max(box[3], lb["y"] + size))
    return {"label": label, "group": group, "base": base, "smap": smap, "g_new": g_new,
            "points": spoints, "labels": labels, "box": box,
            "want": (long_side, short_side)}


def build_file(pl, b, straighten):
    # round the crop outward so the written viewBox provably contains the geometry (3 decimals)
    x0, y0, x1, y1 = pl["box"]
    x0, y0 = math.floor(x0 * 1000) / 1000.0, math.floor(y0 * 1000) / 1000.0
    x1, y1 = math.ceil(x1 * 1000) / 1000.0, math.ceil(y1 * 1000) / 1000.0
    w, h = x1 - x0, y1 - y0
    root = ET.Element(f"{{{b.SVG_NS}}}svg", {
        "width": f"{w:.2f}mm", "height": f"{h:.2f}mm",
        "viewBox": f"{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}",
    })
    g = ET.SubElement(root, f"{{{b.SVG_NS}}}g", {
        "id": "feather",
        "transform": transform_str(pl["g_new"] if straighten else pl["base"]),
        # provenance: split out of the aggregate, not generated from a photo
        "data-source": os.path.basename(DEFAULT_SRC),
    })
    for el in pl["group"]:
        local = el.tag.split("}")[-1]
        if local == "path":
            g.append(copy_element(el, new_id=pl["label"]))
        elif local == "text":
            for lb in pl["labels"]:
                if lb["el"] is not el:
                    continue
                add = {"x": f"{lb['x']:.4f}", "y": f"{lb['y']:.4f}"}
                if lb["transform"] is not None:
                    add["transform"] = transform_str(lb["transform"])
                g.append(copy_element(el, drop=("id",), add=add))
    ET.indent(root, space="  ")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(root, encoding="unicode") + "\n")


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #
def verify_files(plans, b, texts, straighten):
    """Each file must reproduce the aggregate through the same transform, come out upright at the
    same length, and keep its label level, verbatim in text and on its own feather."""
    problems, notes = [], []
    for pl in plans:
        label = pl["label"]
        root = ET.fromstring(texts[label])
        vb = [float(v) for v in root.get("viewBox").split()]
        if len(vb) != 4 or vb[2] <= 0 or vb[3] <= 0:
            problems.append(f"{label}: bad viewBox {root.get('viewBox')!r}")
            continue
        feather = root.find(f"{{{b.SVG_NS}}}g")
        if feather is None or feather.get("id") != "feather":
            problems.append(f"{label}: no <g id='feather'>")
            continue
        got = outline_points(feather, b.parse_transform(feather.get("transform")), b)
        if len(got) != len(pl["points"]):
            problems.append(f"{label}: {len(got)} points vs {len(pl['points'])} expected")
            continue
        dev = max(max(abs(a[0] - c[0]), abs(a[1] - c[1])) for a, c in zip(got, pl["points"]))
        if dev > TOL_MM:
            problems.append(f"{label}: outline differs from the aggregate by {dev:.6f} mm")

        # size kept: the straightened bounding box must be the aggregate's minimum-area box, which
        # is orientation-invariant -- so this catches any accidental rescaling
        if straighten:
            gw = bbox(got)[2] - bbox(got)[0]
            gh = bbox(got)[3] - bbox(got)[1]
            want_long, want_short = pl["want"]
            if abs(gh - want_long) > 0.05 or abs(gw - want_short) > 0.05:
                problems.append(f"{label}: straightened box {gw:.3f}x{gh:.3f} mm is not the "
                                f"aggregate's {want_short:.3f}x{want_long:.3f} mm")

        if straighten:
            # upright = the shape's tightest-fit long side is vertical (and it is the taller side)
            ang, long_side, short_side = min_area_box(got)
            off = abs(ang - 90.0)                    # the long side should run vertically
            off = min(off, 180.0 - off)
            if off > UPRIGHT_TOL_DEG:
                problems.append(f"{label}: long axis ends up {off:.2f} deg off vertical")
            if (bbox(got)[3] - bbox(got)[1]) <= (bbox(got)[2] - bbox(got)[0]):
                problems.append(f"{label}: not taller than wide after straightening")
            if narrow_end(got) != "bottom":
                notes.append(f"{label}: tip ends up at the top")

        gx0, gy0, gx1, gy1 = bbox(got)
        if (gx0 < vb[0] - TOL_MM or gy0 < vb[1] - TOL_MM
                or gx1 > vb[0] + vb[2] + TOL_MM or gy1 > vb[1] + vb[3] + TOL_MM):
            problems.append(f"{label}: outline falls outside its own viewBox")

        # labels: text verbatim, net transform level, anchored on the straightened feather
        src_text = [el for el in pl["group"] if el.tag.split("}")[-1] == "text"]
        out_text = list(feather.iter(f"{{{b.SVG_NS}}}text"))
        if len(src_text) != len(out_text):
            problems.append(f"{label}: {len(out_text)} labels written, {len(src_text)} in the "
                            f"aggregate")
            continue
        for a, c, lb in zip(src_text, out_text, pl["labels"]):
            aa = {k: v for k, v in a.attrib.items() if k not in ("id", "x", "y", "transform")}
            cc = {k: v for k, v in c.attrib.items() if k not in ("id", "x", "y", "transform")}
            if aa != cc or (a.text or "") != (c.text or ""):
                problems.append(f"{label}: label text changed ({aa} -> {cc})")
            net = mat_mul(b.parse_transform(feather.get("transform")),
                          b.parse_transform(c.get("transform")))
            if straighten and max(abs(x - y) for x, y in
                                  zip(net[:4], (-1.0, 0.0, 0.0, -1.0))) > 1e-6:
                problems.append(f"{label}: label is not level (net linear {net[:4]})")
            anchor = b.mat_apply(net, (float(c.get("x", 0)), float(c.get("y", 0))))
            if max(abs(anchor[0] - lb["anchor"][0]), abs(anchor[1] - lb["anchor"][1])) > TOL_MM:
                problems.append(f"{label}: label anchor {anchor} is not where the straightening "
                                f"puts it ({lb['anchor'][0]:.3f},{lb['anchor'][1]:.3f})")
            if not b._point_in_polygon(anchor, got):
                problems.append(f"{label}: label sits outside its own outline")
    return problems, notes


def verify_readback(plans, b, out_dir):
    """The written files must load through build-feather-aggregate.py as the same geometry."""
    problems = []
    loaded = {f.label: f for f in b.load_all(out_dir)}
    for pl in plans:
        label = pl["label"]
        if label not in loaded:
            problems.append(f"{label}: build-feather-aggregate.py cannot read it back")
            continue
        got = loaded[label].points
        if len(got) != len(pl["points"]):
            problems.append(f"{label}: read-back has {len(got)} points vs {len(pl['points'])}")
            continue
        dev = max(max(abs(a[0] - c[0]), abs(a[1] - c[1])) for a, c in zip(got, pl["points"]))
        if dev > TOL_MM:
            problems.append(f"{label}: read-back differs from the aggregate by {dev:.6f} mm")
    return problems


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=DEFAULT_SRC,
                    help=f"aggregate to split (default {DEFAULT_SRC})")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help=f"folder for the individual files (default {DEFAULT_OUT})")
    ap.add_argument("--margin-mm", type=float, default=MARGIN_MM,
                    help=f"context around each feather in the viewBox (default {MARGIN_MM})")
    ap.add_argument("--no-straighten", action="store_true",
                    help="keep the arrangement rotation: write each feather exactly as it lies in "
                         "the aggregate (lossless, but most files then open rotated)")
    ap.add_argument("--no-ancestors", action="store_true",
                    help="ignore the prefix groups' transforms, so sizes come from the feather's "
                         "own transform instead of the group arrangement")
    ap.add_argument("--check", action="store_true", help="verify only; write nothing")
    args = ap.parse_args()

    b = load_builder()
    if not os.path.exists(args.src):
        raise SystemExit(f"no aggregate at {args.src}")
    root = ET.parse(args.src).getroot()
    straighten, include_ancestors = not args.no_straighten, not args.no_ancestors

    plans = []
    for label, group, parents in find_feathers(root, b):
        base = composed_transform(group, parents, b, include_ancestors)
        plans.append(plan(label, group, base, b, args.margin_mm, straighten))
    if not plans:
        raise SystemExit(f"no feather groups found in {args.src}")

    groups = {}
    for pl in plans:
        groups.setdefault(LABEL_RE.match(pl["label"]).group(1), []).append(pl["label"])
    print(f"aggregate: {os.path.basename(args.src)} -> {len(plans)} feathers")
    print("transform: feather group "
          + ("+ every ancestor (prefix group included)" if include_ancestors else "only")
          + (", straightened upright" if straighten else ", as drawn (not straightened)"))
    for prefix in sorted(groups, key=lambda p: (p not in b.GROUP_ORDER, p)):
        labels = sorted(groups[prefix], key=lambda l: int(LABEL_RE.match(l).group(2)))
        first = next(pl for pl in plans if pl["label"] == labels[0])
        print(f"  {prefix:3s} {len(labels):2d}  {labels[0]} length "
              f"{bbox(first['points'])[3] - bbox(first['points'])[1]:7.1f} mm  "
              + " ".join(labels))

    texts = {pl["label"]: build_file(pl, b, straighten) for pl in plans}

    def write_all(directory):
        os.makedirs(directory, exist_ok=True)
        for pl in plans:
            path = os.path.join(directory, f"{pl['label']}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(texts[pl["label"]])

    if args.check:
        # full verification, including the read-back, without touching a tracked file
        tmp = os.path.join(HERE, "as-built", "scratch", "split-check")
        shutil.rmtree(tmp, ignore_errors=True)
        write_all(tmp)
        problems, notes = verify_files(plans, b, texts, straighten)
        problems += verify_readback(plans, b, tmp)
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        existing = set()
        if os.path.isdir(args.out):
            existing = {os.path.splitext(f)[0] for f in os.listdir(args.out)
                        if f.endswith(".svg")}
        changed = 0
        for pl in plans:
            path = os.path.join(args.out, f"{pl['label']}.svg")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    changed += fh.read() != texts[pl["label"]]
        write_all(args.out)
        print(f"wrote {len(plans)} files to {args.out} ({changed} changed on disk)")
        extra = sorted(existing - {pl["label"] for pl in plans})
        if extra:
            print(f"  note: {len(extra)} file(s) there are not in the aggregate and were left "
                  f"alone: {', '.join(extra)}")
        problems, notes = verify_files(plans, b, texts, straighten)
        problems += verify_readback(plans, b, args.out)

    if problems:
        print("\n! verification FAILED:")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"verification: {len(plans)} files, outline == aggregate through the same transform, "
          f"lengths kept, labels level and on their feather, builder reads them back identically")
    for n in notes:
        print("  note: " + n)
    if args.check:
        print("(--check: nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
