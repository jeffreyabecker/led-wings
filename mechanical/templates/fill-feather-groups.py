#!/usr/bin/env python3
"""Fill each feather in the aggregate with a colour for its grouping.

The aggregate's feathers are grouped by prefix (P, S, A, PC, SC, MC, LC, B). Each outline path
currently carries an inline ``fill="none"``, which beats anything inherited from its prefix group,
so the fill is set on the outline itself:

    <path id="{feather}-outline" fill="{colour}" fill-opacity="0.45" .../>

The colour is looked up from the feather's prefix and recorded on the prefix group as
``data-fill`` so the palette is readable in the file. Translucent on purpose: the rows overlap
heavily, so a solid fill would hide whole feathers. Geometry, stroke and the centre lines are
untouched.

Usage
-----
    python fill-feather-groups.py --check     # report only, write nothing
    python fill-feather-groups.py
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

# One colour per grouping. Deliberately light/pastel rather than saturated: the fills stack.
FILLS = {
    "P": "#1f77b4",    # primaries
    "S": "#ff7f0e",    # secondaries
    "A": "#2ca02c",    # alula
    "PC": "#d62728",   # primary coverts
    "SC": "#9467bd",   # secondary coverts
    "MC": "#17becf",   # median coverts
    "LC": "#bcbd22",   # lesser coverts
    "B": "#8c564b",    # body feathers
}
FALLBACK = "#7f7f7f"
FILL_OPACITY = "0.45"


def local(tag):
    return tag.split("}")[-1]


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

    counts, changed, unknown = {}, [], set()
    for g in root.iter(f"{{{SVG_NS}}}g"):
        outlines = [e for e in g if (e.get("id") or "").endswith("-outline")]
        if not outlines:
            continue
        label = g.get("id") or ""
        m = LABEL_RE.match(label)
        prefix = m.group(1).upper() if m else ""
        colour = FILLS.get(prefix, FALLBACK)
        if prefix not in FILLS:
            unknown.add(label)
        counts[prefix] = counts.get(prefix, 0) + 1
        g.set("data-fill", colour)
        for el in outlines:
            if el.get("fill") != colour or el.get("fill-opacity") != FILL_OPACITY:
                el.set("fill", colour)
                el.set("fill-opacity", FILL_OPACITY)
                changed.append(f"{label}-outline")

    print(f"{os.path.basename(args.aggregate)}: {len(changed)} outlines filled")
    for prefix in sorted(counts):
        print(f"  {prefix:3s} {counts[prefix]:2d} feathers  {FILLS.get(prefix, FALLBACK)}"
              + ("" if prefix in FILLS else "   (no palette entry)"))
    if unknown:
        print("  ! no palette for: " + ", ".join(sorted(unknown)))

    if args.check:
        print("(--check: nothing written)")
        return 0
    if not changed:
        print("nothing to do")
        return 0

    ET.indent(root, space="  ")
    with open(args.aggregate, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 + ET.tostring(root, encoding="unicode") + "\n")
    print(f"wrote {args.aggregate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
