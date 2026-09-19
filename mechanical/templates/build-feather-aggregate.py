#!/usr/bin/env python3
"""Aggregate the per-feather SVGs in as-built/vectors/individuals/ into one catalog SVG.

Source of truth: ``as-built/vectors/individuals/<LABEL>.svg`` -- one feather per file, each
authored inside *its own photo sheet's* mm frame. Those frames are not shared (the sheets are
separate photographs), so concatenating the files would stack unrelated feathers: S1 from
``S1-6.jpg`` and SC1 from ``SC1-8_...jpg`` land in the same place. The aggregate therefore
re-places every feather, at 1:1 (user units = mm), by transforming its **group** -- the
``<path>`` inside is copied verbatim, so a feather's outline is bit-for-bit its own file's.

Layout
------
One row per prefix, in ``GROUP_ORDER``, feathers left to right in numeric order. Nesting::

    <g id="catalog">                 presentation defaults for the outlines
      <g id="P">                     one group per prefix
        <g id="P1" transform="translate(dx,dy) translate(tx,ty) scale(1,-1)">
          <path id="P1-outline" .../>    verbatim from individuals/P1.svg (d + transform)
          <text ...>P1</text>            the source's own label, with a counter-transform

No text is emitted for the document or the groups -- the only labels in the output are the ones
carried by the individual SVGs.

Flip
----
``--flip`` (default ``vertical``) mirrors each outline in its own slot, about the feather's
bounding-box centre: a mirror leaves that box unchanged, so rows and slots do not move. The
mirror goes on the group, together with the placement. The label rides the mirrored group (so it
stays on the same part of the feather) with a local counter-transform, because a group mirror
would otherwise reverse the glyphs -- the net effect on a label is a pure translation, leaving it
rendered exactly as authored.

Usage
-----
    python build-feather-aggregate.py                 # -> as-built/vectors/feathers-aggregate.svg
    python build-feather-aggregate.py --png           # + scratch raster QC raster
    python build-feather-aggregate.py --check         # verify only, write nothing

The build always self-checks: each written outline must equal its group transform applied to the
source outline (same points, to 0.01 mm), paths must be untouched, each label must keep its
glyph orientation and mirrored anchor and still lie on its own feather, no two feathers may
overlap, and no non-source label text may appear.
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN = os.path.join(HERE, "as-built", "vectors", "individuals")
DEFAULT_OUT = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
DEFAULT_SCRATCH = os.path.join(HERE, "as-built", "scratch")

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)          # default namespace -> plain <svg>, not <svg:svg>
ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# Row order: flight feathers, then coverts from largest to smallest. Any prefix not listed
# (or not matching <letters><digits>) is appended after these, alphabetically.
GROUP_ORDER = ["P", "S", "A", "PC", "SC", "MC", "LC", "B"]
GROUP_TITLE = {
    "P": "primaries",
    "S": "secondaries",
    "A": "alula",
    "PC": "primary coverts",
    "SC": "secondary coverts",
    "MC": "median coverts",
    "LC": "lesser coverts",
    "B": "body feathers",
}

LABEL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")
_NUM = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"

# catalogue layout, mm
MARGIN_MM = 25.0
GAP_X_MM = 14.0
ROW_GAP_MM = 30.0
STROKE_PAD_MM = 0.25          # half of the 0.5 stroke, so padded boxes never touch

# Flip the geometry, per feather, about its own bounding-box centre: the bbox is unchanged by
# a mirror, so the row layout and the slot of every feather stay exactly the same.
#   none       as authored (tips up: the primaries are a ~7 mm point at the top edge and
#              ~31 mm wide at the bottom)
#   vertical   mirror top<->bottom (tips down)
#   horizontal mirror left<->right
FLIP_CHOICES = ("none", "vertical", "horizontal", "both")


# --------------------------------------------------------------------------- #
# affine transforms
# --------------------------------------------------------------------------- #
IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m, n):
    """m @ n (apply n first, then m)."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def mat_apply(m, p):
    a, b, c, d, e, f = m
    x, y = p
    return (a * x + c * y + e, b * x + d * y + f)


def mat_translate(x, y):
    return (1.0, 0.0, 0.0, 1.0, x, y)


def mat_inverse(m):
    a, b, c, d, e, f = m
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError(f"singular transform {m}")
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def transform_str(m):
    """An affine matrix as an SVG transform list, short form when it is a plain translation."""
    a, b, c, d, e, f = m
    if (a, b, c, d) == (1.0, 0.0, 0.0, 1.0):
        return f"translate({e:.3f},{f:.3f})"
    return f"matrix({a:.10g},{b:.10g},{c:.10g},{d:.10g},{e:.10g},{f:.10g})"


def flip_matrix(bbox, flip):
    """Mirror about the bbox centre. Matches flip_transform_str() exactly."""
    if flip == "none":
        return IDENT
    x0, y0, x1, y1 = bbox
    m = IDENT
    if flip in ("horizontal", "both"):
        m = mat_mul(m, (-1.0, 0.0, 0.0, 1.0, x0 + x1, 0.0))
    if flip in ("vertical", "both"):
        m = mat_mul(m, (1.0, 0.0, 0.0, -1.0, 0.0, y0 + y1))
    return m


def flip_transform_str(bbox, flip):
    """The same mirror as an SVG transform list, written the way a human would."""
    if flip == "none":
        return ""
    x0, y0, x1, y1 = bbox
    sx = -1 if flip in ("horizontal", "both") else 1
    sy = -1 if flip in ("vertical", "both") else 1
    tx = (x0 + x1) if sx < 0 else 0.0
    ty = (y0 + y1) if sy < 0 else 0.0
    return f"translate({tx:.4f},{ty:.4f}) scale({sx},{sy})"


def label_counter_transform(feather, text_el, flip):
    """Transform for a label inside a mirrored feather group: cancels the group's mirror and
    slides the label back onto the same part of the feather.

    A label must not be mirrored (the glyphs would reverse), so the net effect has to be a pure
    translation: with the group carrying the mirror F, a local L gives net = F o L o M. Setting
    L = F o Q (Q = the translation that moves the anchor to its mirrored spot) leaves
    net = Q o M -- the source rendering, relocated, glyphs exactly as authored. F o Q is still a
    mirror (mirror o translation = mirror), so L is `translate(2*anchor) scale(flip)`.
    """
    if flip == "none":
        return ""
    x = float(text_el.get("x", 0.0))
    y = float(text_el.get("y", 0.0))
    ax, ay = mat_apply(parse_transform(text_el.get("transform")), (x, y))
    sx = -1 if flip in ("horizontal", "both") else 1
    sy = -1 if flip in ("vertical", "both") else 1
    ex = 2.0 * ax if flip in ("horizontal", "both") else 0.0
    ey = 2.0 * ay if flip in ("vertical", "both") else 0.0
    return f"translate({ex:.4f},{ey:.4f}) scale({sx},{sy})"


def parse_transform(text):
    """SVG transform list -> affine matrix. Handles translate/scale/rotate/matrix/skew."""
    m = IDENT
    for name, args in re.findall(r"([A-Za-z]+)\s*\(([^)]*)\)", text or ""):
        v = [float(t) for t in re.findall(_NUM, args)]
        n = name.strip().lower()
        if n == "matrix" and len(v) == 6:
            local = tuple(v)
        elif n == "translate" and len(v) >= 1:
            local = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
        elif n == "scale" and len(v) >= 1:
            local = (v[0], 0.0, 0.0, v[1] if len(v) > 1 else v[0], 0.0, 0.0)
        elif n == "rotate" and len(v) >= 1:
            a = math.radians(v[0])
            ca, sa = math.cos(a), math.sin(a)
            r = (ca, sa, -sa, ca, 0.0, 0.0)
            if len(v) >= 3:
                cx, cy = v[1], v[2]
                local = mat_mul(mat_mul((1.0, 0.0, 0.0, 1.0, cx, cy), r),
                                (1.0, 0.0, 0.0, 1.0, -cx, -cy))
            else:
                local = r
        elif n == "skewx" and len(v) >= 1:
            local = (1.0, 0.0, math.tan(math.radians(v[0])), 1.0, 0.0, 0.0)
        elif n == "skewy" and len(v) >= 1:
            local = (1.0, math.tan(math.radians(v[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            print(f"  ! ignoring unsupported transform {name}({args})", file=sys.stderr)
            continue
        m = mat_mul(m, local)
    return m


# --------------------------------------------------------------------------- #
# path geometry (sampled, so Bezier extents are tight rather than control-point hulls)
# --------------------------------------------------------------------------- #
def _cubic(pts, p0, p1, p2, p3, n):
    for k in range(1, n + 1):
        t = k / n
        mt = 1.0 - t
        pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                    mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))


def _quad(pts, p0, p1, p2, n):
    for k in range(1, n + 1):
        t = k / n
        mt = 1.0 - t
        pts.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                    mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))


def _arc(pts, p0, rx, ry, phi_deg, large_arc, sweep, p1, n):
    """Endpoint -> centre parameterisation (SVG spec F.6.5), sampled."""
    if rx == 0 or ry == 0 or p0 == p1:
        pts.append(p1)
        return
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large_arc == sweep:
        co = -co
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (p0[0] + p1[0]) / 2.0
    cy = sp * cxp + cp * cyp + (p0[1] + p1[1]) / 2.0

    def angle(ux, uy, vx, vy):
        d = math.hypot(ux, uy) * math.hypot(vx, vy)
        if d == 0:
            return 0.0
        a = math.acos(max(-1.0, min(1.0, (ux * vx + uy * vy) / d)))
        return -a if ux * vy - uy * vx < 0 else a

    th1 = angle(1.0, 0.0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    for k in range(1, n + 1):
        th = th1 + dth * k / n
        pts.append((cx + rx * math.cos(th) * cp - ry * math.sin(th) * sp,
                    cy + rx * math.cos(th) * sp + ry * math.sin(th) * cp))


def path_subpaths(d, samples=32):
    """Subpaths of path data `d` as lists of sampled points, in pre-transform user units."""
    toks = re.findall(r"[MmZzLlHhVvCcSsQqTtAa]|" + _NUM, d or "")
    subs = []
    pts = []
    cur = (0.0, 0.0)
    sub = (0.0, 0.0)
    ctrl = None
    cmd = None
    i = 0

    def num(n):
        nonlocal i
        vals = toks[i:i + n]
        if len(vals) < n:
            raise ValueError("truncated path data")
        i += n
        return [float(v) for v in vals]

    while i < len(toks):
        tok = toks[i]
        if len(tok) == 1 and tok.isalpha():
            cmd = tok
            i += 1
            if cmd in "Zz":
                pts.append(sub)
                cur, ctrl, cmd = sub, None, None
                continue
        elif cmd is None:
            raise ValueError(f"unexpected {tok!r} before any command")
        if cmd is None:
            raise ValueError("unexpected path data after close")

        rel = cmd.islower()
        c = cmd.upper()

        def abspt(x, y):
            return (cur[0] + x, cur[1] + y) if rel else (x, y)

        if c == "M":
            x, y = num(2)
            cur = abspt(x, y)
            sub = cur
            if pts:
                subs.append(pts)
            pts = [cur]
            ctrl = None
            cmd = "l" if rel else "L"          # implicit lineto for the following pairs
        elif c == "L":
            x, y = num(2)
            cur = abspt(x, y)
            pts.append(cur)
            ctrl = None
        elif c == "H":
            (x,) = num(1)
            cur = (cur[0] + x, cur[1]) if rel else (x, cur[1])
            pts.append(cur)
            ctrl = None
        elif c == "V":
            (y,) = num(1)
            cur = (cur[0], cur[1] + y) if rel else (cur[0], y)
            pts.append(cur)
            ctrl = None
        elif c == "C":
            x1, y1, x2, y2, x, y = num(6)
            p1, p2, p3 = abspt(x1, y1), abspt(x2, y2), abspt(x, y)
            _cubic(pts, cur, p1, p2, p3, samples)
            cur, ctrl = p3, p2
        elif c == "S":
            x2, y2, x, y = num(4)
            p1 = (2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if ctrl else cur
            p2, p3 = abspt(x2, y2), abspt(x, y)
            _cubic(pts, cur, p1, p2, p3, samples)
            cur, ctrl = p3, p2
        elif c == "Q":
            x1, y1, x, y = num(4)
            p1, p2 = abspt(x1, y1), abspt(x, y)
            _quad(pts, cur, p1, p2, samples)
            cur, ctrl = p2, p1
        elif c == "T":
            x, y = num(2)
            p1 = (2 * cur[0] - ctrl[0], 2 * cur[1] - ctrl[1]) if ctrl else cur
            p2 = abspt(x, y)
            _quad(pts, cur, p1, p2, samples)
            cur, ctrl = p2, p1
        elif c == "A":
            rx, ry, phi, laf, sf, x, y = num(7)
            p1 = abspt(x, y)
            _arc(pts, cur, rx, ry, phi, int(laf), int(sf), p1, samples)
            cur, ctrl = p1, None
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    if pts:
        subs.append(pts)
    return subs


def path_points(d, samples=32):
    """Every sampled point of path data `d`, flattened across subpaths."""
    return [p for sub in path_subpaths(d, samples) for p in sub]


# --------------------------------------------------------------------------- #
# reading one individual
# --------------------------------------------------------------------------- #
class Feather:
    __slots__ = ("label", "prefix", "index", "source", "els", "bbox", "points", "own")

    def __init__(self, label, prefix, index, source, els, bbox, points, own):
        self.label = label
        self.prefix = prefix
        self.index = index
        self.source = source
        self.els = els          # [(element, ctm)] in document order
        self.bbox = bbox        # (x0, y0, x1, y1) of the outline, transformed, user units
        self.points = points    # outline points in the file's own frame, for verification
        self.own = own          # the feather group's own transform (IDENT for plain files)

    @property
    def size(self):
        return (self.bbox[2] - self.bbox[0], self.bbox[3] - self.bbox[1])


def _local(el):
    return el.tag.split("}")[-1]


def collect_geometry(root):
    """([(element, ctm)], group_ctm) for path/text outside <defs>, ancestors' transforms included.

    `group_ctm` is the accumulated transform of the group the elements sit in -- the feather's own
    frame. Individual files written by split-feather-aggregate.py carry a real transform there
    (straightening, mirror, group scale), so the builder has to put it back on the group it writes,
    or the outline it draws would not be the one in the file.
    """
    parent, ctm = {}, {}
    order = []

    def walk(el, m):
        m = mat_mul(m, parse_transform(el.get("transform")))
        ctm[id(el)] = m
        order.append(el)
        for ch in el:
            parent[id(ch)] = el
            walk(ch, m)

    walk(root, IDENT)

    def in_defs(el):
        while id(el) in parent:
            el = parent[id(el)]
            if _local(el) == "defs":
                return True
        return False

    group = None
    for el in order:
        if _local(el) == "g" and el.get("id") in ("feather", "outlines"):
            group = el
            break
    if group is not None:
        return ([(el, ctm[id(el)]) for el in group if _local(el) in ("path", "text")],
                ctm[id(group)])
    return ([(el, ctm[id(el)]) for el in order
             if _local(el) in ("path", "text") and not in_defs(el)], IDENT)


def bbox_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def load_individual(path):
    """One individuals/<LABEL>.svg -> Feather (outline bbox in absolute sheet mm)."""
    label = os.path.splitext(os.path.basename(path))[0]
    m = LABEL_RE.match(label)
    if not m:
        raise ValueError(f"{label}: not <prefix><digits>")
    root = ET.parse(path).getroot()
    els, own = collect_geometry(root)
    if not els:
        raise ValueError(f"{label}: no path/text geometry found")
    pts = []
    for el, ctm in els:
        if _local(el) != "path":
            continue
        pts.extend(mat_apply(ctm, p) for p in path_points(el.get("d")))
    if not pts:
        raise ValueError(f"{label}: no <path> found")
    return Feather(label, m.group(1).upper(), int(m.group(2)), path, els,
                   bbox_of(pts), pts, own)


def load_all(in_dir):
    paths = sorted(glob.glob(os.path.join(in_dir, "*.svg")))
    if not paths:
        raise SystemExit(f"no SVGs in {in_dir}")
    return [load_individual(p) for p in paths]


# --------------------------------------------------------------------------- #
# layout + write
# --------------------------------------------------------------------------- #
def order_groups(feathers):
    groups = {}
    for f in feathers:
        groups.setdefault(f.prefix, []).append(f)
    known = [p for p in GROUP_ORDER if p in groups]
    extra = sorted(p for p in groups if p not in GROUP_ORDER)
    return [(p, sorted(groups[p], key=lambda f: (f.index, f.label))) for p in known + extra]


def layout(feathers, gap_x=GAP_X_MM, row_gap=ROW_GAP_MM, margin=MARGIN_MM, align="base"):
    """Assign every feather a translate that drops it into its row slot. Returns (rows, W, H).

    `align` is which edge the row lines up on. The default `base` aligns the *bottom* edges:
    measured 3 mm inside each end, the primaries are a sharp point at the top (P1 6.8 mm) and
    broad at the bottom (30.6 mm), i.e. tip up / vane base at the bottom, so bottom-aligned
    rows put the bases on one line and fan the tips, the way a feather set is normally shown.
    `top` (tips flush, bases ragged) and `center` are the alternatives.
    """
    rows = []
    y = margin
    for prefix, group in order_groups(feathers):
        top = y
        height = max(f.size[1] for f in group)
        x = margin
        placed = []
        for f in group:
            dx = x - f.bbox[0]
            if align == "top":
                dy = top - f.bbox[1]
            elif align == "center":
                dy = top + 0.5 * (height - f.size[1]) - f.bbox[1]
            else:                             # base: bottom edges flush
                dy = top + (height - f.size[1]) - f.bbox[1]
            placed.append((f, dx, dy))
            x += f.size[0] + gap_x
        rows.append({"prefix": prefix, "top": top,
                     "width": x - gap_x - margin, "height": height, "placed": placed})
        y = top + height + row_gap
    width = margin * 2 + max(r["width"] for r in rows)
    height = y - row_gap + margin
    return rows, width, height


def _copy_element(el, new_id=None, tag=None, extra=None):
    tag = tag or _local(el)
    out = ET.Element(f"{{{SVG_NS}}}{tag}", dict(el.attrib))
    if new_id is not None:
        out.set("id", new_id)
    elif "id" in out.attrib:
        del out.attrib["id"]
    for k, v in (extra or {}).items():
        out.set(k, v)
    out.text = el.text
    return out


def build(feathers, out_path, flip="none", align="base"):
    """Write the catalog. Only the source SVGs' own labels are emitted -- no document title
    and no per-group heading text.

    `flip` mirrors each feather (see FLIP_CHOICES) in its own slot. It is applied to the
    feather's `<g>`, together with its placement, so the `<path>` inside is copied verbatim --
    and the label gets a counter-transform, because a group mirror would otherwise reverse the
    glyphs.
    """
    rows, width, height = layout(feathers, align=align)

    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": f"{width:.2f}mm",
        "height": f"{height:.2f}mm",
        "viewBox": f"0 0 {width:.3f} {height:.3f}",
    })
    total = sum(len(r["placed"]) for r in rows)
    ET.SubElement(root, f"{{{SVG_NS}}}title").text = (
        f"As-built feather templates - {total} feathers, 1:1 mm"
        + (f", {flip} flip" if flip != "none" else ""))
    ET.SubElement(root, f"{{{SVG_NS}}}desc").text = (
        f"Aggregate of as-built/vectors/individuals/*.svg, one group per feather prefix. "
        f"Each outline is copied verbatim from its individual file and only translated"
        + (f" and mirrored ({flip}) about its own centre" if flip != "none" else "")
        + f", so it stays 1:1 (user units = mm) and keeps its label.")

    catalog = ET.SubElement(root, f"{{{SVG_NS}}}g",
                            {"id": "catalog", "fill": "none", "stroke": "#000",
                             "stroke-width": "0.5"})

    counts = {}
    for row in rows:
        prefix = row["prefix"]
        g = ET.SubElement(catalog, f"{{{SVG_NS}}}g",
                          {"id": prefix,
                           "data-title": GROUP_TITLE.get(prefix, ""),
                           "data-count": str(len(row["placed"]))})
        for f, dx, dy in row["placed"]:
            counts[prefix] = counts.get(prefix, 0) + 1
            # placement, the optional mirror, and the source file's own group transform -- the
            # split files carry a real one (straightening, mirror, group scale); a plain generated
            # file has IDENT there
            group_ctm = mat_mul(mat_mul(mat_translate(dx, dy), flip_matrix(f.bbox, flip)), f.own)
            fg = ET.SubElement(g, f"{{{SVG_NS}}}g", {
                "id": f.label,
                # all of it lives on the group, so the path below stays untouched
                "transform": transform_str(group_ctm),
                "data-source": f"individuals/{os.path.basename(f.source)}",
            })
            for el, _ in f.els:
                local = _local(el)
                if local == "path":
                    extra = {"id": f"{f.label}-outline"}
                    if "fill" not in el.attrib:
                        extra.update({"fill": "none", "stroke": "#000", "stroke-width": "0.5"})
                    fg.append(_copy_element(el, extra=extra))
                elif local == "text":
                    extra = {}
                    if "fill" not in el.attrib:
                        extra["fill"] = "#000"
                    if "font-family" not in el.attrib:
                        extra["font-family"] = "sans-serif"
                    counter = label_counter_transform(f, el, flip)
                    if counter:
                        orig = el.get("transform")
                        extra["transform"] = f"{counter} {orig}".strip() if orig else counter
                    fg.append(_copy_element(el, extra=extra))

    ET.indent(root, space="  ")
    text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(root, encoding="unicode") + "\n")
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return text, rows, width, height, counts


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #
def _point_in_polygon(pt, poly):
    """Ray casting; poly is a closed list of points."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def verify(source_feathers, text, flip="none", tol=0.01):
    """Re-parse what we wrote and check it against the source files.

    Strongest form of the check available: for every feather the written outline must equal the
    source outline put through exactly `translate + mirror` -- not merely the same size, the
    same points. Also: only the source SVGs' own labels are present, they are byte-identical in
    attributes, and no two feathers overlap.
    """
    problems, notes = [], []
    root = ET.fromstring(text)
    if root.get("width") is None or not root.get("viewBox"):
        problems.append("aggregate root has no width/viewBox")

    by_label = {f.label: f for f in source_feathers}
    catalog = root.find(f"{{{SVG_NS}}}g")
    seen, labels_seen = {}, []
    sx = -1 if flip in ("horizontal", "both") else 1
    sy = -1 if flip in ("vertical", "both") else 1
    for g in (catalog.iter(f"{{{SVG_NS}}}g") if catalog is not None else []):
        label = g.get("id") or ""
        if label not in by_label:
            continue
        src = by_label[label]
        ctm = parse_transform(g.get("transform"))
        if ctm == IDENT:
            problems.append(f"{label}: feather group has no placement transform")
        # the group must be exactly translate + (optional mirror) + the source's own transform
        rel = mat_mul(ctm, mat_inverse(src.own))
        if abs(rel[1]) > 1e-9 or abs(rel[2]) > 1e-9:
            problems.append(f"{label}: group transform is not translate+mirror+own ({ctm})")
        if (round(rel[0]), round(rel[3])) != (sx, sy):
            problems.append(f"{label}: group mirror is ({rel[0]:g},{rel[3]:g}), expected "
                            f"({sx},{sy}) for flip={flip}")

        # the group must be the *only* thing moving the outline: the path inside is verbatim, so
        # the written points must equal the group transform applied to the source points
        src_paths = [el for el, _ in src.els if _local(el) == "path"]
        out_paths = list(g.iter(f"{{{SVG_NS}}}path"))
        if not out_paths:
            problems.append(f"{label}: aggregate group has no path")
            continue
        if len(out_paths) != len(src_paths):
            problems.append(f"{label}: {len(out_paths)} paths written, {len(src_paths)} in the "
                            f"source")
        for a, b in zip(src_paths, out_paths):
            if a.get("transform") != b.get("transform"):
                problems.append(f"{label}: path transform was rewritten "
                                f"({a.get('transform')!r} -> {b.get('transform')!r})")
            if a.get("d") != b.get("d"):
                problems.append(f"{label}: path data was rewritten")
        out_final = []
        for p in out_paths:
            ptm = mat_mul(ctm, parse_transform(p.get("transform")))
            out_final.extend(mat_apply(ptm, q) for q in path_points(p.get("d")))
        # src.points are already in the source file's own frame, so the expectation is the placed
        # geometry (rel = translate + mirror) applied to them, not the full group transform
        want = [mat_apply(rel, q) for q in src.points]
        if len(out_final) != len(want):
            problems.append(f"{label}: {len(out_final)} points written vs {len(want)} in the "
                            f"source")
        else:
            dev = max(math.hypot(a[0] - b[0], a[1] - b[1])
                      for a, b in zip(out_final, want))
            if dev > tol:
                problems.append(f"{label}: outline differs from group-transform(source) by "
                                f"{dev:.3f} mm")

        # labels: same text and same glyph orientation as the source, anchor mirrored with the
        # outline so the label stays on its own feather
        src_text = [el for el, _ in src.els if _local(el) == "text"]
        out_text = list(g.iter(f"{{{SVG_NS}}}text"))
        if len(out_text) != len(src_text):
            problems.append(f"{label}: {len(out_text)} labels written, {len(src_text)} in the "
                            f"source")
        for a, b in zip(src_text, out_text):
            # the source's own id (Inkscape's "feather-label", repeated across files) is stripped:
            # keeping it would put 42 duplicate ids in one document
            a_att = {k: v for k, v in a.attrib.items() if k not in ("id", "transform")}
            b_att = {k: v for k, v in b.attrib.items() if k not in ("id", "transform")}
            if a_att != b_att or (a.text or "") != (b.text or ""):
                problems.append(f"{label}: label changed ({a_att} -> {b_att})")
                continue
            labels_seen.append((b.text or "").strip())
            # net transform on a label = the source file's own transform o the label's own; the
            # output's net must keep the source's linear part (glyphs exactly as authored) and put
            # the anchor where the placement (rel) takes it
            tm_src = mat_mul(src.own, parse_transform(a.get("transform")))
            tm_out = mat_mul(ctm, parse_transform(b.get("transform")))
            if max(abs(x - y) for x, y in zip(tm_src[:4], tm_out[:4])) > 1e-6:
                problems.append(f"{label}: label orientation/mirroring changed "
                                f"({tm_src[:4]} -> {tm_out[:4]})")
            xy = (float(b.get("x", 0)), float(b.get("y", 0)))
            got_anchor = mat_apply(tm_out, xy)
            # the label rides the placed group (so it stays on the same part of the feather);
            # a counter-transform only fixes the glyphs, leaving the anchor where placement puts it
            want_anchor = mat_apply(rel, mat_apply(tm_src, xy))
            if math.hypot(got_anchor[0] - want_anchor[0],
                          got_anchor[1] - want_anchor[1]) > 0.01:
                problems.append(f"{label}: label anchor {got_anchor} is not the mirrored "
                                f"{want_anchor}")
            if not _point_in_polygon(got_anchor, out_final):
                problems.append(f"{label}: label sits outside its own outline")
        box = bbox_of(out_final)
        got = (box[2] - box[0], box[3] - box[1])
        if abs(got[0] - src.size[0]) > 0.02 or abs(got[1] - src.size[1]) > 0.02:
            problems.append(f"{label}: bbox size changed {src.size[0]:.2f}x{src.size[1]:.2f} -> "
                            f"{got[0]:.2f}x{got[1]:.2f} mm")
        seen[label] = box

    missing = sorted(set(by_label) - set(seen))
    if missing:
        problems.append("missing from aggregate: " + ", ".join(missing))

    # nothing but the source labels: no document title, no group heading text
    stray = []
    if catalog is not None:
        for g in catalog.iter(f"{{{SVG_NS}}}g"):
            label = g.get("id") or ""
            if label in by_label:
                continue
            for t in g:
                if _local(t) == "text":
                    stray.append((g.get("id"), (t.text or "").strip()))
    if stray:
        problems.append("non-source label text emitted: "
                        + ", ".join(f"{gid}: {txt!r}" for gid, txt in stray))
    if labels_seen and len(labels_seen) != len(by_label):
        problems.append(f"only {len(labels_seen)} source labels present, expected {len(by_label)}")

    items = sorted(seen.items())
    for i, (la, a) in enumerate(items):
        for lb, b in items[i + 1:]:
            if (a[0] - STROKE_PAD_MM < b[2] + STROKE_PAD_MM
                    and b[0] - STROKE_PAD_MM < a[2] + STROKE_PAD_MM
                    and a[1] - STROKE_PAD_MM < b[3] + STROKE_PAD_MM
                    and b[1] - STROKE_PAD_MM < a[3] + STROKE_PAD_MM):
                problems.append(f"overlap: {la} and {lb}")
    return problems, seen, notes


def rasterise_svg(svg_path, png_path, scale=0.7, pad=4):
    """Self-contained QC raster: re-read the written SVG and draw its paths with PIL.

    cairosvg needs a system libcairo that may not exist here, so this fallback keeps --png
    usable. It reads the *output file*, not the in-memory model, so it still checks what was
    actually written (transforms included).
    """
    from PIL import Image, ImageDraw
    root = ET.parse(svg_path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    width = max(1, int(vb[2] * scale)) + 2 * pad
    height = max(1, int(vb[3] * scale)) + 2 * pad
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    n = 0

    def walk(el, m):
        nonlocal n
        m = mat_mul(m, parse_transform(el.get("transform")))
        tag = _local(el)
        if tag == "path":
            for sub in path_subpaths(el.get("d"), samples=16):
                draw.line([(pad + p[0] * scale, pad + p[1] * scale)
                           for p in (mat_apply(m, q) for q in sub)],
                          fill="black", width=1)
                n += 1
        elif tag == "text":
            # glyphs need a real renderer; for QC mark where the label anchor lands
            a = mat_apply(m, (float(el.get("x", 0)), float(el.get("y", 0))))
            cx, cy = pad + a[0] * scale, pad + a[1] * scale
            r = 2
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="red")
        for ch in el:
            walk(ch, m)

    walk(root, IDENT)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    img.save(png_path)
    return n


def write_png(svg_path, png_path, scale=0.7):
    """Rasterise via cairosvg when it works, else the built-in PIL fallback."""
    try:
        import cairosvg
    except (ImportError, OSError) as exc:
        print(f"  ! cairosvg unavailable ({exc.__class__.__name__}); "
              f"using the built-in renderer", file=sys.stderr)
    else:
        try:
            cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale,
                             background_color="white")
            return png_path, "cairosvg"
        except OSError as exc:
            print(f"  ! cairosvg failed ({exc.__class__.__name__}); "
                  f"using the built-in renderer", file=sys.stderr)
    rasterise_svg(svg_path, png_path, scale=scale)
    return png_path, "built-in PIL renderer"


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="in_dir", default=DEFAULT_IN,
                    help=f"folder of individual feather SVGs (default {DEFAULT_IN})")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help=f"aggregate SVG to write (default {DEFAULT_OUT})")
    ap.add_argument("--png", action="store_true",
                    help="also rasterise to as-built/scratch/<out-stem>.png for visual QC")
    ap.add_argument("--png-scale", type=float, default=0.7,
                    help="raster scale for --png (default 0.7 = 70%% of 1:1)")
    ap.add_argument("--check", action="store_true", help="verify only; write nothing")
    ap.add_argument("--align", choices=("base", "top", "center"), default="base",
                    help="row alignment: which feather edge lines up (default base = the "
                         "vane bases on one line, tips fanning out)")
    ap.add_argument("--flip", choices=FLIP_CHOICES, default="none",
                    help="mirror each outline in its own slot (default none: the individual files "
                         "already carry the orientation they were split out with); labels are "
                         "never mirrored, they stay verbatim from the source SVGs")
    args = ap.parse_args()

    feathers = load_all(args.in_dir)
    if args.flip != "none":
        odd = sorted(f.label for f in feathers if f.own != IDENT)
        if odd:
            raise SystemExit(
                f"--flip {args.flip} cannot be combined with files that carry their own group "
                f"transform ({len(odd)} of {len(feathers)}, e.g. {', '.join(odd[:4])}).\n"
                f"Those files already encode their orientation (see split-feather-aggregate.py); "
                f"re-split with --no-straighten to regenerate plain ones, or use --flip none.")
    print(f"individuals: {len(feathers)} feathers from {args.in_dir}")
    for prefix, group in order_groups(feathers):
        print(f"  {prefix:3s} {GROUP_TITLE.get(prefix, ''):18s} "
              f"{len(group):2d}  " + " ".join(f.label for f in group))

    rows, width, height = layout(feathers, align=args.align)
    print(f"layout: {len(rows)} rows, canvas {width:.1f} x {height:.1f} mm, "
          f"{args.align}-aligned, flip={args.flip}")
    for r in rows:
        print(f"  {r['prefix']:3s} {len(r['placed']):2d} feathers, "
              f"{r['width']:.1f} x {r['height']:.1f} mm")

    if args.check:
        text, rows, width, height, counts = build(feathers, None, flip=args.flip,
                                                  align=args.align)
    else:
        text, rows, width, height, counts = build(feathers, args.out, flip=args.flip,
                                                  align=args.align)

    problems, seen, notes = verify(feathers, text, flip=args.flip)
    if problems:
        print("\n! verification FAILED:")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"verification: {len(seen)} feathers, outline == source "
          f"({args.flip} flip, translate only) to within 0.01 mm, "
          f"source labels only, no overlaps")
    for n in notes:
        print("  note: " + n)

    if args.check:
        print("(--check: nothing written)")
        return 0

    size_kb = os.path.getsize(args.out) / 1024.0
    print(f"wrote {args.out}  ({size_kb:.1f} KB)")
    if args.png:
        png = os.path.join(DEFAULT_SCRATCH,
                           os.path.splitext(os.path.basename(args.out))[0] + ".png")
        path, how = write_png(args.out, png, args.png_scale)
        print(f"wrote {path}  (scale {args.png_scale}, {how})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
