#!/usr/bin/env python3
"""
assemble_sheets.py -- resolve / assemble / tile / verify / emit.

Reads templates/layout.yaml (the spec) and the source file it names, and emits
templates/print/sheets/sheet-NNN.svg, ordered so filename order is print order.

The engine makes no layout decisions: it copies referenced geometry verbatim,
applies the spec's position + transform, tiles each sheet's drawing area onto the
paper safe-area by a fixed rule, and fails loudly when the spec is malformed.
"""

import argparse
import copy
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
PRINT_DIR = TEMPLATES / "print"
SHEETS_DIR = PRINT_DIR / "sheets"
DEFAULT_SPEC = TEMPLATES / "layout.yaml"

# Physical-sheet CSS, added to the spec's output-style on every page.
# Physical-sheet CSS, added to the spec's output-style on every page. `.overlap`
# is deliberately lighter and dashed: it is a guide for lining up tiles, not ink.
CSS2 = ("\n.crop { stroke: #999999; stroke-width: 0.25; }\n"
        ".overlap { stroke: #999999; stroke-width: 0.15; stroke-dasharray: 2 2; fill: none; }\n"
        ".note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }\n")

# Corner registration ticks are inset this far into the safe area, so they print
# fully instead of landing on the inkable edge where the printer may clip them.
CROP_INSET = 5.0


def fmt(x):
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Affine transforms + path geometry (for the ink-bounds check)
# --------------------------------------------------------------------------

_IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


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
            raise AssertionError(f"unsupported transform {kind!r} in {tstr!r}")
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


_PATH_NUMS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}
_NUMBER = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")


def _path_points(d):
    """Control/end points a path passes through, in the path's own frame."""
    toks = _NUMBER.findall(d or "")
    i, n = 0, len(toks)
    letter, x, y = None, 0.0, 0.0
    start = (0.0, 0.0)
    pts = []

    def take(k):
        nonlocal i
        vals = [float(t) for t in toks[i:i + k]]
        i += k
        return vals

    while i < n:
        if toks[i].isalpha():
            letter = toks[i]
            i += 1
            if letter in "zZ":
                x, y = start
                continue
        elif letter is None:
            raise AssertionError(f"path data without a command: {d!r}")
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


def _walk_pts(el, matrix, out):
    m = _mul(matrix, transform_matrix(el.get("transform") or ""))
    if el.tag == "path":
        for x, y in _path_points(el.get("d")):
            out.append(_apply_matrix(m, x, y))
    for child in el:
        _walk_pts(child, m, out)


# --------------------------------------------------------------------------
# Spec + source loading
# --------------------------------------------------------------------------

def strip_ns(elem):
    for e in elem.iter():
        if isinstance(e.tag, str) and e.tag.startswith("{"):
            e.tag = e.tag.split("}", 1)[1]
    return elem


def load_spec(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_source(spec_dir, source_file):
    src = spec_dir / source_file
    if not src.exists():
        raise SystemExit(f"source-file not found: {src}")
    return strip_ns(ET.parse(src).getroot())


def resolve(root, xpath):
    candidates = [xpath]
    # ElementTree (py3.13+) rejects absolute paths; make them relative.
    if xpath.startswith("//"):
        candidates.append("." + xpath)
    elif xpath.startswith("/"):
        candidates.append("." + xpath)
    for xp in candidates:
        for q in (xp, xp.replace('"', "'")):
            try:
                els = root.findall(q)
            except SyntaxError:
                continue
            if els:
                return els
    return []


def serialize(el):
    c = copy.deepcopy(el)
    for e in c.iter():
        if "id" in e.attrib:
            del e.attrib["id"]
    return ET.tostring(c, encoding="unicode")


# --------------------------------------------------------------------------
# Element assembly
# --------------------------------------------------------------------------

def transform_str(position, transform):
    parts = [f"translate({fmt(position['x'])} {fmt(position['y'])})"]
    if transform:
        if transform.get("rotate"):
            parts.append(f"rotate({fmt(transform['rotate'])})")
        if "scale" in transform:
            sx, sy = transform["scale"]
            parts.append(f"scale({fmt(sx)} {fmt(sy)})")
    return " ".join(parts)


def element_matrix(position, transform):
    return transform_matrix(transform_str(position, transform))


def assemble_body(sheet, root):
    out = []
    for el in sheet["elements"]:
        if "text" in el:
            cls = el.get("class", "label")
            x, y = el["position"]["x"], el["position"]["y"]
            out.append(f'<text class="{cls}" x="{fmt(x)}" y="{fmt(y)}">{esc(el["text"])}</text>')
        elif "source-id" in el:
            els = resolve(root, el["source-id"])
            if not els:
                raise SystemExit(f'{sheet["title"]}: source-id {el["source-id"]!r} resolves to nothing')
            for e in els:
                tr = transform_str(el["position"], el.get("transform"))
                out.append(f'<g transform="{tr}">{serialize(e)}</g>')
        else:
            raise SystemExit(f'{sheet["title"]}: element is neither text nor source-id: {el!r}')
    return "\n".join(out)


# --------------------------------------------------------------------------
# Ink-bounds check
# --------------------------------------------------------------------------

def element_bbox(el):
    """Ink bbox of a source-id element after its position + transform."""
    pts = []
    m = element_matrix(el["position"], el.get("transform"))
    for e in el["_resolved"]:
        _walk_pts(e, m, pts)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def check_bounds(sheet, root, warnings, tol=0.5):
    W = float(sheet["dimensions"]["width"])
    H = float(sheet["dimensions"]["height"])
    for el in sheet["elements"]:
        if "text" in el:
            x, y = el["position"]["x"], el["position"]["y"]
            if not (math.isfinite(x) and math.isfinite(y)):
                raise SystemExit(f'{sheet["title"]}: text {el["text"]!r} has a non-finite position')
            continue
        els = resolve(root, el["source-id"])
        if not els:
            raise SystemExit(f'{sheet["title"]}: source-id {el["source-id"]!r} resolves to nothing')
        el["_resolved"] = els
        box = element_bbox(el)
        if box is None:
            continue
        x0, y0, x1, y1 = box
        # Control-point bbox is conservative (bezier control points may poke
        # outside the viewBox while the curve stays inside), so this is a hint,
        # not a failure.
        if x0 < -tol or y0 < -tol or x1 > W + tol or y1 > H + tol:
            warnings.append(f'{sheet["title"]}: {el["source-id"]!r} ink bbox '
                            f'({x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}) extends outside '
                            f'drawing area {W}x{H}')


# --------------------------------------------------------------------------
# Tiling
# --------------------------------------------------------------------------

def overlap_pair(overlap):
    if isinstance(overlap, dict):
        return float(overlap.get("x", 0.0)), float(overlap.get("y", 0.0))
    return float(overlap), float(overlap)


def corner_ticks(margin_x, margin_y, safe_w, safe_h):
    L = 5.0
    lo_x = margin_x + CROP_INSET
    hi_x = margin_x + safe_w - CROP_INSET
    lo_y = margin_y + CROP_INSET
    hi_y = margin_y + safe_h - CROP_INSET
    segs = []
    for cx in (lo_x, hi_x):
        for cy in (lo_y, hi_y):
            sx = 1.0 if cx == lo_x else -1.0
            sy = 1.0 if cy == lo_y else -1.0
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx + sx * L)}" y2="{fmt(cy)}"/>')
            segs.append(f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}" '
                        f'x2="{fmt(cx)}" y2="{fmt(cy + sy * L)}"/>')
    return "<g>" + "".join(segs) + "</g>"


def overlap_marks(c, r, cols, rows, margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y):
    """Dashed lines on BOTH halves of every overlap seam, so adjacent tiles can be
    aligned by matching their two lines. A tile has a seam on each side where it
    shares content with a neighbour (left/right/top/bottom)."""
    segs = []
    if c < cols - 1:  # right seam (next tile repeats content on this edge)
        x = margin_x + safe_w - overlap_x
        segs.append(f'<line class="overlap" x1="{fmt(x)}" y1="{fmt(margin_y)}" '
                    f'x2="{fmt(x)}" y2="{fmt(margin_y + safe_h)}"/>')
    if c > 0:  # left seam (this tile repeats the previous tile's content)
        x = margin_x + overlap_x
        segs.append(f'<line class="overlap" x1="{fmt(x)}" y1="{fmt(margin_y)}" '
                    f'x2="{fmt(x)}" y2="{fmt(margin_y + safe_h)}"/>')
    if r < rows - 1:  # bottom seam
        y = margin_y + safe_h - overlap_y
        segs.append(f'<line class="overlap" x1="{fmt(margin_x)}" y1="{fmt(y)}" '
                    f'x2="{fmt(margin_x + safe_w)}" y2="{fmt(y)}"/>')
    if r > 0:  # top seam
        y = margin_y + overlap_y
        segs.append(f'<line class="overlap" x1="{fmt(margin_x)}" y1="{fmt(y)}" '
                    f'x2="{fmt(margin_x + safe_w)}" y2="{fmt(y)}"/>')
    return "<g>" + "".join(segs) + "</g>" if segs else ""


def tile(title, W, H, body, style, paper):
    trim_w = float(paper["trim"]["width"])
    trim_h = float(paper["trim"]["height"])
    safe_w = float(paper["safe-area"]["width"])
    safe_h = float(paper["safe-area"]["height"])
    overlap_x, overlap_y = overlap_pair(paper["overlap"])
    margin_x = (trim_w - safe_w) / 2.0
    margin_y = (trim_h - safe_h) / 2.0
    stride_x = safe_w - overlap_x
    stride_y = safe_h - overlap_y

    assert stride_x > 0 and stride_y > 0, "overlap must be smaller than the safe area"

    cols = 1 if W <= safe_w else math.ceil((W - safe_w) / stride_x) + 1
    rows = 1 if H <= safe_h else math.ceil((H - safe_h) / stride_y) + 1

    pages = []
    if cols == 1 and rows == 1:
        ox = margin_x + (safe_w - W) / 2.0
        oy = margin_y + (safe_h - H) / 2.0
        tr = f"translate({fmt(ox)} {fmt(oy)})"
        page = f'<g transform="{tr}">{body}</g>'
        pages.append((page, tr, 1, 1, 1))
        return pages, (cols, rows), (ox, oy)

    clip = (f'<defs><clipPath id="clip"><rect x="{fmt(margin_x)}" y="{fmt(margin_y)}" '
            f'width="{fmt(safe_w)}" height="{fmt(safe_h)}"/></clipPath></defs>')
    for r in range(rows):
        for c in range(cols):
            tx = margin_x - c * stride_x
            ty = margin_y - r * stride_y
            tr = f"translate({fmt(tx)} {fmt(ty)})"
            idx = r * cols + c + 1
            parts = [
                '<g clip-path="url(#clip)">',
                f'<g transform="{tr}">{body}</g>',
                '</g>',
                corner_ticks(margin_x, margin_y, safe_w, safe_h),
                overlap_marks(c, r, cols, rows, margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y),
                f'<text class="note" x="{fmt(trim_w / 2)}" y="{fmt(trim_h - 2.5)}">'
                f'{esc(title)} \u00b7 tile {idx}/{cols * rows} \u00b7 {cols}x{rows}</text>',
            ]
            pages.append(("\n".join(parts), tr, idx, cols, rows))
    return pages, (cols, rows), None


def sheet_svg(style, defs, body, trim_w, trim_h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{fmt(trim_w)}mm" height="{fmt(trim_h)}mm" '
            f'viewBox="0 0 {fmt(trim_w)} {fmt(trim_h)}">\n'
            f'<style type="text/css">{style}{CSS2}</style>\n'
            f'{defs}'
            f'<rect x="0" y="0" width="{fmt(trim_w)}" height="{fmt(trim_h)}" fill="#ffffff"/>\n'
            f'{body}\n</svg>\n')


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Assemble sheets from the declarative spec.")
    ap.add_argument("--spec", default=str(DEFAULT_SPEC), help="path to layout.yaml")
    ap.add_argument("--out-dir", default=str(SHEETS_DIR), help="sheet SVGs + manifest dir")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    spec_dir = spec_path.parent
    root = load_source(spec_dir, spec["source-file"])
    style = spec["output-style"]
    paper = spec["paper"]

    # validate paper
    for k in ("trim", "safe-area"):
        assert "width" in paper[k] and "height" in paper[k], f"paper.{k} needs width/height"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("sheet-*.svg"):
        p.unlink()

    trim_w = float(paper["trim"]["width"])
    trim_h = float(paper["trim"]["height"])

    warnings = []
    n_sheets = 0
    n_tiled = 0

    for sheet in spec["sheets"]:
        W = float(sheet["dimensions"]["width"])
        H = float(sheet["dimensions"]["height"])
        check_bounds(sheet, root, warnings)
        body = assemble_body(sheet, root)
        pages, (cols, rows), _ = tile(sheet["title"], W, H, body, style, paper)

        for page_body, tr, tile_idx, c, r in pages:
            n_sheets += 1
            fn = f"sheet-{n_sheets:03d}.svg"
            svg = sheet_svg(style, "", page_body, trim_w, trim_h)
            (out_dir / fn).write_text(svg, encoding="utf-8")
            if (cols, rows) != (1, 1):
                n_tiled += 1

    print(f"wrote {n_sheets} sheets ({n_tiled} tiled) -> {out_dir}")
    if warnings:
        print(f"\n{len(warnings)} bounds warning(s):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("no bounds warnings")
    print("all checks passed")


if __name__ == "__main__":
    main()
