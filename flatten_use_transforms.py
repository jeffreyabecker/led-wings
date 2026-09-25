#!/usr/bin/env python3
"""THROWAWAY: flatten <defs>/<use> transforms onto the <use> element.

In mechanical/templates/feathers-aggregate-min.svg each feather's geometry sits
in <defs> as <g id="X-def"> with a transform, and/or its <path> child carries a
transform. The placing <use href="#X-def"> carries a transform of its own.

Rendering a use applies, for every point of the referenced geometry::

    parent_group_ctm . use_transform . def_transform . inner_transform

This script folds the last three into one matrix on the <use> and deletes the
transform attributes from the def group and from every element inside it, so the
placement is expressed once, in the place it is used::

    parent_group_ctm . use_transform      (def_transform . inner_transform folded in)

The defs stay in the document; only the transforms move. Geometry is untouched,
so rendering is pixel-identical -- verified by comparing the composed matrix of
every geometry element before and after.

Editing is done by re-serialising ONLY the <use> start tags and the def start
tags, so the rest of the hand-formatted document is byte-identical.

Usage:
    python flatten_use_transforms.py --check      # report, write nothing
    python flatten_use_transforms.py -o out.svg   # write elsewhere
    python flatten_use_transforms.py              # rewrite in place
"""

import argparse
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
DEFAULT_SVG = "mechanical/templates/feathers-aggregate-min.svg"

NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TRANSFORM_RE = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")

# ---------------------------------------------------------------------------
# affine matrices, as (a, b, c, d, e, f) for the SVG convention
#     x' = a*x + c*y + e
#     y' = b*x + d*y + f
# (y is DOWN, and everything stays in that space -- no flipping here.)
# ---------------------------------------------------------------------------


def mat_mul(m1, m2):
    """m1 * m2 -- the transform that applies m2 first, then m1."""
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


def mat_apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def mat_translate(tx, ty):
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def mat_scale(sx, sy):
    return (sx, 0.0, 0.0, sy, 0.0, 0.0)


def mat_rotate(deg, cx=0.0, cy=0.0):
    rad = math.radians(deg)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    rot = (cos_r, sin_r, -sin_r, cos_r, 0.0, 0.0)
    if cx or cy:
        return mat_mul(mat_mul(mat_translate(cx, cy), rot), mat_translate(-cx, -cy))
    return rot


def parse_transform(text):
    """Parse an SVG transform attribute list (matrix/translate/scale/rotate/skew)."""
    result = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, raw_args in TRANSFORM_RE.findall(text or ""):
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
        elif name == "skewX":
            m = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
        elif name == "skewY":
            m = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise ValueError(f"unsupported transform: {name}({raw_args})")
        result = mat_mul(result, m)
    return result


def num(value):
    """A short decimal for a matrix entry, without float noise.

    repr() gives the shortest string that reads back as the same double, which is
    what we want for the geometry -- but a sum of products can land a hair off an
    exact value (0.9999999999999999 for 1, or 554.8051500000001 for 554.80515) and
    printing that noise would make the file unreadable for no gain. Only slack
    smaller than a nanometre is trimmed; everything else is transmitted exactly.
    """
    value = float(value)
    if abs(value) < 1e-12:
        return "0"
    nearest = round(value)
    if nearest and abs(value - nearest) < 1e-9:
        return repr(float(nearest))
    return repr(value)


def matrix_attr(m):
    return "matrix(" + ",".join(num(v) for v in m) + ")"


def is_identity(m):
    return m == (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# a quote-aware tag scanner, so only the tags we touch are re-serialised
# ---------------------------------------------------------------------------
ATTRIBUTE_RE = re.compile(r"([-\w:.]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.:")


def tags_with_spans(text):
    """Yield (start, end, name, attrs_text, is_close) for every start/close tag.

    A hand-rolled scan rather than a regex: attributes may contain `>`, `<` and
    quotes, so the only safe end of a tag is a `>` found outside quotes. Skipping
    comments, CDATA and processing instructions keeps their innards from being
    mistaken for tags.
    """
    i, n = 0, len(text)
    while True:
        lt = text.find("<", i)
        if lt < 0:
            return
        if text.startswith("<!--", lt):
            end = text.find("-->", lt)
            i = n if end < 0 else end + 3
            continue
        if text.startswith("<![CDATA[", lt):
            end = text.find("]]>", lt)
            i = n if end < 0 else end + 3
            continue
        i = lt + 1
        is_close = text.startswith("/", i)
        if is_close:
            i += 1
        if i >= n or (text[i] not in NAME_CHARS):
            # a stray `<` in text, or a `<?xml ... ?>` declaration
            end = text.find(">", i)
            i = n if end < 0 else end + 1
            continue
        name_start = i
        while i < n and text[i] in NAME_CHARS:
            i += 1
        name = text[name_start:i]
        attrs_start = i
        while i < n:
            ch = text[i]
            if ch in "\"'":
                i = text.find(ch, i + 1)
                if i < 0:
                    i = n
                    break
                i += 1
                continue
            if ch == ">":
                break
            i += 1
        yield lt, min(i + 1, n), name, text[attrs_start:i], is_close


def first_attr_indent(attrs_text):
    """The whitespace in front of a tag's first attribute.

    Reusing it keeps each rewritten tag looking the way the document already looks:
    a def group inside `<defs>` is indented further than a top-level `<use>`, and a
    one-line tag simply comes back as one line.
    """
    m = ATTRIBUTE_RE.search(attrs_text)
    if not m:
        return ""
    line_start = attrs_text.rfind("\n", 0, m.start()) + 1
    return attrs_text[line_start:m.start()]


def set_attrs(attrs_text, updates, drops):
    """Rebuild a start-tag attribute string with `updates` applied and `drops` removed.

    Attributes keep their original order at the tag's own indentation, and an
    updated attribute keeps its slot. Attributes the tag did not have go last, so a
    `style` already present stays where the document had it. Values come back
    double-quoted, one to a line, which is how the document is written.
    """
    indent = first_attr_indent(attrs_text)
    pieces = []
    seen = set()
    for m in ATTRIBUTE_RE.finditer(attrs_text):
        name, raw = m.group(1), m.group(2)[1:-1]
        if name in updates:            # an explicit update outranks a drop
            seen.add(name)
            pieces.append(f'{name}="{updates[name]}"')
        elif name not in drops:
            pieces.append(f'{name}="{raw}"')
    for name, value in updates.items():
        # Only `seen` matters here: an update with no existing attribute to replace
        # is being *added*, which is what an update means. `drops` says which
        # attributes to take away, not which to withhold.
        if name not in seen:
            pieces.append(f'{name}="{value}"')
    return "".join("\n" + indent + p for p in pieces)


def id_of(attrs_text):
    """The plain `id` of a start tag, or None. `inkscape:id`-style names do not match."""
    for m in ATTRIBUTE_RE.finditer(attrs_text):
        if m.group(1) == "id":
            return m.group(2)[1:-1]
    return None


# ---------------------------------------------------------------------------
# the document walk
# ---------------------------------------------------------------------------
def local(tag):
    return tag.split("}")[-1]


def read_text(path):
    """Read the document with its newlines intact (no universal-newline translation)."""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path, text):
    """Write with `newline=""` so the document keeps the LF endings it came with.

    Python's default text mode turns every "\\n" into os.linesep, which on Windows
    would silently rewrite the whole file as CRLF -- a spurious diff over every line.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def href_of(el):
    return el.get("href") or el.get(XLINK_HREF)


def geometry_descendants(el):
    """Every descendant of `el` that carries a transform, in document order."""
    return [child for child in el.iter() if child is not el and child.get("transform")]


def matrix_to_root(el, parents):
    """The matrix of `el` and every ancestor, in the order the drawing applies them.

    SVG nests transforms innermost-first: a transform on a child is applied to its
    geometry before its parent's. Walking outward from `el` therefore visits the
    matrices in application order, and each one is multiplied on the *left* of what
    is already there -- so the outermost element ends up leftmost, and the element
    itself rightmost. For a `<use>` pointing at a def, that is
    ``ancestors . use . def . contents``.
    """
    m = parse_transform(el.get("transform", ""))
    cur = el
    while cur in parents:
        cur = parents[cur]
        m = mat_mul(parse_transform(cur.get("transform", "")), m)
    return m


def referenced_chain(use, referenced):
    """(placement, elements): how the referenced geometry is placed, and by what.

    `placement` is the product of the def's own transform and everything inside it,
    outermost first. It deliberately excludes the `<use>` element's own transform.

    Nested SVG transforms apply innermost-first, so the full placement of the
    geometry a use U points at is ``U . placement`` -- the use's transform is
    applied last and is therefore leftmost.

    Only the elements whose transform was actually folded in are returned, so no
    element loses a transform that is not accounted for in the result.
    """
    chain = [referenced]
    for el in geometry_descendants(referenced):
        if local(el.tag) == "g":
            # A nested group composes like anything else, but so does whatever its
            # siblings do; folding it into the use would drag them along with it.
            raise SystemExit(
                f"use #{use.get('id')}: {referenced.get('id')} holds a nested "
                f"transformed group ({el.get('id') or 'unnamed'}) -- flatten that "
                f"by hand, or flatten it into the individual file instead"
            )
        chain.append(el)

    placement = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for el in chain:
        placement = mat_mul(placement, parse_transform(el.get("transform", "")))
    return placement, chain


def referenced_placement(use, referenced):
    """The whole placement of a use's geometry: ``use . def . contents``."""
    placement, chain = referenced_chain(use, referenced)
    return mat_mul(parse_transform(use.get("transform", "")), placement), chain


def plan_changes(root):
    """What will be rewritten, without writing anything.

    Returns a list of (use_element, referenced_element, old_transform, new_transform,
    [elements losing their transform]).
    """
    by_id = {}
    for el in root.iter():
        eid = el.get("id")
        if eid and local(el.tag) in ("g", "path", "rect", "circle", "ellipse", "polygon",
                                     "polyline", "line", "text", "tspan", "use", "image"):
            by_id.setdefault(eid, el)

    changes = []
    for use in root.iter(f"{{{SVG_NS}}}use"):
        target = href_of(use)
        if not target or not target.startswith("#"):
            continue
        tid = target[1:]
        if tid not in by_id:
            raise SystemExit(f"use #{use.get('id')}: no element with id {tid!r}")
        referenced = by_id[tid]

        composed, chain = referenced_placement(use, referenced)

        # Always written out, even when it collapses to the identity: the placement
        # is then stated once per use, in one place, with nothing left implicit.
        new = matrix_attr(composed)
        losing = [el for el in chain if el.get("transform")]
        changes.append((use, referenced, use.get("transform", ""), new, losing))
    return changes

# ---------------------------------------------------------------------------
# verification: compare every geometry element's composed matrix, old vs new
# ---------------------------------------------------------------------------
def composed_geometry_matrices(path):
    """{geometry id: the matrix that places it}, for every drawable element.

    The matrix is read the way a renderer builds it, so both the file before the
    flatten and the file after it are described by one rule with no special cases:
    start from the element's own transform and fold in each ancestor's, walking
    outward (a child's transform is applied before its parent's).

    For a `<use>`, walking ancestors reaches the `<defs>` and the referenced
    element, and the element's own transform is the one on the `<use>` -- which,
    after flattening, already carries everything the def and its contents used to.
    """
    root = ET.parse(path).getroot()
    parents = {child: parent for parent in root.iter() for child in parent}
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}

    def in_defs(el):
        """True for a <defs> descendant: inert, and drawn only where a use puts it.

        A def's own matrix stops meaning anything once its use has been flattened,
        so defs geometry is left out of the comparison rather than reported as a
        false move.
        """
        cur = el
        while cur in parents:
            cur = parents[cur]
            if local(cur.tag) == "defs":
                return True
        return False

    out = {}
    for el in root.iter():
        kind = local(el.tag)
        if kind == "use":
            # Where the use sits, times what it applies, times how the def places
            # its own contents. The def part is read from the file as it stands, so
            # one rule covers both files: before flattening the def carries its
            # transform, and after flattening it carries none, and the use carries
            # the lot.
            placement = parse_transform(el.get("transform", ""))
            ref = by_id.get((href_of(el) or "#")[1:])
            if ref is not None:
                inner, _chain = referenced_chain(el, ref)
                placement = mat_mul(placement, inner)
            out[f"use:{el.get('id')}"] = mat_mul(_ancestors_of(el, parents), placement)
        elif kind in ("path", "rect", "circle", "ellipse", "line", "polygon", "polyline"):
            if in_defs(el):
                continue
            out[f"geo:{el.get('id')}"] = matrix_to_root(el, parents)
    return out


def _ancestors_of(el, parents):
    """Every ancestor's matrix, outermost leftmost; `el` itself is not included."""
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    cur = el
    while cur in parents:
        cur = parents[cur]
        m = mat_mul(parse_transform(cur.get("transform", "")), m)
    return m


def matrices_match(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def verify(before_path, after_path):
    before = composed_geometry_matrices(before_path)
    after = composed_geometry_matrices(after_path)
    problems = []
    for key, m in before.items():
        if key not in after:
            problems.append(f"missing after: {key}")
        elif not matrices_match(m, after[key]):
            problems.append(f"moved: {key}\n    before {m}\n    after  {after[key]}")
    for key in after:
        if key not in before:
            problems.append(f"extra after: {key}")
    return problems


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg", nargs="?", default=DEFAULT_SVG)
    ap.add_argument("-o", "--output", help="write here instead of in place")
    ap.add_argument("-n", "--check", action="store_true",
                    help="report the plan and verify, write nothing")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="show every transform being folded into each use")
    args = ap.parse_args(argv)

    src = args.svg
    text = read_text(src)

    root = ET.fromstring(text)
    changes = plan_changes(root)

    # --- what the plan says, for the operator ---------------------------------
    print(f"{len(changes)} <use> element(s) to flatten:")
    for use, referenced, old, new, stripped in changes:
        uid = use.get("id") or "?"
        if args.verbose:
            src_bits = []
            if referenced.get("transform"):
                src_bits.append(f"{referenced.get('id')}:[{referenced.get('transform')}]")
            for el in geometry_descendants(referenced):
                src_bits.append(f"{el.get('id') or local(el.tag)}:[{el.get('transform')}]")
            print(f"  {uid:6s} use:[{old or '(none)'}]")
            for bit in src_bits:
                print(f"         folded {bit}")
            print(f"         => {new or '(none)'}")
        else:
            print(f"  {uid:6s} -> {new or '(none)'}   "
                  f"({len(stripped)} inner transform(s) folded away)")

    transforms_dropped = sum(1 for _, ref, _, _, _ in changes if ref.get("transform")) \
        + sum(len(stripped) for _, _, _, _, stripped in changes)
    print(f"  plus {transforms_dropped} transform attribute(s) removed from <defs>")

    # --- rebuild only the tags that change ------------------------------------
    use_new = {use.get("id"): new for use, _, _, new, _ in changes}
    def_new = {ref.get("id") for _, ref, _, _, _ in changes}
    strip_inner = {el.get("id") for _, ref, _, _, _ in changes
                   for el in geometry_descendants(ref)}
    drop_transform = {"transform": ""}

    out_parts = []
    n_use = n_def = n_inner = 0
    for start, end, name, attrs, is_close in tags_with_spans(text):
        if is_close:
            continue
        eid = id_of(attrs)
        # Keep the closing characters exactly as the document wrote them, so a
        # self-closing tag stays " />" and an opening tag keeps any trailing space.
        raw_tag = text[start:end].rstrip()
        tail = raw_tag[-(len(raw_tag) - raw_tag.rfind("/")):] if raw_tag.endswith("/>") else ">"

        if name == "use" and eid in use_new:
            rebuilt = set_attrs(attrs, {"transform": use_new[eid]}, drop_transform)
            out_parts.append((start, end, f"<use{rebuilt}{tail}"))
            n_use += 1
        elif eid is not None and eid in def_new:
            rebuilt = set_attrs(attrs, {}, drop_transform)
            out_parts.append((start, end, f"<{name}{rebuilt}{tail}"))
            n_def += 1
        elif eid is not None and eid in strip_inner:
            rebuilt = set_attrs(attrs, {}, drop_transform)
            out_parts.append((start, end, f"<{name}{rebuilt}{tail}"))
            n_inner += 1

    # assemble
    pieces = []
    cursor = 0
    for start, end, replacement in out_parts:
        pieces.append(text[cursor:start])
        pieces.append(replacement)
        cursor = end
    pieces.append(text[cursor:])
    new_text = "".join(pieces)

    print(f"  rewrote {n_use} <use>, {n_def} def group(s), {n_inner} inner element(s)")

    if args.check:
        out = args.output or ".flatten-check.svg"
        write_text(out, new_text)
        problems = verify(src, out)
        if problems:
            print("VERIFY FAILED:")
            for p in problems:
                print("  " + p)
            return 1
        print(f"verify OK: every geometry element keeps its composed matrix ({out} left for inspection)")
        return 0

    out = args.output or src
    tmp = out + ".tmp"
    write_text(tmp, new_text)
    problems = verify(src, tmp)
    if problems:
        print("VERIFY FAILED -- not writing:")
        for p in problems:
            print("  " + p)
        return 1
    print("verify OK: every geometry element keeps its composed matrix")
    os.replace(tmp, out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
