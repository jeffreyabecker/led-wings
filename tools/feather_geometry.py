"""Geometry helpers for converting individual feather SVGs into printable PDF templates.

Units are millimetres throughout: every individual feather SVG is authored so that
one user unit maps to one millimetre (width="NN.NNmm" with a matching viewBox width).
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
COMMAND_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]")
PARAM_COUNT = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}

# ---------------------------------------------------------------------------
# affine matrices, stored as (a, b, c, d, e, f) meaning
#     x' = a*x + c*y + e
#     y' = b*x + d*y + f
# ---------------------------------------------------------------------------
Matrix = tuple


def mat_identity() -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m1: Matrix, m2: Matrix) -> Matrix:
    """Return m1 * m2, i.e. the transform that applies m2 first, then m1."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def mat_apply(m: Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def mat_determinant(m: Matrix) -> float:
    a, b, c, d = m[:4]
    return a * d - b * c


def mat_mean_scale(m: Matrix) -> float:
    """Geometric-mean linear scale factor of a matrix (used to map stroke widths)."""
    return math.sqrt(abs(mat_determinant(m))) or 1.0


def mat_translate(tx: float, ty: float) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def mat_scale(sx: float, sy: float) -> Matrix:
    return (sx, 0.0, 0.0, sy, 0.0, 0.0)


def mat_rotate(deg: float, cx: float = 0.0, cy: float = 0.0) -> Matrix:
    rad = math.radians(deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    rot = (cos_r, sin_r, -sin_r, cos_r, 0.0, 0.0)
    if cx or cy:
        return mat_mul(mat_mul(mat_translate(cx, cy), rot), mat_translate(-cx, -cy))
    return rot


def parse_transform(text: str) -> Matrix:
    """Parse an SVG transform attribute list (matrix/translate/scale/rotate)."""
    result = mat_identity()
    for name, raw_args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", text or ""):
        args = [float(v) for v in NUMBER_RE.findall(raw_args)]
        name = name.strip()
        if name == "matrix" and len(args) == 6:
            m = tuple(args)
        elif name == "translate":
            m = mat_translate(args[0], args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            m = mat_scale(args[0], args[1] if len(args) > 1 else args[0])
        elif name == "rotate":
            cx, cy = (args[1], args[2]) if len(args) > 2 else (0.0, 0.0)
            m = mat_rotate(args[0], cx, cy)
        else:
            raise ValueError(f"unsupported transform: {name}({raw_args})")
        result = mat_mul(result, m)
    return result


def transform_path(path: "Path", m: Matrix) -> "Path":
    """Return a new Path with every coordinate mapped through m."""
    if m == mat_identity():
        return path
    out: list[list] = []
    for sub in path.subpaths:
        new_sub = []
        for seg in sub:
            op = seg[0]
            if op == "Z":
                new_sub.append(("Z",))
            else:
                pts = [
                    mat_apply(m, seg[i], seg[i + 1]) for i in range(1, len(seg), 2)
                ]
                flat = [op]
                for x, y in pts:
                    flat.extend((x, y))
                new_sub.append(tuple(flat))
        out.append(new_sub)
    return Path(out, closed=path.closed)


# ---------------------------------------------------------------------------
# path parsing
# ---------------------------------------------------------------------------
@dataclass
class Path:
    subpaths: list[list[tuple]] = field(default_factory=list)
    closed: bool = False

    def is_empty(self) -> bool:
        return not any(sub for sub in self.subpaths)


def _tokenize(d: str) -> list:
    tokens: list = []
    i, n = 0, len(d)
    while i < n:
        ch = d[i]
        if ch in " ,\t\r\n":
            i += 1
            continue
        if ch.isalpha():
            tokens.append(ch)
            i += 1
            continue
        m = NUMBER_RE.match(d, i)
        if not m:
            raise ValueError(f"bad path token at {i}: {d[i:i + 24]!r}")
        tokens.append(float(m.group(0)))
        i = m.end()
    return tokens


def _arc_to_curves(x0, y0, rx, ry, phi_deg, large_arc, sweep, x1, y1) -> list:
    """Convert an SVG elliptical arc to a list of cubic segments (absolute coords)."""
    if rx == 0 or ry == 0:
        return [("L", x1, y1)]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg % 360.0)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x0 - x1) / 2.0, (y0 - y1) / 2.0
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1.0:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(num / den, 0.0))
    if large_arc == sweep:
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cos_p * cxp - sin_p * cyp + (x0 + x1) / 2.0
    cy = sin_p * cxp + cos_p * cyp + (y0 + y1) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        norm = math.hypot(ux, uy) * math.hypot(vx, vy)
        val = max(-1.0, min(1.0, dot / norm)) if norm else 1.0
        ang = math.acos(val)
        if ux * vy - uy * vx < 0:
            ang = -ang
        return ang

    theta1 = angle(1.0, 0.0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep and dtheta < 0:
        dtheta += 2 * math.pi

    n_seg = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2.0))))
    delta = dtheta / n_seg
    t = 4.0 / 3.0 * math.tan(delta / 4.0)
    segments = []
    theta = theta1
    for _ in range(n_seg):
        cos1, sin1 = math.cos(theta), math.sin(theta)
        cos2, sin2 = math.cos(theta + delta), math.sin(theta + delta)
        e1x = cos_p * rx * cos1 - sin_p * ry * sin1 + cx
        e1y = sin_p * rx * cos1 + cos_p * ry * sin1 + cy
        e2x = cos_p * rx * cos2 - sin_p * ry * sin2 + cx
        e2y = sin_p * rx * cos2 + cos_p * ry * sin2 + cy
        d1x = -cos_p * rx * sin1 - sin_p * ry * cos1
        d1y = -sin_p * rx * sin1 + cos_p * ry * cos1
        d2x = -cos_p * rx * sin2 - sin_p * ry * cos2
        d2y = -sin_p * rx * sin2 + cos_p * ry * cos2
        segments.append(
            (
                "C",
                e1x + t * d1x,
                e1y + t * d1y,
                e2x - t * d2x,
                e2y - t * d2y,
                e2x,
                e2y,
            )
        )
        theta += delta
    return segments


def parse_path(d: str) -> Path:
    """Parse SVG path data into absolute M/L/C/Z segments.

    Output shape: subpaths is a list of segments, each ("M", x, y), ("L", x, y) or
    ("C", x1, y1, x2, y2, x, y); ("Z",) closes back to the subpath start.
    """
    tokens = _tokenize(d)
    subpaths: list[list[tuple]] = []
    current: list[tuple] = []
    i, n = 0, len(tokens)
    cmd = None
    x = y = 0.0
    start_x = start_y = 0.0
    prev_c2 = None
    prev_q1 = None
    closed_any = False

    def flush():
        nonlocal current
        if current:
            subpaths.append(current)
            current = []

    while i < n:
        tok = tokens[i]
        if isinstance(tok, str):
            cmd = tok
            i += 1
            if cmd in "Zz":
                if current:
                    current.append(("Z",))
                    closed_any = True
                x, y = start_x, start_y
                prev_c2 = prev_q1 = None
                continue
        elif cmd is None:
            raise ValueError("path data does not start with a command")

        upper = cmd.upper()
        relative = cmd.islower()
        if upper in "ML":
            x1, y1 = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if relative:
                x1, y1 = x + x1, y + y1
            if upper == "M":
                flush()
                current.append(("M", x1, y1))
                start_x, start_y = x1, y1
                cmd = "l" if relative else "L"
            else:
                current.append(("L", x1, y1))
            x, y = x1, y1
            prev_c2 = prev_q1 = None
            continue
        if upper == "H":
            x1 = float(tokens[i])
            i += 1
            if relative:
                x1 = x + x1
            current.append(("L", x1, y))
            x = x1
            prev_c2 = prev_q1 = None
            continue
        if upper == "V":
            y1 = float(tokens[i])
            i += 1
            if relative:
                y1 = y + y1
            current.append(("L", x, y1))
            y = y1
            prev_c2 = prev_q1 = None
            continue
        if upper == "C":
            vals = [float(v) for v in tokens[i:i + 6]]
            i += 6
            x1, y1, x2, y2, x3, y3 = vals
            if relative:
                x1, y1, x2, y2, x3, y3 = (
                    x + x1, y + y1, x + x2, y + y2, x + x3, y + y3,
                )
            current.append(("C", x1, y1, x2, y2, x3, y3))
            prev_c2 = (x2, y2)
            x, y = x3, y3
            prev_q1 = None
            continue
        if upper == "S":
            vals = [float(v) for v in tokens[i:i + 4]]
            i += 4
            x2, y2, x3, y3 = vals
            if relative:
                x2, y2, x3, y3 = x + x2, y + y2, x + x3, y + y3
            if prev_c2 is None:
                x1, y1 = x, y
            else:
                x1, y1 = 2 * x - prev_c2[0], 2 * y - prev_c2[1]
            current.append(("C", x1, y1, x2, y2, x3, y3))
            prev_c2 = (x2, y2)
            x, y = x3, y3
            prev_q1 = None
            continue
        if upper in "QT":
            if upper == "Q":
                vals = [float(v) for v in tokens[i:i + 4]]
                i += 4
                qx, qy, x3, y3 = vals
                if relative:
                    qx, qy, x3, y3 = x + qx, y + qy, x + x3, y + y3
                prev_q1 = (qx, qy)
            else:
                vals = [float(v) for v in tokens[i:i + 2]]
                i += 2
                x3, y3 = vals
                if relative:
                    x3, y3 = x + x3, y + y3
                if prev_q1 is None:
                    qx, qy = x, y
                else:
                    qx, qy = 2 * x - prev_q1[0], 2 * y - prev_q1[1]
                prev_q1 = (qx, qy)
            c1x, c1y = x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y)
            c2x, c2y = x3 + 2.0 / 3.0 * (qx - x3), y3 + 2.0 / 3.0 * (qy - y3)
            current.append(("C", c1x, c1y, c2x, c2y, x3, y3))
            x, y = x3, y3
            prev_c2 = None
            continue
        if upper == "A":
            vals = tokens[i:i + 7]
            i += 7
            rx, ry, rot, large, sweep, ax, ay = [float(v) for v in vals]
            if relative:
                ax, ay = x + ax, y + ay
            for seg in _arc_to_curves(x, y, rx, ry, rot, int(large), int(sweep), ax, ay):
                current.append(seg)
            x, y = ax, ay
            prev_c2 = prev_q1 = None
            continue
        raise ValueError(f"unsupported path command: {cmd}")

    flush()
    return Path(subpaths, closed=closed_any)


# ---------------------------------------------------------------------------
# flattening and bbox
# ---------------------------------------------------------------------------
def _flatten_cubic(p0, p1, p2, p3, tol, out, depth=0):
    """Adaptive subdivision; appends points after p0 up to and including p3."""
    if depth >= 24:
        out.append(p3)
        return
    x0, y0 = p0
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    ux, uy = 3 * x1 - 2 * x0 - x3, 3 * y1 - 2 * y0 - y3
    vx, vy = 3 * x2 - 2 * x3 - x0, 3 * y2 - 2 * y3 - y0
    d = max(ux * ux, vx * vx) + max(uy * uy, vy * vy)
    if d <= 16.0 * tol * tol:
        out.append(p3)
        return
    # de Casteljau split at t = 0.5
    x01, y01 = (x0 + x1) / 2, (y0 + y1) / 2
    x12, y12 = (x1 + x2) / 2, (y1 + y2) / 2
    x23, y23 = (x2 + x3) / 2, (y2 + y3) / 2
    x012, y012 = (x01 + x12) / 2, (y01 + y12) / 2
    x123, y123 = (x12 + x23) / 2, (y12 + y23) / 2
    xm, ym = (x012 + x123) / 2, (y012 + y123) / 2
    _flatten_cubic((x0, y0), (x01, y01), (x012, y012), (xm, ym), tol, out, depth + 1)
    _flatten_cubic((xm, ym), (x123, y123), (x23, y23), (x3, y3), tol, out, depth + 1)


def flatten_path(path: Path, tol: float = 0.005) -> list[list[tuple[float, float]]]:
    """Convert a Path to closed polylines of (x, y) points."""
    polys: list[list[tuple[float, float]]] = []
    for sub in path.subpaths:
        pts: list[tuple[float, float]] = []
        cx = cy = sx = sy = 0.0
        for seg in sub:
            op = seg[0]
            if op == "M":
                if len(pts) > 1:
                    polys.append(pts)
                cx = sx = seg[1]
                cy = sy = seg[2]
                pts = [(cx, cy)]
            elif op == "L":
                cx, cy = seg[1], seg[2]
                pts.append((cx, cy))
            elif op == "C":
                p0 = (cx, cy)
                p1 = (seg[1], seg[2])
                p2 = (seg[3], seg[4])
                p3 = (seg[5], seg[6])
                _flatten_cubic(p0, p1, p2, p3, tol, pts)
                cx, cy = p3
            elif op == "Z":
                if pts and (abs(pts[0][0] - cx) > 1e-9 or abs(pts[0][1] - cy) > 1e-9):
                    pts.append(pts[0])
                cx, cy = sx, sy
        if len(pts) > 1:
            polys.append(pts)
    return polys


def bbox_of_polys(polys) -> tuple[float, float, float, float]:
    xs_min = ys_min = math.inf
    xs_max = ys_max = -math.inf
    for poly in polys:
        for x, y in poly:
            xs_min = min(xs_min, x)
            xs_max = max(xs_max, x)
            ys_min = min(ys_min, y)
            ys_max = max(ys_max, y)
    if xs_min is math.inf:
        raise ValueError("empty geometry")
    return (xs_min, ys_min, xs_max, ys_max)


def expand_bbox(box, amount: float) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return (x0 - amount, y0 - amount, x1 + amount, y1 + amount)


# ---------------------------------------------------------------------------
# individual feather SVG loading
# ---------------------------------------------------------------------------
@dataclass
class Feather:
    name: str
    source: Path
    polys_right: list  # transformed geometry in the as-built (right) orientation, mm
    box: tuple  # bbox of the stroke centreline geometry
    stroke_mm: float
    declared_size_mm: tuple
    view_box: tuple

    @property
    def width(self) -> float:
        return self.box[2] - self.box[0]

    @property
    def height(self) -> float:
        return self.box[3] - self.box[1]

    @property
    def cut_box(self) -> tuple:
        """Bounding box including half the stroke width on each side."""
        return expand_bbox(self.box, self.stroke_mm / 2.0)


def load_feather(svg_path: Path) -> Feather:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ValueError(f"{svg_path.name}: unexpected root element {root.tag!r}")

    def dims(attr: str) -> float:
        raw = root.get(attr, "")
        m = NUMBER_RE.match(raw)
        if not m:
            raise ValueError(f"{svg_path.name}: cannot read {attr}={raw!r}")
        value = float(m.group(0))
        unit = raw[m.end():].strip()
        if unit not in ("mm", ""):
            raise ValueError(f"{svg_path.name}: unsupported unit in {attr}={raw!r}")
        return value

    width_mm, height_mm = dims("width"), dims("height")
    vb = [float(v) for v in NUMBER_RE.findall(root.get("viewBox", ""))]
    if len(vb) != 4:
        raise ValueError(f"{svg_path.name}: missing/invalid viewBox")

    # Find the single <path> element and accumulate every ancestor <g> transform
    # plus the path's own transform (B1-B4 carry a rotate() on the path itself).
    group = None
    path_el = None
    for child in root:
        if child.tag == f"{{{SVG_NS}}}g":
            group = child
            for grandchild in child:
                if grandchild.tag == f"{{{SVG_NS}}}path":
                    path_el = grandchild
                    break
            break
    if group is None or path_el is None:
        raise ValueError(f"{svg_path.name}: no <g><path> feather geometry found")

    matrix = parse_transform(group.get("transform", ""))
    path_matrix = parse_transform(path_el.get("transform", ""))
    matrix = mat_mul(matrix, path_matrix)
    stroke_mm = float(path_el.get("stroke-width", "0.5"))

    path = transform_path(parse_path(path_el.get("d", "")), matrix)
    polys = flatten_path(path)
    box = bbox_of_polys(polys)

    return Feather(
        name=svg_path.stem,
        source=svg_path,
        polys_right=polys,
        box=box,
        stroke_mm=stroke_mm,
        declared_size_mm=(width_mm, height_mm),
        view_box=tuple(vb),
    )
