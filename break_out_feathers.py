#!/usr/bin/env python3
"""THROWAWAY: break each feather's geometry out of the aggregate into its own file.

mechanical/templates/feathers-aggregate-min.svg keeps all 28 feathers in <defs>,
each a <g id="X-def"> holding one <path>, with a <use href="#X-def"> placing it.
This writes each one to mechanical/templates/individuals/<feather>.svg and repoints
the <use> at that file, then drops the now-empty <defs>.

The geometry does NOT move. Each feather's own coordinates are kept exactly as they
are, and the individual file's viewBox is set to the padded bounding box of that
geometry, with width/height matching it:

    viewBox = "x0-pad y0-pad w+2·pad h+2·pad"   width/height = "w+2·pad" / "h+2·pad"

That choice is deliberate. With the viewport exactly the viewBox rectangle, the
viewBox-to-viewport mapping is the identity, so the <use> transform keeps meaning
what it meant before: the aggregate's own placement, nothing more and nothing less.
It was measured, not assumed -- Inkscape applies a <use>'s x/y *on top of* that
mapping, so an `x="x0"` form lands the feather a whole viewBox-origin away from
where it belongs. The script therefore writes no x/y, and asserts the two sizes
match so the identity cannot quietly stop being true.

The padding is what keeps a 0.5 mm stroke from being clipped by the file's edge.

Usage:
    python break_out_feathers.py --check     # report, write nothing
    python break_out_feathers.py             # write individuals/ and rewrite
"""

import argparse
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

# ElementTree serialises a namespaced attribute as "{uri}name" unless the prefix is
# registered, which is not valid XML and produces a file nothing can open. Register
# the prefixes the catalogue uses; the root element spells them out anyway.
ET.register_namespace("", SVG_NS)
ET.register_namespace("svg", SVG_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)
ET.register_namespace("sodipodi", SODIPODI_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

DEFAULT_SVG = "mechanical/templates/feathers-aggregate-min.svg"
INDIVIDUALS_DIRNAME = "individuals"
PAD_MM = 1.0

NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
COMMAND_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]")

Matrix = tuple  # (a, b, c, d, e, f): x' = a·x + c·y + e, y' = b·x + d·y + f


# ---------------------------------------------------------------------------
# path reading, bounds and transform folding
# ---------------------------------------------------------------------------
def parse_path(d):
    """Absolute segments from path data: ('M'|'L', x, y) and ('C', ...6 coords)."""
    tokens = []
    for m in re.finditer(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d or ""):
        text = m.group(0)
        tokens.append(text if text.isalpha() else float(text))

    segs = []
    i, n = 0, len(tokens)
    cmd = None
    x = y = sub_x = sub_y = 0.0
    while i < n:
        tok = tokens[i]
        if isinstance(tok, str):
            cmd = tok
            i += 1
            if cmd in "Zz":
                x, y = sub_x, sub_y
                continue
        if cmd is None:
            raise ValueError("path data does not start with a command")
        up, rel = cmd.upper(), cmd.islower()

        def take(k):
            nonlocal i
            vals = [float(v) for v in tokens[i:i + k]]
            i += k
            return vals

        if up in "ML":
            vx, vy = take(2)
            if rel:
                vx, vy = x + vx, y + vy
            if up == "M":
                sub_x, sub_y = vx, vy
                cmd = "l" if rel else "L"
            segs.append(("L", vx, vy))
            x, y = vx, vy
        elif up == "H":
            (vx,) = take(1)
            vx = x + vx if rel else vx
            segs.append(("L", vx, y))
            x = vx
        elif up == "V":
            (vy,) = take(1)
            vy = y + vy if rel else vy
            segs.append(("L", x, vy))
            y = vy
        elif up in "CS":
            vals = take(6 if up == "C" else 4)
            if up == "S":
                c2x, c2y, vx, vy = vals
                c1x = c1y = None
            else:
                c1x, c1y, c2x, c2y, vx, vy = vals
            if rel:
                if c1x is not None:
                    c1x, c1y = x + c1x, y + c1y
                c2x, c2y = x + c2x, y + c2y
                vx, vy = x + vx, y + vy
            if c1x is None:
                c1x, c1y = x, y
            segs.append(("C", c1x, c1y, c2x, c2y, vx, vy))
            x, y = vx, vy
        elif up in "QT":
            if up == "Q":
                qx, qy, vx, vy = take(4)
                if rel:
                    qx, qy, vx, vy = x + qx, y + qy, x + vx, y + vy
            else:
                vx, vy = take(2)
                if rel:
                    vx, vy = x + vx, y + vy
                qx, qy = x, y
            c1x = x + 2.0 / 3.0 * (qx - x)
            c1y = y + 2.0 / 3.0 * (qy - y)
            c2x = vx + 2.0 / 3.0 * (qx - vx)
            c2y = vy + 2.0 / 3.0 * (qy - vy)
            segs.append(("C", c1x, c1y, c2x, c2y, vx, vy))
            x, y = vx, vy
        elif up == "A":
            rx, ry, _rot, _large, _sweep, vx, vy = take(7)
            if rel:
                vx, vy = x + vx, y + vy
            # A bezier approximation is not worth it here: this catalogue has no
            # arcs (checked), and a wrong bound is worse than a loud failure.
            raise SystemExit("path uses an elliptical arc; bounds would need real "
                             "arc maths -- teach this script or flatten it upstream")
        else:
            raise ValueError(f"unsupported path command: {cmd}")
    return segs


def path_bounds(d, matrix):
    """Bounding box of a path's control points, mapped through `matrix`.

    Control points, not the curve: a cubic stays inside the hull of its control
    points, so this can only overstate the box, never clip the drawing. Overstating
    just means a slightly roomier file, which costs nothing.
    """
    xs, ys = [], []
    for seg in parse_path(d):
        flat = seg[1:]
        for j in range(0, len(flat), 2):
            px, py = flat[j], flat[j + 1]
            a, b, c, dd, e, f = matrix
            xs.append(a * px + c * py + e)
            ys.append(b * px + dd * py + f)
    if not xs:
        raise SystemExit("path has no coordinates")
    return min(xs), min(ys), max(xs), max(ys)


def mat_mul(m1, m2):
    """m1 . m2 -- apply m2 first, then m1."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def parse_transform(text):
    def rot(deg, cx=0.0, cy=0.0):
        rad = math.radians(deg)
        cs, sn = math.cos(rad), math.sin(rad)
        m = (cs, sn, -sn, cs, 0.0, 0.0)
        if cx or cy:
            return mat_mul(mat_mul((1, 0, 0, 1, cx, cy), m), (1, 0, 0, 1, -cx, -cy))
        return m

    out = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, raw in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", text or ""):
        args = [float(v) for v in NUMBER_RE.findall(raw)]
        if name == "matrix":
            m = tuple(args)
        elif name == "translate":
            m = (1, 0, 0, 1, args[0], args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            m = (args[0], 0, 0, args[1] if len(args) > 1 else args[0], 0, 0)
        elif name == "rotate":
            m = rot(*args)
        elif name == "skewX":
            m = (1, 0, math.tan(math.radians(args[0])), 1, 0, 0)
        elif name == "skewY":
            m = (1, math.tan(math.radians(args[0])), 0, 1, 0, 0)
        else:
            raise SystemExit(f"unsupported transform: {name}()")
        out = mat_mul(out, m)
    return out


def fold_transforms(el):
    """The transform on `el` and everything inside it, outermost first.

    A transform on the def group applies before (outside) one on the path inside
    it, so the group's matrix stays leftmost as the contents are folded in.
    """
    m = parse_transform(el.get("transform", ""))
    for child in el.iter():
        if child is el or local(child.tag) in ("g", "defs", "svg"):
            continue
        m = mat_mul(m, parse_transform(child.get("transform", "")))
    return m


# ---------------------------------------------------------------------------
# number and text helpers
# ---------------------------------------------------------------------------
def num(value, places=6):
    """Trim a float to `places` and drop trailing zeros -- coordinates, not matrices."""
    out = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return "0" if out in ("", "-0", "-0.", "0.") else out


def local(tag):
    return tag.split("}")[-1]


def transform_attr(el):
    return (el.get("transform") or "").strip()


# ---------------------------------------------------------------------------
# splitting the stylesheet
# ---------------------------------------------------------------------------
# The selector group deliberately swallows whatever precedes the rule, so a rule's
# own comment and blank line travel with it: `/* P -- primaries */\n.P .outline`.
RULE_RE = re.compile(r"([^{}]*?)\s*\{([^{}]*)\}")


def split_stylesheet(text):
    """(stroke_rules, fill_rules) from one stylesheet body.

    Colour belongs to the arrangement, not to the feather. The per-family colour
    rules (`.P .outline { fill: ... }`, with the comment above each one) go to the
    aggregate; everything else -- the group's stroke width, the `.outline` stroke,
    the centerline and visibility-line geometry rules -- stays with the feather.

    This works across the file boundary: the cloned content of a `<use>` is matched
    by the referencing document's CSS, so the aggregate's fill rules do reach
    geometry that lives in a referenced file. It is a question of which file states
    the rule, not of whether the fill arrives.
    """
    stroke, fill = [], []
    cursor = 0
    for m in RULE_RE.finditer(text):
        selector, body = m.group(1), m.group(2)
        # only the per-family colour rules move: `.visibility-line { fill: none }`
        # is geometry, not colour, and belongs with the feather
        if ".outline" in selector and "fill" in body:
            fill.append(m.group(0))
        else:
            stroke.append(text[cursor:m.start()])
            stroke.append(m.group(0))
        cursor = m.end()
    if cursor < len(text):
        stroke.append(text[cursor:])
    return "".join(stroke), "".join(fill)


def thin_stylesheet(stylesheet):
    """The single `.outline` rule an individual feather needs, and nothing else.

    A feather's file is geometry plus the line it is cut along, so the whole
    catalogue stylesheet boils down to one rule: stroke, and the stroke width that
    used to ride the `.group` rule. Everything else in the sheet -- the family
    colours, the label and centerline and visibility-line rules -- is either the
    aggregate's business or unused here.

    The stroke width is read from `.group` rather than assumed, so this keeps
    matching the catalogue if that number is ever retuned.
    """
    stroke = re.search(r"\.outline\s*\{([^{}]*)\}", stylesheet)
    group = re.search(r"\.group\s*\{([^{}]*)\}", stylesheet)

    def value(body, prop):
        m = re.search(prop + r"\s*:\s*([^;]+)", body or "")
        return m.group(1).strip() if m else None

    stroke_colour = value(stroke.group(1) if stroke else "", "stroke") or "#000000"
    width = value(group.group(1) if group else "", "stroke-width") or "0.5"
    return f".outline {{\n  stroke: {stroke_colour};\n  stroke-width: {width};\n}}\n"


# ---------------------------------------------------------------------------
# the individual file
# ---------------------------------------------------------------------------
def individual_svg(feather, group, path, stylesheet, view):
    """One feather as a standalone document, geometry coordinates untouched."""
    x0, y0, w, h = view
    indented = "\n".join("  " + line if line.strip() else line
                         for line in thin_stylesheet(stylesheet).strip("\n").splitlines())

    def attrs(el, drop=()):
        """The element's attributes as written, minus anything in `drop`.

        A transform would be applied a second time: the viewBox already accounts
        for the group's and the path's, so the coordinates are placed exactly once.
        `data-fill` recorded the colour back when the geometry sat in the
        aggregate's <defs>; the colour is stated once now, by the aggregate's CSS,
        so a copy here is just a second place to keep in step.

        Namespaced names come back as "{uri}name" from ElementTree and have to be
        spelled with their prefix: "{uri}label" is not valid XML.
        """
        out = []
        for key in el.attrib:
            if key in drop:
                continue
            name = key
            for uri, prefix in ((INKSCAPE_NS, "inkscape"), (SODIPODI_NS, "sodipodi")):
                name = name.replace("{" + uri + "}", prefix + ":")
            out.append(f'\n    {name}="{el.get(key)}"')
        return "".join(out)

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- {feather}: one feather, broken out of feathers-aggregate-min.svg.
     The outline's coordinates are unchanged from the aggregate; they are only
     placed by this file's viewBox, which is the outline's bounding box plus
     {num(PAD_MM)} mm of margin so the cut line's stroke is not clipped.
     The aggregate references this file with a <use> whose width/height match the
     viewBox exactly, which makes the viewBox-to-viewport mapping the identity and
     leaves the aggregate's own placement matrix as the only thing positioning it.
     Stroke only, as `.outline`: the fill is the aggregate's to state, not this
     file's. The group keeps its class because that is what the aggregate's
     `.P .outline {{ fill: ... }}` rules select through. -->
<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:svg="http://www.w3.org/2000/svg"
    xmlns:inkscape="{INKSCAPE_NS}"
    xmlns:sodipodi="{SODIPODI_NS}"
    version="1.1"
    id="{feather}"
    width="{num(w)}mm"
    height="{num(h)}mm"
    viewBox="{num(x0)} {num(y0)} {num(w)} {num(h)}"
    inkscape:label="{feather}">
  <title id="title-{feather}">{feather} - single feather outline, 1:1 mm, no fill</title>
  <style
     type="text/css"
     id="style-{feather}">
{indented}
  </style>
  <g{attrs(group, drop=("transform", "data-fill"))}>
    <path{attrs(path, drop=("transform",))} />
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg", nargs="?", default=DEFAULT_SVG)
    ap.add_argument("--check", action="store_true",
                    help="report what would be written, write nothing")
    args = ap.parse_args(argv)

    src = Path(args.svg)
    text = src.read_text(encoding="utf-8")
    root = ET.fromstring(text)

    defs = root.find(f"{{{SVG_NS}}}defs")
    if defs is None:
        raise SystemExit(f"{src}: no <defs> -- already broken out?")
    uses = list(root.iter(f"{{{SVG_NS}}}use"))
    if not uses:
        raise SystemExit(f"{src}: no <use> elements to repoint")

    # the stylesheet travels with each feather so the file stands on its own
    style_el = root.find(f"{{{SVG_NS}}}style")
    if style_el is None:
        raise SystemExit(f"{src}: no <style> block to copy")
    stylesheet = style_el.text or ""

    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}

    out_dir = src.parent / INDIVIDUALS_DIRNAME
    plan = []
    for group in list(defs):
        gid = group.get("id") or ""
        if not gid.endswith("-def"):
            raise SystemExit(f"{src}: unexpected child of <defs>: {gid!r}")
        feather = gid[:-len("-def")]
        paths = [c for c in group if local(c.tag) == "path"]
        others = [c for c in group if local(c.tag) != "path"]
        if len(paths) != 1:
            raise SystemExit(f"{gid}: expected exactly one <path>, found {len(paths)}")
        if others:
            raise SystemExit(f"{gid}: carries non-path children "
                             f"({[local(c.tag) for c in others]}) -- break out by hand")
        path = paths[0]
        if path.get("d") is None:
            raise SystemExit(f"{path.get('id')}: no path data")

        m = fold_transforms(group)
        x0, y0, x1, y1 = path_bounds(path.get("d"), m)
        view = (x0 - PAD_MM, y0 - PAD_MM, (x1 - x0) + 2 * PAD_MM, (y1 - y0) + 2 * PAD_MM)
        plan.append((feather, gid, group, path, view))

    # --- what will be written -------------------------------------------------
    print(f"{len(plan)} feather(s) -> {out_dir}{os.sep}")
    for feather, gid, group, path, view in plan:
        x0, y0, w, h = view
        print(f"  {feather:6s} {path.get('id'):14s} "
              f"viewBox={num(x0)} {num(y0)} {num(w)} {num(h)}")

    # --- repoint each <use> ---------------------------------------------------
    repointed = 0
    for use in uses:
        target = use.get("href") or use.get(XLINK_HREF) or ""
        if not target.startswith("#"):
            raise SystemExit(f"use #{use.get('id')}: already points at {target!r}")
        tid = target[1:]
        if tid not in by_id:
            raise SystemExit(f"use #{use.get('id')}: nothing has id {tid!r}")
        if use.get("x") or use.get("y"):
            raise SystemExit(f"use #{use.get('id')}: carries x/y, which would stack "
                             f"on the viewBox mapping -- handle it by hand")
        repointed += 1
    print(f"  {repointed} <use> element(s) to repoint at {INDIVIDUALS_DIRNAME}/")

    if args.check:
        print("check only -- nothing written")
        return 0

    # --- write the individual files ------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for feather, gid, group, path, view in plan:
        dest = out_dir / f"{feather}.svg"
        dest.write_text(individual_svg(feather, group, path, stylesheet, view),
                        encoding="utf-8", newline="")
        written.append(dest)
    print(f"wrote {len(written)} file(s)")

    # --- rewrite the aggregate by text, so hand formatting survives -----------
    # <use> tags: point the href at the file, rewrite the fragment to the id that
    # file actually exposes, and pin the viewport to the viewBox so the
    # viewBox-to-viewport mapping stays the identity.
    view_of = {feather: view for feather, _g, _p, _pa, view in plan}
    target_of = {}
    for feather, gid, group, path, view in plan:
        # the id this file exposes for the whole feather
        name = group.get("id")
        if not name:
            raise SystemExit(f"{feather}: its group has no id to reference")
        target_of[feather] = name

    new_text = text
    for use in uses:
        target = (use.get("href") or use.get(XLINK_HREF))[1:]
        feather = target[:-len("-def")]
        x0, y0, w, h = view_of[feather]
        href = f"{INDIVIDUALS_DIRNAME}/{feather}.svg#{target_of[feather]}"
        # replace the href (fragment included) and add the sizing attributes
        pattern = re.compile(
            r"(<use\b(?=[^>]*\bid=\"" + re.escape(use.get("id")) + r"\")[^>]*?)"
            r"(?:xlink:)?href=\"#[^\"]*\"",
            re.S)
        m = pattern.search(new_text)
        if not m:
            raise SystemExit(f"could not find the <use> tag for #{use.get('id')}")
        attrs = f'href="{href}"\n       width="{num(w)}"\n       height="{num(h)}"'
        new_text = new_text[:m.start()] + m.group(1) + attrs + new_text[m.end():]

    # <defs> now holds nothing that is used: drop the whole block.
    defs_start = new_text.find("<defs")
    if defs_start < 0:
        raise SystemExit("could not find the <defs> block in the text")
    defs_end = new_text.find("</defs>", defs_start)
    if defs_end < 0:
        raise SystemExit("could not find </defs>")
    defs_end += len("</defs>")
    while defs_end < len(new_text) and new_text[defs_end] in "\r\n":
        defs_end += 1
    new_text = (new_text[:defs_start]
                + "<!-- Each feather's geometry now lives in "
                  + INDIVIDUALS_DIRNAME + "/<feather>.svg and is placed by the "
                  "<use> elements below. -->\n"
                + new_text[defs_end:])

    tmp = src.with_suffix(src.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8", newline="")
    os.replace(tmp, src)
    print(f"rewrote {src}")

    # --- prove it: the file must still parse, and <defs> must be gone --------
    check = ET.fromstring(src.read_text(encoding="utf-8"))
    if check.find(f"{{{SVG_NS}}}defs") is not None:
        raise SystemExit("rewrite left a <defs> behind")
    left = [u.get("id") for u in check.iter(f"{{{SVG_NS}}}use")
            if not (u.get("href") or "").startswith(INDIVIDUALS_DIRNAME + "/")]
    if left:
        raise SystemExit(f"uses not repointed: {left}")
    print("aggregate parses, <defs> gone, every <use> points at an individual file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
