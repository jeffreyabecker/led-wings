#!/usr/bin/env python3
"""
prepare_source.py -- one-time correction of feathers-aggregate.svg.

Three things, all "correct at source" so the file is placement-ready and the
spec can copy geometry verbatim:

1. Feathers: rewrite each <path> so its `d` is origin-framed, compensate the
   parent group transform so the Inkscape view is unchanged, delete data-wh/
   data-vb. B family stays horizontal (rotation is declared in layout.yaml).
2. outline-toplines -> assembly-template: drop the toplines' data-wh/data-vb,
   re-origin the whole group (wrap children in a translate + compensate the
   group transform).
3. X-align groups: same re-origin (wrap + compensate).
"""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

AGG = Path(__file__).resolve().parent / "templates" / "feathers-aggregate.svg"
NS = "{http://www.w3.org/2000/svg}"

_NUMBER = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")
_PATH_NUMS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}
_IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def fmt(x):
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", "-0."):
        return "0"
    return s


def _mul(A, B):
    a1, b1, c1, d1, e1, f1 = A
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _ops(tstr):
    out = []
    for kind, args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", tstr or ""):
        vals = [float(v) for v in re.split(r"[\s,]+", args.strip()) if v]
        if kind == "matrix":
            out.append(("matrix", vals))
        elif kind == "translate":
            out.append(("translate", vals + [0.0] * (2 - len(vals))))
        elif kind == "scale":
            out.append(("scale", vals + vals[:1] * (2 - len(vals))))
        elif kind == "rotate":
            cx, cy = (vals[1], vals[2]) if len(vals) >= 3 else (0.0, 0.0)
            a = math.radians(vals[0])
            cos, sin = math.cos(a), math.sin(a)
            out.append(("matrix", [cos, sin, -sin, cos,
                                   cx - cos * cx + sin * cy,
                                   cy - sin * cx - cos * cy]))
        elif kind == "skewX":
            out.append(("matrix", [1.0, 0.0, math.tan(math.radians(vals[0])), 1.0, 0.0, 0.0]))
        elif kind == "skewY":
            out.append(("matrix", [1.0, math.tan(math.radians(vals[0])), 0.0, 1.0, 0.0, 0.0]))
        else:
            raise AssertionError(f"unsupported transform {kind!r}")
    return out


def transform_matrix(*tstrs):
    m = _IDENT
    for tstr in tstrs:
        for kind, vals in _ops(tstr):
            if kind == "matrix":
                m = _mul(m, tuple(vals))
            elif kind == "translate":
                m = _mul(m, (1.0, 0.0, 0.0, 1.0, vals[0], vals[1]))
            elif kind == "scale":
                m = _mul(m, (vals[0], 0.0, 0.0, vals[1], 0.0, 0.0))
    return m


def _apply_matrix(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def _path_points(d):
    toks = _NUMBER.findall(d or "")
    i, n = 0, len(toks)
    letter, x, y = None, 0.0, 0.0
    start = (0.0, 0.0)
    pts = []

    def take(k):
        nonlocal i
        v = [float(t) for t in toks[i:i + k]]
        i += k
        return v

    while i < n:
        if toks[i].isalpha():
            letter = toks[i]
            i += 1
            if letter in "zZ":
                x, y = start
                continue
        elif letter is None:
            break
        c = letter.lower()
        rel = letter.islower()
        k = _PATH_NUMS[c]
        if k == 0:
            continue
        v = take(k)
        if c == "h":
            x = x + v[0] if rel else v[0]
            pts.append((x, y))
        elif c == "v":
            y = y + v[0] if rel else v[0]
            pts.append((x, y))
        elif c == "a":
            ex, ey = v[5], v[6]
            x, y = (x + ex, y + ey) if rel else (ex, ey)
            pts.append((x, y))
        else:
            pairs = [(v[j], v[j + 1]) for j in range(0, len(v), 2)]
            if rel:
                pairs = [(x + px, y + py) for (px, py) in pairs]
            pts.extend(pairs)
            x, y = pairs[-1]
            if c == "m":
                start = (x, y)
        if c in "ml":
            letter = "l" if rel else "L"
    return pts


def translate_path(d, dx, dy):
    """Translate every absolute coordinate of a path `d` by (dx, dy)."""
    toks = _NUMBER.findall(d or "")
    out = []
    i, n = 0, len(toks)
    letter = None
    first = True
    while i < n:
        if toks[i].isalpha():
            letter = toks[i]
            out.append(letter)
            i += 1
            if letter in "zZ":
                continue
        elif letter is None:
            out.append(toks[i])
            i += 1
            continue
        c = letter.lower()
        k = _PATH_NUMS[c]
        if k == 0:
            continue
        args = toks[i:i + k]
        i += k
        vals = [float(a) for a in args]
        if letter.isupper():
            if c == "h":
                vals[0] += dx
            elif c == "v":
                vals[0] += dy
            elif c == "a":
                vals[5] += dx
                vals[6] += dy
            elif c in "mlcqst":
                for j in range(0, len(vals), 2):
                    vals[j] += dx
                    vals[j + 1] += dy
        elif first and c == "m":
            vals[0] += dx
            vals[1] += dy
        out.extend(fmt(v) for v in vals)
        first = False
        if c == "m":
            letter = "l" if letter.islower() else "L"
    return " ".join(out)


def ink_bbox(group):
    """Ink bbox of a group's descendants in the group's local frame."""
    pts = []

    def walk(el, matrix):
        m = _mul(matrix, transform_matrix(el.get("transform") or ""))
        if el.tag == f"{NS}path":
            for x, y in _path_points(el.get("d")):
                pts.append(_apply_matrix(m, x, y))
        elif el.tag == f"{NS}circle":
            cx, cy, r = float(el.get("cx")), float(el.get("cy")), float(el.get("r"))
            for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r)):
                pts.append(_apply_matrix(m, cx + dx, cy + dy))
        for child in el:
            walk(child, m)

    for child in group:
        walk(child, _IDENT)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def re_origin(group):
    """Wrap a group's children so their ink sits at the group's local origin,
    and compensate the group's own transform to keep the view unchanged."""
    box = ink_bbox(group)
    if box is None:
        return
    bx0, by0 = box[0], box[1]
    wrapper = ET.Element(f"{NS}g")
    wrapper.set("transform", f"translate({fmt(-bx0)} {fmt(-by0)})")
    for child in list(group):
        group.remove(child)
        wrapper.append(child)
    group.append(wrapper)
    old = group.get("transform") or ""
    group.set("transform", f"{old} translate({fmt(bx0)} {fmt(by0)})".strip())


def strip_markers(root):
    """Remove the origin-digit marker machinery: <marker> defs and the CSS that
    references them. The align overlays then render as silhouettes + plain arrow
    lines."""
    for defs in root.iter():
        if defs.tag == f"{NS}defs":
            for m in list(defs):
                if m.tag == f"{NS}marker":
                    defs.remove(m)
            break
    for style in root.iter():
        if style.tag == f"{NS}style":
            text = style.text or ""
            text = re.sub(r"\.arrow\s*\{\s*marker-start:\s*url\(#diamond\);\s*\}", "", text)
            text = re.sub(r"\.numeral\s*\{[^}]*\}", "", text)
            text = re.sub(r"\.num\d\s*\{\s*marker-start:\s*url\(#num\d\);\s*\}", "", text)
            text = re.sub(r"#num\d(?:,\s*#num\d)*\s*\{\s*overflow:\s*visible;\s*\}", "", text)
            text = re.sub(r"#diamond\s*\{[^}]*\}", "", text)
            text = re.sub(r"#diamond\s+path\s*\{[^}]*\}", "", text)
            style.text = text
            break


def main():
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")

    root = ET.parse(AGG).getroot()

    # 1. Feathers: correct path data + compensate + drop frame metadata.
    n_feathers = 0
    for g in root.iter():
        if g.tag != f"{NS}g" or g.get("class") != "feather":
            continue
        name = g.get("id")
        vb = (g.get("data-vb") or "").split()
        assert len(vb) == 4, f"{name}: feather group needs data-vb"
        x0, y0 = float(vb[0]), float(vb[1])
        path = g.find(f"./{NS}path")
        path.set("d", translate_path(path.get("d"), -x0, -y0))
        old = g.get("transform") or ""
        g.set("transform", f"{old} translate({fmt(x0)} {fmt(y0)})".strip())
        for attr in ("data-wh", "data-vb"):
            if attr in g.attrib:
                del g.attrib[attr]
        n_feathers += 1

    # 2. toplines: drop frame metadata (geometry re-origined at the group level).
    n_toplines = 0
    for g in root.iter():
        if g.tag == f"{NS}g" and g.get("class") == "topline":
            for attr in ("data-wh", "data-vb"):
                if attr in g.attrib:
                    del g.attrib[attr]
            n_toplines += 1

    # 3. rename + re-origin outline-toplines -> assembly-template.
    assembly = None
    for g in root.iter():
        if g.tag == f"{NS}g" and g.get("id") == "outline-toplines":
            g.set("id", "assembly-template")
            re_origin(g)
            assembly = "assembly-template"
            break

    # 4. re-origin each align group.
    n_aligns = 0
    for g in root.iter():
        if g.tag == f"{NS}g" and g.get("class") == "align" and g.get("id") and g.get("id").endswith("-align"):
            re_origin(g)
            n_aligns += 1

    # 5. strip the origin-digit marker machinery.
    strip_markers(root)

    xml = ET.tostring(root, encoding="unicode")
    AGG.write_text('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + xml + "\n",
                   encoding="utf-8")
    print(f"corrected {n_feathers} feathers, {n_toplines} toplines, "
          f"{assembly}, {n_aligns} align groups")


if __name__ == "__main__":
    main()
