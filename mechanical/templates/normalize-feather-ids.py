#!/usr/bin/env python3
"""Normalize the ids in every individual feather SVG.

Each file holds one group with a label and two paths. The ids were generic (``feather``,
``feather-label``, ``center-line``) and the outline doubled as the feather code, which says
nothing about which element is which. Rewrite them as:

    <g id="feather">              -> <g id="{feather}">
    <text id="feather-label">     -> <text id="{feather}-label">
    <path id="{feather}">         -> <path id="{feather}-outline">
    <path id="center-line">       -> <path id="{feather}-center-line">

where ``{feather}`` is the file's own name (the label it carries). Geometry is never touched:
only ``id`` attributes change, and every path's ``d``, ``transform``, ``style`` and
``sodipodi:nodetypes`` are compared before and after.

Usage
-----
    python normalize-feather-ids.py --check     # report only, write nothing
    python normalize-feather-ids.py             # update in place
    python normalize-feather-ids.py --dir D
"""
from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(HERE, "as-built", "vectors", "individuals")
SVG_NS = "http://www.w3.org/2000/svg"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_NS = "http://www.w3.org/1999/xlink"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
CC_NS = "http://creativecommons.org/ns#"
DC_NS = "http://purl.org/dc/elements/1.1/"
for _prefix, _uri in (("", SVG_NS), ("sodipodi", SODIPODI_NS), ("inkscape", INKSCAPE_NS),
                      ("xlink", XLINK_NS), ("rdf", RDF_NS), ("cc", CC_NS), ("dc", DC_NS)):
    ET.register_namespace(_prefix, _uri)

# svg, inkscape and dc/cc/rdf only ever appeared as <defs>/<sodipodi:namedview> scaffolding; the
# individual files carry none of them, so the round trip below has nothing to lose.


def local(tag):
    return tag.split("}")[-1]


def rename(label, tree):
    """Retag the group and its three children in place; return {old: new} for the record.

    Idempotent: the old ids (``feather``, ``feather-label``, ``<label>``, ``center-line``) and the
    new ones are both accepted, so a second run is a no-op and a half-normalized file still lands
    on the same scheme.
    """
    group = next((g for g in tree.iter(f"{{{SVG_NS}}}g")), None)
    if group is None:
        raise SystemExit(f"{label}: no <g>")
    seen = {}
    new_id = label if group.get("id") in ("feather", label) else None
    if new_id is None:
        raise SystemExit(f"{label}: group id is {group.get('id')!r}, expected 'feather' or {label!r}")
    seen[group.get("id")] = new_id
    group.set("id", new_id)

    for el in group:
        kind = local(el.tag)
        old = el.get("id")
        if kind == "text":
            new = f"{label}-label"
            if old not in ("feather-label", new):
                raise SystemExit(f"{label}: label id is {old!r}, expected 'feather-label' or {new!r}")
        elif kind == "path":
            # the outline carried the feather code itself; the other path is the quill line
            new = f"{label}-outline" if old in (label, f"{label}-outline") else f"{label}-center-line"
            if old not in (label, new, f"{label}-center-line"):
                raise SystemExit(f"{label}: path id is {old!r}, which is neither the outline "
                                 f"({label!r}) nor the centre line ('center-line')")
        else:
            continue
        if old in seen and seen[old] != new:
            raise SystemExit(f"{label}: {old!r} would map to both {seen[old]!r} and {new!r}")
        seen[old] = new
        el.set("id", new)
    return seen


def geometry(tree):
    """Every path's drawing attributes, for a before/after comparison."""
    return [{k: v for k, v in el.attrib.items() if k != "id"}
            for el in tree.iter(f"{{{SVG_NS}}}path")]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=DEFAULT_DIR,
                    help=f"folder of individual feather SVGs (default {DEFAULT_DIR})")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    names = sorted(f for f in os.listdir(args.dir) if f.endswith(".svg"))
    if not names:
        raise SystemExit(f"no SVGs in {args.dir}")

    changed, unchanged = [], []
    for name in names:
        label = os.path.splitext(name)[0]
        path = os.path.join(args.dir, name)
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        tree = ET.fromstring(text)
        before = geometry(tree)
        mapping = rename(label, tree)

        group = next(g for g in tree.iter(f"{{{SVG_NS}}}g"))
        want = {label, f"{label}-label", f"{label}-outline", f"{label}-center-line"}
        got = {group.get("id")} | {el.get("id") for el in group}
        if got != want:
            raise SystemExit(f"{label}: ids came out as {sorted(got)}, expected {sorted(want)}")
        if geometry(tree) != before:
            raise SystemExit(f"{label}: path geometry changed; nothing written")

        if set(mapping) == want and all(k == v for k, v in mapping.items()):
            unchanged.append(label)
            continue
        changed.append(label)
        if not args.check:
            ET.indent(tree, space="  ")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                         + ET.tostring(tree, encoding="unicode") + "\n")

    print(f"{len(names)} files in {args.dir}: {len(changed)} renamed"
          + (f", {len(unchanged)} already normalized ({', '.join(unchanged)})" if unchanged else ""))
    for label in changed:
        print(f"  {label:5s} feather -> {label}, feather-label -> {label}-label, "
              f"{label} -> {label}-outline, center-line -> {label}-center-line")
    print("(--check: nothing written)" if args.check else f"wrote {len(changed)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
