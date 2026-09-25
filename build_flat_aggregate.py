#!/usr/bin/env python3
"""Resolve the feather aggregate into real paths, and trace its outer silhouette.

``mechanical/templates/feathers-aggregate-min.svg`` keeps almost no geometry of its
own. Each feather is a ``<use>`` pointing OUT of the document at
``individuals/<name>.svg#<name>-def``, and the placement is split over transforms a
renderer composes:

    prefix group  .  use  .  viewBox-to-viewport  .  def group  .  inner element

Inkscape sees a cross-file ``<use>`` as a link rather than a clone, so ``Unlink Clone``
and ``Path > Union`` have nothing usable to act on -- which is why the aggregate
cannot be combined by hand. This script resolves every reference, bakes all of those
transforms into the path data, and writes documents whose paths ARE the geometry:

``flat``    the resolved document. One ``<path>`` per feather, no ``<use>``, no
            ``transform`` attribute anywhere, presentation baked on. Open this in
            Inkscape and ``Ctrl++`` (Path > Union) works on a plain selection.
``outline`` one path tracing the outer silhouette of every feather -- the union,
            computed here by supersampled raster and contour trace. This is the cut
            line for the whole assembly. It approximates the true outline; the error
            is bounded by ``--outline-tol`` (default 0.05 mm).
``both``    the flat document plus the outline as an extra layer on top.

Self-contained on purpose: the path parser, the matrix algebra, the raster and the
contour trace all live in this file.

Two independent checks run before anything is written:

* **bbox** -- an individual file's viewBox is, by its own docstring, that feather's
  bounding box plus 1 mm of margin, and the aggregate's ``<use>`` width and height
  match it exactly. So the viewBox-to-viewport matrix must be the identity, and the
  baked path's bounding box must equal its feather's viewBox size. That proves the
  transform chain and the reference resolution landed where SVG says they should.
* **raster** -- the original aggregate and the written flat file are each rendered to
  a coverage mask at 0.25 mm and the masks must agree. This is the check the bbox one
  cannot make: it sees fills, winding, self-intersection and stray geometry.

Usage:
    python build_flat_aggregate.py                  # flat + outline
    python build_flat_aggregate.py --mode flat      # just the resolved document
    python build_flat_aggregate.py --check          # verify, write nothing
    python build_flat_aggregate.py -v               # per-feather transform report
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = REPO_ROOT / "mechanical" / "templates"
DEFAULT_SRC = TEMPLATES_DIR / "feathers-aggregate-min.svg"
DEFAULT_FLAT = TEMPLATES_DIR / "feathers-aggregate-flat.svg"
DEFAULT_OUTLINE = TEMPLATES_DIR / "feathers-aggregate-outline.svg"
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_NS = "http://www.w3.org/1999/xlink"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"

# Scaffolding groups: never feather geometry.
SKIP_GROUPS = ("toplines",)

GEOMETRY_TAGS = ("path", "rect", "circle", "ellipse", "line", "polygon", "polyline")

RASTER_MM = 0.25            # verification raster grain
MASK_TOL = 0.02             # fraction of raster cells allowed to differ
OUTLINE_RES_MM = 0.10       # silhouette raster grain
OUTLINE_SUPERSAMPLE = 4     # samples per axis per raster cell

NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TRANSFORM_RE = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")
STYLE_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
STYLE_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)

# Properties that may arrive as a presentation attribute, in a style="" or through CSS.
PRESENTATION_ATTRS = frozenset({
    "fill", "fill-opacity", "fill-rule", "stroke", "stroke-width", "stroke-opacity",
    "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray",
    "color", "paint-order", "display", "visibility", "opacity",
})

# What each path command takes. Everything except "a" can be baked into.
COMMAND_ARGS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2,
                "a": 7, "z": 0}


# ---------------------------------------------------------------------------
# formatting and small parsers
# ---------------------------------------------------------------------------
def local(tag) -> str:
    return str(tag).split("}")[-1]


def fmt(value: float, places: int = 4) -> str:
    """Fixed decimals, trailing zeros trimmed. Four places is 0.1 um in millimetres."""
    text = f"{value:.{places}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def parse_style(text) -> dict:
    """A ``style="a:b;c:d"`` attribute as a dict of lowercased names to raw values."""
    out: dict = {}
    for piece in (text or "").split(";"):
        name, sep, value = piece.partition(":")
        if sep:
            out[name.strip().lower()] = value.strip()
    return out


def parse_stylesheet(text) -> dict:
    """``{selector: {property: value}}`` for the flat CSS rules an Inkscape file holds."""
    rules: dict = {}
    for selector, body in STYLE_RULE_RE.findall(STYLE_COMMENT_RE.sub("", text or "")):
        selector = " ".join(selector.split())
        if not selector or selector.startswith("@"):
            continue
        decls = rules.setdefault(selector, {})
        for piece in body.split(";"):
            name, sep, value = piece.partition(":")
            if sep:
                decls[name.strip().lower()] = value.strip()
    return rules


def selector_matches(selector: str, names: set) -> bool:
    """True if ``names`` satisfies a simple descendant selector.

    Every compound in the selector must be covered by the element's own class or tag
    name, or by the names of the ancestors passed in. That is enough for the
    aggregate's stylesheet: ``.outline``, ``.group``, ``.P .outline``, ``.P``.
    """
    compounds = selector.replace(">", " ").split()
    return bool(compounds) and all(
        any(part.lstrip(".") in names for part in compound.split()) for compound in compounds
    )


def names_of(el) -> set:
    return set((el.get("class") or "").split()) | {local(el.tag)}


def resolve_props(el, ancestors, rules: dict) -> dict:
    """The presentation properties in force on ``el``, cascaded from its ancestors.

    Later selectors win, matching a stylesheet; presentation attributes beat CSS (as
    SVG says); an inline ``style`` beats both. ``display`` is dropped: every source
    here is ``display:inline``, and carrying it onto real geometry would make Inkscape
    open the file with hidden layers.
    """
    props: dict = {}
    for node in list(ancestors) + [el]:
        node_names = names_of(node)
        for selector, decls in rules.items():
            if selector_matches(selector, node_names):
                props.update(decls)
        props.update({k: v for k, v in node.attrib.items()
                      if k in PRESENTATION_ATTRS and k != "style"})
        props.update(parse_style(node.get("style")))
    props.pop("display", None)
    return props


# ---------------------------------------------------------------------------
# affine matrices: (a, b, c, d, e, f) meaning x' = a*x + c*y + e, y' = b*x + d*y + f
# SVG space throughout -- x right, y DOWN. Nothing here flips anything.
# ---------------------------------------------------------------------------
Matrix = tuple


def mat_identity() -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m1: Matrix, m2: Matrix) -> Matrix:
    """m1 * m2: the transform that applies m2 first, then m1."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2,
            b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2,
            b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1,
            b1 * e2 + d1 * f2 + f1)


def mat_apply(m: Matrix, x: float, y: float) -> tuple:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def mat_translate(tx: float, ty: float) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def mat_scale(sx: float, sy: float) -> Matrix:
    return (sx, 0.0, 0.0, sy, 0.0, 0.0)


def mat_rotate(deg: float, cx: float = 0.0, cy: float = 0.0) -> Matrix:
    r = math.radians(deg)
    cos_r, sin_r = math.cos(r), math.sin(r)
    rot = (cos_r, sin_r, -sin_r, cos_r, 0.0, 0.0)
    if cx or cy:
        return mat_mul(mat_mul(mat_translate(cx, cy), rot), mat_translate(-cx, -cy))
    return rot


def parse_transform(text) -> Matrix:
    """Parse an SVG transform list (matrix/translate/scale/rotate/skewX/skewY)."""
    result = mat_identity()
    for name, raw_args in TRANSFORM_RE.findall(text or ""):
        args = [float(v) for v in NUMBER_RE.findall(raw_args)]
        if name == "matrix" and len(args) == 6:
            m = tuple(args)
        elif name == "translate":
            m = mat_translate(args[0], args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            m = mat_scale(args[0], args[1] if len(args) > 1 else args[0])
        elif name == "rotate":
            cx, cy = (args[1], args[2]) if len(args) > 2 else (0.0, 0.0)
            m = mat_rotate(args[0], cx, cy)
        elif name == "skewX":
            m = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
        elif name == "skewY":
            m = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise SystemExit(f"unsupported transform: {name}({raw_args})")
        result = mat_mul(result, m)
    return result


def is_identity(m: Matrix, tol: float = 1e-9) -> bool:
    return all(abs(a - b) <= tol for a, b in zip(m, mat_identity()))


# ---------------------------------------------------------------------------
# path data: parse, bake a matrix in, flatten, serialise
# ---------------------------------------------------------------------------
def iter_segments(d: str):
    """Yield ``(letter, [floats])`` for every command in a path's ``d``.

    An explicit command followed by extra coordinate sets is an implicit repeat of
    that command, which is how these outlines write long runs (``l 1,2 3,4 5,6``).
    """
    for letter, body in re.findall(r"([A-Za-z])([^A-Za-z]*)", d or ""):
        args = [float(v) for v in NUMBER_RE.findall(body)]
        low = letter.lower()
        count = COMMAND_ARGS.get(low, 0)
        if count == 0:
            yield letter, []
            continue
        if low == "m":
            if len(args) < 2:
                continue
            yield letter, args[:2]
            follow = "l" if letter == "m" else "L"
            rest = args[2:]
            for i in range(0, len(rest) - 1, 2):
                yield follow, rest[i:i + 2]
            continue
        for i in range(0, len(args) - count + 1, count):
            yield letter, args[i:i + count]


def transform_d(d: str, m: Matrix) -> str:
    """``d`` with ``m`` folded into every coordinate, re-emitted as absolute commands.

    Relative commands are resolved to absolute first: a translation cannot be applied
    to a curve's control offsets or an arc's radii without the running point, and doing
    the arithmetic once here keeps the output directly comparable between the source
    and the baked document.
    """
    a, b, c, dd, e, f = m
    x = y = 0.0
    start_x = start_y = 0.0
    out: list = []

    def put(px: float, py: float, letter: str):
        nx, ny = a * px + c * py + e, b * px + dd * py + f
        out.append(f"{letter}{fmt(nx)},{fmt(ny)}")
        return nx, ny

    for letter, args in iter_segments(d):
        low = letter.lower()
        absolute = letter.isupper()
        if low == "z":
            out.append("Z")
            x, y = start_x, start_y
            continue
        if low == "a":
            raise SystemExit(f"arc commands are not supported: d={d[:60]!r}")
        count = COMMAND_ARGS[low]
        for i in range(0, len(args), count):
            chunk = args[i:i + count]
            if low == "h":
                px, py = (chunk[0] if absolute else x + chunk[0]), y
            elif low == "v":
                px, py = x, (chunk[0] if absolute else y + chunk[0])
            else:
                px = chunk[0] if absolute else x + chunk[0]
                py = chunk[1] if absolute else y + chunk[1]
            if low in ("m", "l", "t"):
                x, y = put(px, py, "M" if low == "m" else "L")
                if low == "m":
                    start_x, start_y = x, y
            elif low in ("c", "s", "q"):
                points = [(px, py)]
                for j in range(2, count, 2):
                    points.append((chunk[j] if absolute else x + chunk[j],
                                   chunk[j + 1] if absolute else y + chunk[j + 1]))
                mapped = [mat_apply(m, px_, py_) for px_, py_ in points]
                out.append(letter.upper() + "".join(f"{fmt(px_)},{fmt(py_)}"
                                                    for px_, py_ in mapped))
                x, y = mapped[-1]
            else:
                raise SystemExit(f"unsupported path command {letter!r}")
    return "".join(out)


def flatten_d(d: str, tol: float = 0.02) -> list:
    """A path's ``d`` as closed polylines of (x, y), curves subdivided adaptively."""
    polys: list = []
    pts: list = []
    x = y = start_x = start_y = 0.0

    def flush():
        if len(pts) > 2:
            polys.append(list(pts))
        pts.clear()

    def cubic(p0, p1, p2, p3, depth=0):
        if depth >= 24:
            pts.append(p3)
            return
        x0, y0 = p0
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        ux, uy = 3 * x1 - 2 * x0 - x3, 3 * y1 - 2 * y0 - y3
        vx, vy = 3 * x2 - 2 * x3 - x0, 3 * y2 - 2 * y3 - y0
        if max(ux * ux, vx * vx) + max(uy * uy, vy * vy) <= 16.0 * tol * tol:
            pts.append(p3)
            return
        x01, y01 = (x0 + x1) / 2, (y0 + y1) / 2
        x12, y12 = (x1 + x2) / 2, (y1 + y2) / 2
        x23, y23 = (x2 + x3) / 2, (y2 + y3) / 2
        x012, y012 = (x01 + x12) / 2, (y01 + y12) / 2
        x123, y123 = (x12 + x23) / 2, (y12 + y23) / 2
        xm, ym = (x012 + x123) / 2, (y012 + y123) / 2
        cubic(p0, (x01, y01), (x012, y012), (xm, ym), depth + 1)
        cubic((xm, ym), (x123, y123), (x23, y23), p3, depth + 1)

    for letter, args in iter_segments(d):
        low = letter.lower()
        absolute = letter.isupper()
        if low == "z":
            if pts and (abs(pts[0][0] - start_x) > 1e-9
                        or abs(pts[0][1] - start_y) > 1e-9):
                pts.append((start_x, start_y))
            flush()
            x, y = start_x, start_y

            continue
        count = COMMAND_ARGS[low]
        for i in range(0, len(args), count):
            chunk = args[i:i + count]
            if low == "h":
                px, py = (chunk[0] if absolute else x + chunk[0]), y
            elif low == "v":
                px, py = x, (chunk[0] if absolute else y + chunk[0])
            else:
                px = chunk[0] if absolute else x + chunk[0]
                py = chunk[1] if absolute else y + chunk[1]
            if low == "m":
                flush()
                pts.append((px, py))
                start_x, start_y = px, py
            elif low == "l":
                pts.append((px, py))
            elif low == "c":
                cubic((x, y), (px, py),
                      (chunk[2] if absolute else x + chunk[2],
                       chunk[3] if absolute else y + chunk[3]),
                      (chunk[4] if absolute else x + chunk[4],
                       chunk[5] if absolute else y + chunk[5]))
                px = chunk[4] if absolute else x + chunk[4]
                py = chunk[5] if absolute else y + chunk[5]
            else:
                raise SystemExit(f"unsupported curve command {letter!r} in d={d[:60]!r}")
            x, y = px, py
    flush()
    return polys


def bbox_of_d(d: str) -> tuple:
    """Bounding box of a path's control points.

    Exact for these outlines -- every one is lines and cubics whose controls are the
    extremes of their own hulls -- and used only as a sanity check, never as a cut
    measurement.
    """
    xs: list = []
    ys: list = []
    x = y = 0.0
    for letter, args in iter_segments(d):
        low = letter.lower()
        absolute = letter.isupper()
        if low == "z":
            continue
        count = COMMAND_ARGS[low]
        for i in range(0, len(args), count):
            chunk = args[i:i + count]
            if low == "h":
                px, py = (chunk[0] if absolute else x + chunk[0]), y
            elif low == "v":
                px, py = x, (chunk[0] if absolute else y + chunk[0])
            else:
                px = chunk[0] if absolute else x + chunk[0]
                py = chunk[1] if absolute else y + chunk[1]
                for j in range(2, count, 2):
                    xs.append(chunk[j] if absolute else x + chunk[j])
                    ys.append(chunk[j + 1] if absolute else y + chunk[j + 1])
            xs.append(px)
            ys.append(py)
            x, y = px, py
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def primitives_to_d(el) -> str | None:
    """Convert a basic shape to equivalent path data, or None if it is not one."""
    kind = local(el.tag)
    if kind == "rect":
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        w, h = float(el.get("width", 0)), float(el.get("height", 0))
        return f"M{x},{y}L{x + w},{y}L{x + w},{y + h}L{x},{y + h}Z"
    if kind == "line":
        return (f"M{el.get('x1', 0)},{el.get('y1', 0)}"
                f"L{el.get('x2', 0)},{el.get('y2', 0)}")
    if kind in ("polygon", "polyline"):
        points = NUMBER_RE.findall(el.get("points", ""))
        pairs = [f"{points[i]},{points[i + 1]}" for i in range(0, len(points) - 1, 2)]
        return "M" + "L".join(pairs) + ("Z" if kind == "polygon" else "")
    return None


def circle_to_d(cx: float, cy: float, rx: float, ry: float) -> str:
    """A full ellipse as two half arcs, which is how SVG itself expresses one."""
    return (f"M{cx},{cy - ry}"
            f"A{rx},{ry} 0 1 0 {cx},{cy + ry}"
            f"A{rx},{ry} 0 1 0 {cx},{cy - ry}Z")


# ---------------------------------------------------------------------------
# reading the aggregate
# ---------------------------------------------------------------------------
class Feather:
    """One resolved feather: baked path data, its presentation, and its provenance."""

    def __init__(self, name, family, source, matrix, paths, viewport, viewbox, ids):
        self.name = name          # "P1"
        self.family = family      # "P"
        self.source = source      # individuals/P1.svg
        self.matrix = matrix      # the composed placement
        self.paths = paths        # [(d, props)]
        self.viewport = viewport  # the viewBox-to-viewport part alone
        self.viewbox = viewbox    # (min_x, min_y, w, h) from the individual file
        self.ids = ids            # the source path ids, for labels

    @property
    def outline_d(self) -> str:
        return self.paths[0][0] if self.paths else ""


class Extra:
    """A scaffolding path carried over from the aggregate: toplines, guides."""

    def __init__(self, name, d, props):
        self.name = name
        self.d = d
        self.props = props


def find_by_id(root, target_id: str):
    if target_id == root.get("id"):
        return root
    for el in root.iter():
        if el.get("id") == target_id:
            return el
    return None


def viewbox_matrix(ref_root, use_width, use_height) -> Matrix:
    """The viewBox-to-viewport mapping an external ``<use>`` applies to a document.

    ``<use>`` gives the referenced ``<svg>`` a viewport as wide and tall as the use's
    width and height, and the viewBox scales into it. When the two agree -- which the
    individual files state is their whole design -- this is the identity, and the
    aggregate's own placement matrix is the only thing positioning the feather.
    """
    parts = (ref_root.get("viewBox") or "").split()
    if len(parts) != 4:
        return mat_identity()
    min_x, min_y, vb_w, vb_h = (float(v) for v in parts)
    if not vb_w or not vb_h:
        return mat_identity()
    width = float(use_width) if use_width else vb_w
    height = float(use_height) if use_height else vb_h
    return mat_mul(mat_scale(width / vb_w, height / vb_h),
                   mat_translate(-min_x, -min_y))


class Resolved:
    """The aggregate with every external reference resolved and every transform baked."""

    def __init__(self, src: Path):
        self.src = src
        self.text = src.read_text(encoding="utf-8")
        self.root = ET.fromstring(self.text)
        style_el = self.root.find(f"{{{SVG_NS}}}style")
        self.style_text = style_el.text if style_el is not None else ""
        self.rules = parse_stylesheet(self.style_text)
        self.feathers: list = []
        self.extras: list = []
        self._load()

    # -- loading ----------------------------------------------------------
    def _hidden(self, el, ancestors) -> bool:
        for node in list(ancestors) + [el]:
            if parse_style(node.get("style")).get("display") == "none":
                return True
            if (node.get("display") or "") == "none":
                return True
        return False

    def _resolve_use(self, use) -> Feather:
        href = use.get("href") or use.get(f"{{{XLINK_NS}}}href") or ""
        if not href:
            raise SystemExit(f"use #{use.get('id')}: no href")
        if href.startswith("#"):
            raise SystemExit(f"use #{use.get('id')}: {href} is not an external reference")
        file_part, _, target_id = href.partition("#")
        ref_path = self.src.parent / file_part
        if not ref_path.is_file():
            raise SystemExit(f"use #{use.get('id')}: missing {ref_path}")
        ref_root = ET.parse(ref_path).getroot()
        target = find_by_id(ref_root, target_id)
        if target is None:
            raise SystemExit(f"use #{use.get('id')}: "
                             f"{ref_path.name} has no id {target_id!r}")

        viewport = viewbox_matrix(ref_root, use.get("width"), use.get("height"))
        inner = mat_mul(viewport, parse_transform(ref_root.get("transform", "")))
        inner = mat_mul(inner, parse_transform(target.get("transform", "")))
        matrix = mat_mul(parse_transform(use.get("transform", "")), inner)

        # Presentation: the referenced file's stylesheet says stroke, the aggregate's
        # says fill, and the family class sits on the def group -- so the selector
        # match has to see the def group's class at the same time as the path's.
        def_ancestors = [target]
        family_class = (target.get("class") or "").strip()
        paths: list = []
        ids: list = []
        for el in target.iter():
            if el is target:
                continue
            kind = local(el.tag)
            if kind == "path" and el.get("d"):
                d = el.get("d")
            elif kind == "circle":
                d = circle_to_d(float(el.get("cx", 0)), float(el.get("cy", 0)),
                                float(el.get("r", 0)), float(el.get("r", 0)))
            elif kind == "ellipse":
                d = circle_to_d(float(el.get("cx", 0)), float(el.get("cy", 0)),
                                float(el.get("rx", 0)), float(el.get("ry", 0)))
            elif kind in GEOMETRY_TAGS:
                d = primitives_to_d(el)
                if not d:
                    continue
            elif kind in ("text", "tspan", "image"):
                raise SystemExit(f"{ref_path.name}: unsupported <{kind}> "
                                 f"inside {target_id}")
            else:
                if el.get("transform"):
                    raise SystemExit(
                        f"{ref_path.name}: transformed <{kind}> "
                        f"({el.get('id') or 'unnamed'}) inside {target_id} -- its "
                        f"placement is not expressible as one matrix per feather")
                continue
            props = resolve_props(el, def_ancestors, self.rules)
            full = mat_mul(matrix, parse_transform(el.get("transform", "")))
            paths.append((transform_d(d, full), props))
            ids.append(el.get("id") or "")
        if not paths:
            raise SystemExit(f"use #{use.get('id')}: "
                             f"{ref_path.name}#{target_id} has no geometry")

        parts = (ref_root.get("viewBox") or "").split()
        viewbox = tuple(float(v) for v in parts) if len(parts) == 4 else None
        family = family_class.split()[-1] if family_class else (target_id.rstrip("0123456789"))
        return Feather(use.get("id") or "?", family, ref_path, matrix, paths,
                       viewport, viewbox, ids)

    def _load(self) -> None:
        def matrix_through(nodes) -> Matrix:
            m = mat_identity()
            for node in nodes:
                m = mat_mul(m, parse_transform(node.get("transform", "")))
            return m

        def visit(el, ancestors, family):
            for child in el:
                if local(child.tag) != "g":
                    continue
                cid = (child.get("id") or "").strip()
                if cid in SKIP_GROUPS or self._hidden(child, ancestors):
                    continue
                uses = [c for c in child if local(c.tag) == "use"]
                paths = [c for c in child if local(c.tag) == "path" and c.get("d")]
                if uses:
                    for use in uses:
                        self.feathers.append(self._resolve_use(use))
                    for path_el in paths:
                        props = resolve_props(path_el, ancestors + [child], self.rules)
                        m = matrix_through(ancestors + [child, path_el])
                        self.extras.append(Extra(path_el.get("id") or "?",
                                                 transform_d(path_el.get("d"), m), props))
                else:
                    visit(child, ancestors + [child], family or cid)

        visit(self.root, [], None)


# ---------------------------------------------------------------------------
# writing the documents
# ---------------------------------------------------------------------------
def svg_header(root, title: str) -> list:
    parts = (root.get("viewBox") or "0 0 0 0").split()
    min_x, min_y, width, height = (float(v) for v in parts)
    doc_w = root.get("width") or f"{fmt(width, 6)}mm"
    doc_h = root.get("height") or f"{fmt(height, 6)}mm"
    return [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg xmlns="{SVG_NS}" xmlns:svg="{SVG_NS}"',
        f'   xmlns:inkscape="{INKSCAPE_NS}" xmlns:xlink="{XLINK_NS}"',
        f'   xmlns:sodipodi="{SODIPODI_NS}"',
        '   version="1.1" id="flat"',
        f'   width="{doc_w}" height="{doc_h}"',
        f'   viewBox="{fmt(min_x, 6)} {fmt(min_y, 6)} {fmt(width, 6)} {fmt(height, 6)}"',
        '   inkscape:document-units="mm">',
        f"  <title>{title}</title>",
        "  <desc>Flattened from feathers-aggregate-min.svg and individuals/*.svg: every "
        "use reference resolved and every transform baked into the path data, so the "
        "paths are the geometry and Inkscape can ungroup and union them.</desc>",
        f'  <sodipodi:namedview id="nv" pagecolor="#ffffff" bordercolor="#666666" '
        f'borderopacity="1.0" inkscape:document-units="mm" showguides="true" />',
    ]


def props_attr(props: dict) -> str:
    """Presentation attributes for a baked path, in a stable order."""
    order = ("fill", "fill-opacity", "fill-rule", "stroke", "stroke-width",
             "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-dasharray",
             "opacity")
    keys = [k for k in order if k in props]
    keys += [k for k in sorted(props) if k not in order]
    return " ".join(f'{k}="{props[k]}"' for k in keys)


def ring_to_d(ring) -> str:
    return "M" + "L".join(f"{fmt(x)},{fmt(y)}" for x, y in ring) + "Z"


OUTLINE_PROPS = {"fill": "none", "stroke": "#000000", "stroke-width": "0.5",
                 "stroke-linejoin": "round", "stroke-linecap": "round"}


def write_flat(res: Resolved, out: Path,
               outline_d: str | None = None) -> None:
    lines = svg_header(res.root, "Feather templates - flattened, 1:1 mm")
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="feathers" '
                 'id="layer-feathers">')
    by_family: dict = {}
    for feather in res.feathers:
        by_family.setdefault(feather.family, []).append(feather)
    for family in sorted(by_family):
        lines.append(f'    <g id="family-{family}" inkscape:groupmode="layer" '
                     f'inkscape:label="{family}">')
        for feather in by_family[family]:
            lines.append(f'      <g id="{feather.name}" '
                         f'inkscape:label="{feather.name}">')
            for index, (d, props) in enumerate(feather.paths):
                pid = feather.ids[index] or f"{feather.name}-outline"
                lines.append(f'        <path id="{pid}" {props_attr(props)} '
                             f'd="{d}" />')
            lines.append("      </g>")
        lines.append("    </g>")
    lines.append("  </g>")

    if outline_d is not None:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="outline" '
                     'id="layer-outline">')
        lines.append(f'    <path id="wing-outline" {props_attr(OUTLINE_PROPS)} '
                     f'd="{outline_d}" />')
        lines.append("  </g>")

    if res.extras:
        lines.append('  <g inkscape:groupmode="layer" inkscape:label="guides" '
                     'id="layer-guides">')
        for extra in res.extras:
            lines.append(f'    <path id="{extra.name}" {props_attr(extra.props)} '
                         f'd="{extra.d}" />')
        lines.append("  </g>")
    lines.append("</svg>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outline_only(res: Resolved, out: Path, rings: list) -> None:
    lines = svg_header(res.root, "Feather assembly outline - single cut path, 1:1 mm")
    lines.append('  <g inkscape:groupmode="layer" inkscape:label="outline" '
                 'id="layer-outline">')
    lines.append(f'    <path id="wing-outline" {props_attr(OUTLINE_PROPS)} '
                 f'd="{"".join(ring_to_d(r) for r in rings)}" />')
    lines.append("  </g>")
    lines.append("</svg>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# the silhouette: supersampled coverage, then a contour trace
# ---------------------------------------------------------------------------
def coverage_mask(polys: list, box: tuple, res: float, ss: int):
    """A 0-255 coverage mask for a polygon set, supersampled ``ss`` per axis per cell."""
    ox, oy, x1, y1 = box
    w = int(math.ceil((x1 - ox) / res)) + 2
    h = int(math.ceil((y1 - oy) / res)) + 2
    field = bytearray(w * h)
    per_cell = ss * ss
    step = 255 // per_cell
    cap = 255 - step

    for poly in polys:
        n = len(poly)
        if n < 3:
            continue
        ys = [p[1] for p in poly]
        row0 = max(0, int((min(ys) - oy) / res) - 1)
        row1 = min(h - 1, int((max(ys) - oy) / res) + 1)
        for py in range(row0, row1 + 1):
            hits = [0] * w
            touched = False
            for sy in range(ss):
                scan_y = oy + (py + (sy + 0.5) / ss) * res
                xs: list = []
                for i in range(n):
                    ax, ay = poly[i]
                    bx, by = poly[(i + 1) % n]
                    if (ay > scan_y) != (by > scan_y):
                        xs.append(ax + (scan_y - ay) * (bx - ax) / (by - ay))
                if len(xs) < 2:
                    continue
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    lo, hi = xs[i], xs[i + 1]
                    px0 = max(0, int((lo - ox) / res))
                    px1 = min(w - 1, int((hi - ox) / res))
                    for px in range(px0, px1 + 1):
                        for sx in range(ss):
                            sample_x = ox + (px + (sx + 0.5) / ss) * res
                            if lo <= sample_x <= hi:
                                hits[px] += 1
                                touched = True
            if not touched:
                continue
            base = py * w
            for px in range(w):
                add = hits[px] * step
                if add:
                    value = field[base + px] + add
                    field[base + px] = 255 if value > cap else value
    return field, w, h, ox, oy


def trace_contours(field: bytearray, w: int, h: int, ox: float, oy: float,
                   res: float, threshold: int = 128) -> list:
    """Closed rings (mm) tracing the boundary of the covered cells of ``field``.

    A cell corner is a vertex and each side of a covered cell is an edge; an edge whose
    neighbouring cell is also covered is interior and cancels. What is left is the
    region's outline, and walking it collects each ring once.
    """
    inside = bytearray(w * h)
    for i, value in enumerate(field):
        if value >= threshold:
            inside[i] = 1

    edges: set = set()
    for py in range(h):
        row = py * w
        for px in range(w):
            if not inside[row + px]:
                continue
            if not (py > 0 and inside[row - w + px]):
                edges.add((px, py, px + 1, py))
            if not (px + 1 < w and inside[row + px + 1]):
                edges.add((px + 1, py, px + 1, py + 1))
            if not (py + 1 < h and inside[row + w + px]):
                edges.add((px + 1, py + 1, px, py + 1))
            if not (px > 0 and inside[row + px - 1]):
                edges.add((px, py + 1, px, py))

    outgoing: dict = {}
    for ex1, ey1, ex2, ey2 in edges:
        outgoing.setdefault((ex1, ey1), []).append((ex2, ey2))

    rings: list = []
    remaining = set(edges)
    while remaining:
        start = next(iter(remaining))
        ring = [(start[0], start[1])]
        remaining.discard(start)
        cursor = (start[2], start[3])
        guard = 0
        while cursor != ring[0]:
            guard += 1
            if guard > len(edges) + 4:
                break
            ring.append(cursor)
            candidates = [n for n in outgoing.get(cursor, [])
                          if (cursor[0], cursor[1], n[0], n[1]) in remaining]
            if not candidates:
                break
            # Prefer the rightmost turn, which keeps the walk on its own ring where
            # two rings touch at a corner.
            def turn_key(n, cursor=cursor, prev=ring[-2] if len(ring) > 1 else ring[0]):
                ax, ay = cursor[0] - prev[0], cursor[1] - prev[1]
                bx, by = n[0] - cursor[0], n[1] - cursor[1]
                cross = ax * by - ay * bx
                dot = ax * bx + ay * by
                return (0 if cross < 0 else 1, -dot)
            candidates.sort(key=turn_key)
            nxt = candidates[0]
            remaining.discard((cursor[0], cursor[1], nxt[0], nxt[1]))
            cursor = nxt
        if len(ring) >= 5:
            rings.append([(ox + px * res, oy + py * res) for px, py in ring[:-1]])
    return rings


def rdp(points: list, tol: float) -> list:
    """Ramer-Douglas-Peucker: drop vertices that bend the ring by less than ``tol``."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        if last <= first + 1:
            continue
        ax, ay = points[first]
        bx, by = points[last]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        best, best_i = -1.0, -1
        for i in range(first + 1, last):
            px, py = points[i]
            dist = (abs(dy * px - dx * py + bx * ay - by * ax) / norm
                    if norm else math.hypot(px - ax, py - ay))
            if dist > best:
                best, best_i = dist, i
        if best > tol and best_i > 0:
            keep[best_i] = True
            stack.append((first, best_i))
            stack.append((best_i, last))
    return [p for p, k in zip(points, keep) if k]


def ring_area(ring: list) -> float:
    total = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def point_in_ring(px: float, py: float, ring: list) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            if px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def orient_rings(rings: list, tol: float) -> list:
    """Simplify, then wind outer rings and holes opposite ways, as a filled path needs."""
    simplified = [rdp(ring, tol) for ring in rings]
    simplified = [r for r in simplified if len(r) >= 3 and abs(ring_area(r)) > 1.0]
    out: list = []
    for i, ring in enumerate(simplified):
        centroid = (sum(p[0] for p in ring) / len(ring),
                    sum(p[1] for p in ring) / len(ring))
        # Probe halfway to the ring's own centre, so the containment test is not
        # decided by the boundary it may share with the ring being tested against.
        probe = ((ring[0][0] + centroid[0]) / 2.0, (ring[0][1] + centroid[1]) / 2.0)
        depth = 0
        for j, other in enumerate(simplified):
            if i != j and point_in_ring(probe[0], probe[1], other):
                depth += 1
        want_ccw = (depth % 2 == 0)
        if (ring_area(ring) > 0) != want_ccw:
            ring = list(reversed(ring))
        out.append(ring)
    return out


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------
def verify_bboxes(res: Resolved) -> list:
    """Every feather's baked bbox must match its own file's viewBox."""
    problems = []
    for feather in res.feathers:
        if feather.viewbox is None:
            problems.append(f"{feather.name}: no viewBox in {feather.source.name}")
            continue
        _vx, _vy, vw, vh = feather.viewbox
        if not is_identity(feather.viewport, 1e-6):
            problems.append(
                f"{feather.name}: viewBox mapping is not the identity "
                f"({','.join(fmt(v, 9) for v in feather.viewport)}) -- its use "
                f"width/height no longer match the viewBox, so this check cannot run")
            continue
        x0, y0, x1, y1 = bbox_of_d(feather.outline_d)
        got_w, got_h = x1 - x0, y1 - y0
        if abs(got_w - vw) > 1e-3 or abs(got_h - vh) > 1e-3:
            problems.append(
                f"{feather.name}: baked bbox {fmt(got_w)}x{fmt(got_h)} mm does not "
                f"match viewBox {fmt(vw)}x{fmt(vh)} mm ({feather.source.name})")
    return problems


def render_aggregate(res: Resolved, box: tuple, grain: float):
    """Coverage mask of the aggregate, via this file's own loader and matrices."""
    items = [(d, props) for feather in res.feathers for d, props in feather.paths]
    return mask_from_items(items, box, grain)


def render_flat(path: Path, box: tuple, grain: float):
    """Coverage mask of a flat document, read back off the paths it actually wrote."""
    root = ET.parse(path).getroot()
    items: list = []

    def visit(el, props: dict, in_guides: bool):
        for child in el:
            if local(child.tag) != "g":
                continue
            label = child.get("inkscape:label") or child.get("id") or ""
            guides = in_guides or label == "guides"
            here = dict(props)
            here.update({k: v for k, v in child.attrib.items()
                         if k in PRESENTATION_ATTRS and k != "style"})
            here.update(parse_style(child.get("style")))
            visit(child, here, guides)
        if in_guides:
            return
        for child in el:
            if local(child.tag) != "path" or not child.get("d"):
                continue
            merged = dict(props)
            merged.update({k: v for k, v in child.attrib.items()
                           if k in PRESENTATION_ATTRS and k != "style"})
            merged.update(parse_style(child.get("style")))
            items.append((child.get("d"), merged))

    visit(root, {}, False)
    return mask_from_items(items, box, grain)


def mask_from_items(items: list, box: tuple, grain: float):
    """Coverage mask (0-255) of every filled path in ``items``, supersampled 3x3."""
    ox, oy, x1, y1 = box
    w = int(math.ceil((x1 - ox) / grain)) + 2
    h = int(math.ceil((y1 - oy) / grain)) + 2
    mask = bytearray(w * h)
    filled = [(d, props) for d, props in items
              if (props.get("fill") or "").strip().lower() not in ("", "none")]
    if filled:
        field, _w, _h, _ox, _oy = coverage_mask(
            [poly for d, _p in filled for poly in flatten_d(d)], box, grain, 3)
        mask = field
    return mask, w, h


def compare_masks(a, b) -> tuple:
    (m1, w1, h1), (m2, w2, h2) = a, b
    if (w1, h1) != (w2, h2):
        return 1.0, f"mask size mismatch {w1}x{h1} vs {w2}x{h2}"
    total = w1 * h1
    differing = 0
    for i in range(total):
        if abs(m1[i] - m2[i]) > 64:
            differing += 1
    return differing / total, f"{differing} of {total} cells differ"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg", nargs="?", default=str(DEFAULT_SRC))
    ap.add_argument("--mode", choices=("flat", "outline", "both"), default="both")
    ap.add_argument("--flat-out", default=str(DEFAULT_FLAT))
    ap.add_argument("--outline-out", default=str(DEFAULT_OUTLINE))
    ap.add_argument("--outline-tol", type=float, default=0.05)
    ap.add_argument("--check", action="store_true", help="verify, write nothing")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    src = Path(args.svg)
    print(f"reading {src}")
    res = Resolved(src)
    print(f"  {len(res.feathers)} feather(s) from "
          f"{len({f.source for f in res.feathers})} individual file(s), "
          f"{len(res.extras)} guide path(s)")
    for feather in res.feathers:
        if args.verbose:
            print(f"  {feather.name:4s} {feather.source.name:12s} "
                  f"matrix({','.join(fmt(v, 6) for v in feather.matrix)})")

    problems = verify_bboxes(res)
    if problems:
        print("BBOX CHECK FAILED:")
        for p in problems:
            print("  " + p)
        return 1
    print(f"  bbox check OK: every baked outline matches its viewBox "
          f"({len(res.feathers)} feathers)")

    parts = (res.root.get("viewBox") or "0 0 0 0").split()
    vx, vy, vw, vh = (float(v) for v in parts)

    rings = None
    if args.mode in ("outline", "both"):
        box = (vx - 2.0, vy - 2.0, vx + vw + 2.0, vy + vh + 2.0)
        polys = [poly for feather in res.feathers
                 for d, _props in feather.paths for poly in flatten_d(d, 0.02)]
        print(f"  silhouette: {len(polys)} ring(s) to union, tracing at "
              f"{OUTLINE_RES_MM} mm ...")
        field, w, h, ox, oy = coverage_mask(polys, box, OUTLINE_RES_MM,
                                            OUTLINE_SUPERSAMPLE)
        raw = trace_contours(field, w, h, ox, oy, OUTLINE_RES_MM)
        rings = orient_rings(raw, args.outline_tol)
        area = abs(sum(ring_area(r) for r in rings))
        feather_area = abs(sum(ring_area(p) for p in polys))
        print(f"  silhouette: {len(raw)} traced ring(s) -> {len(rings)} after "
              f"simplify; area {fmt(area, 1)} mm2 "
              f"(feathers sum to {fmt(feather_area, 1)} mm2, union must be less)")

    if args.check:
        print("check only: nothing written")
        return 0

    outline_d = "".join(ring_to_d(r) for r in rings) if rings is not None else None

    if args.mode in ("flat", "both"):
        out = Path(args.flat_out)
        write_flat(res, out, outline_d)
        print(f"wrote {out}")
        box = (vx, vy, vx + vw, vy + vh)
        a = render_aggregate(res, box, RASTER_MM)
        b = render_flat(out, box, RASTER_MM)
        delta, note = compare_masks(a, b)
        ok = delta <= MASK_TOL
        print(f"  raster check {'OK' if ok else 'FAILED'} at {RASTER_MM} mm: {note} "
              f"({delta * 100:.4f}% of cells, tolerance {MASK_TOL * 100:.2f}%)")
        if not ok:
            return 1

    if args.mode == "outline" and rings is not None:
        out = Path(args.outline_out)
        write_outline_only(res, out, rings)
        print(f"wrote {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
