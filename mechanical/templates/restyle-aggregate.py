#!/usr/bin/env python3
"""Move the aggregate's presentation from inline attributes to one stylesheet.

Everything that paints is currently repeated on every element: each outline carries
``fill``, ``fill-opacity``, ``stroke`` and ``stroke-width``, each label its font and anchor, and
each centre line a style attribute whose only real value is its stroke width (the rest is
Inkscape noise, and the widths in the file differ in the sixth decimal). This replaces all of it
with a single ``<style>`` block and classes:

    .group    -> the structure lines and labels (stroke, font)
    .outline  -> the feather body; the fill comes from the grouping class, so all six primaries
                 share one rule instead of six copies of the same colour
    .P .outline { fill: #1f77b4 }   ... one rule per grouping
    .centerline -> the quill guide

Colour, opacity and widths now live in exactly one place, and a class can be restyled in a
browser. Presentation attributes are removed rather than left as a fallback -- two sources of
truth is what the stylesheet is meant to end. Geometry (``d``, ``transform``,
``sodipodi:nodetypes``), ids and the ``data-*`` provenance stay attributes, since CSS cannot
carry them; the six ``toplines`` paths are already style-free and are left alone.

Usage
-----
    python restyle-aggregate.py --check     # report only, write nothing
    python restyle-aggregate.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AGG = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
SVG_NS = "http://www.w3.org/2000/svg"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_NS = "http://www.w3.org/1999/xlink"
for _prefix, _uri in (("", SVG_NS), ("sodipodi", SODIPODI_NS),
                      ("inkscape", INKSCAPE_NS), ("xlink", XLINK_NS)):
    ET.register_namespace(_prefix, _uri)

LABEL_RE = re.compile(r"^([A-Za-z]+)\d+$")
# The centre line's stroke width, to 4 dp for the stylesheet. Inline this was 0.264583px on 38
# lines and 0.2645xx on the rest, except four at 0.2415xx -- Inkscape's noise, 0.02 mm at 1:1, so
# they all take the one value the majority already had.
CENTER_STROKE = "0.2646"

GROUPS = [
    ("P", "primaries", "#1f77b4"),
    ("S", "secondaries", "#ff7f0e"),
    ("A", "alula", "#2ca02c"),
    ("PC", "primary coverts", "#d62728"),
    ("SC", "secondary coverts", "#9467bd"),
    ("MC", "median coverts", "#17becf"),
    ("LC", "lesser coverts", "#bcbd22"),
    ("B", "body feathers", "#8c564b"),
]
FILL_OPACITY = "0.45"

# presentation moved into the stylesheet; anything not listed stays an attribute
STRIP_PATH = ("fill", "fill-opacity", "stroke", "stroke-width", "style")
STRIP_TEXT = ("font-family", "font-size", "fill", "text-anchor", "style")


def local(tag):
    return tag.split("}")[-1]


def stylesheet():
    lines = [
        "/* As-built feather catalog. Presentation lives here; elements carry classes only. */",
        ".group {",
        "  stroke: #000000;",
        "  stroke-width: 0.5;",
        "}",
        ".label {",
        "  font-family: sans-serif;",
        "  font-size: 6px;",
        "  fill: #000000;",
        "  text-anchor: middle;",
        "}",
        ".outline {",
        "  stroke: #000000;",
        f"  fill-opacity: {FILL_OPACITY};",
        "}",
        ".centerline {",
        "  fill: none;",
        f"  stroke-width: {CENTER_STROKE};",
        "  stroke-linecap: butt;",
        "  stroke-linejoin: miter;",
        "}",
    ]
    for prefix, title, colour in GROUPS:
        lines += ["", f"/* {prefix} -- {title} */", f".{prefix} .outline {{ fill: {colour}; }}"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregate", default=DEFAULT_AGG,
                    help=f"aggregate to update (default {DEFAULT_AGG})")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    with open(args.aggregate, encoding="utf-8", newline="") as fh:
        text = fh.read()
    root = ET.fromstring(text)

    groups = {p: (title, c) for p, title, c in GROUPS}
    # there are no prefix <g> wrappers in the aggregate: the 42 feather groups sit directly under
    # the root, so the grouping class goes on each feather group and the stylesheet targets
    # `.P .outline` style rules through it
    feather_groups = [g for g in root.iter(f"{{{SVG_NS}}}g")
                      if any((e.get("id") or "").endswith("-outline") for e in g)]

    counts = {"outline": 0, "centerline": 0, "label": 0}
    seen_prefixes = set()
    for fg in feather_groups:
        m = LABEL_RE.match(fg.get("id") or "")
        if not m or m.group(1) not in groups:
            raise SystemExit(f"{fg.get('id')!r}: no grouping colour for this feather")
        prefix = m.group(1)
        seen_prefixes.add(prefix)
        classes = [c for c in (fg.get("class") or "").split() if c not in ("group", prefix)]
        fg.set("class", " ".join(["group", prefix] + classes))
        # the group's inline style (`fill:none;stroke:#000000;stroke-width:0.5`) is what the
        # children used to inherit; the stylesheet now carries it, on the children
        fg.attrib.pop("style", None)
        for el in fg:
            name = local(el.tag)
            if name == "path":
                is_outline = (el.get("id") or "").endswith("-outline")
                add = "outline" if is_outline else "centerline"
                counts[add] += 1
                current = [c for c in (el.get("class") or "").split() if c != add]
                el.set("class", " ".join([add] + current))
                for attr in STRIP_PATH:
                    el.attrib.pop(attr, None)
            elif name == "text":
                counts["label"] += 1
                current = [c for c in (el.get("class") or "").split() if c != "label"]
                el.set("class", " ".join(["label"] + current))
                for attr in STRIP_TEXT:
                    el.attrib.pop(attr, None)

    print(f"{os.path.basename(args.aggregate)}: {len(feather_groups)} feather groups across "
          f"{len(seen_prefixes)} groupings ({', '.join(sorted(seen_prefixes))}), "
          f"{counts['outline']} outlines, {counts['centerline']} centre lines, "
          f"{counts['label']} labels")
    if not counts["outline"]:
        raise SystemExit("no feather outlines found; nothing written")

    style = ET.Element(f"{{{SVG_NS}}}style")
    style.set("type", "text/css")
    style.text = "\n" + stylesheet()
    if root.find(f"{{{SVG_NS}}}style") is not None:
        root.remove(root.find(f"{{{SVG_NS}}}style"))
    root.insert(0, style)

    ET.indent(root, space="  ")
    new_text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                + ET.tostring(root, encoding="unicode") + "\n")
    if args.check:
        print("(--check: nothing written)")
        return 0
    with open(args.aggregate, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    print(f"wrote {args.aggregate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
