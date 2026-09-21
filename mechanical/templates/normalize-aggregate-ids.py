#!/usr/bin/env python3
"""Pass 1: align the aggregate's feather group, outline and label ids with the individuals.

Every feather group in the aggregate becomes, matching the individual files:

    <g id="{feather}">          the group (already the feather code)
    <path id="{feather}-outline">
    <text id="{feather}-label">

The prefix groups (``P``, ``S``, ...), the ``toplines`` group and the document scaffolding keep
their ids; the centre line is left for pass 2. Only ``id`` attributes change -- path geometry is
compared before and after, and the result is re-parsed.

Usage
-----
    python normalize-aggregate-ids.py --check
    python normalize-aggregate-ids.py
"""
from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AGG = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
DEFAULT_IND = os.path.join(HERE, "as-built", "vectors", "individuals")
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

OUTLINE_SUFFIX = "-outline"
LABEL_SUFFIX = "-label"


def local(tag):
    return tag.split("}")[-1]


def geometry(tree):
    return [{k: v for k, v in el.attrib.items() if k != "id"}
            for el in tree.iter(f"{{{SVG_NS}}}path")]


def retag(label, group, changes):
    """Group id -> the feather code; its direct outline and label -> the suffixed ids."""
    if group.get("id") != label:
        changes.append((f"group {group.get('id')!r}", label))
        group.set("id", label)
    for el in group:
        kind = local(el.tag)
        old = el.get("id")
        if kind == "path":
            # in pass 1 the only path that is not already the suffixed outline is the centre line,
            # which pass 2 renames; everything else is the outline
            if old and old.endswith(OUTLINE_SUFFIX):
                continue
            new = f"{label}{OUTLINE_SUFFIX}"
        elif kind == "text":
            new = f"{label}{LABEL_SUFFIX}"
        else:
            continue
        if old != new:
            changes.append((f"{label} {kind} {old!r}", new))
            el.set("id", new)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregate", default=DEFAULT_AGG,
                    help=f"aggregate to update (default {DEFAULT_AGG})")
    ap.add_argument("--individuals", default=DEFAULT_IND,
                    help=f"folder whose file names are the labels (default {DEFAULT_IND})")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    labels = {os.path.splitext(f)[0] for f in os.listdir(args.individuals) if f.endswith(".svg")}
    with open(args.aggregate, encoding="utf-8", newline="") as fh:
        text = fh.read()
    tree = ET.fromstring(text)
    before = geometry(tree)

    changes, found = [], []
    for g in tree.iter(f"{{{SVG_NS}}}g"):
        label = g.get("id") or ""
        if label not in labels:
            continue
        found.append(label)
        retag(label, g, changes)

    missing = sorted(labels - set(found))
    print(f"{os.path.basename(args.aggregate)}: {len(found)} feather groups, "
          f"{len(changes)} ids to retag")
    for old, new in changes:
        print(f"  {old:28s} -> {new}")
    if missing:
        print("  ! no group in the aggregate for: " + ", ".join(missing))

    if geometry(tree) != before:
        raise SystemExit("path geometry changed; nothing written")
    if args.check:
        print("(--check: nothing written)")
        return 1 if missing else 0

    ET.indent(tree, space="  ")
    with open(args.aggregate, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 + ET.tostring(tree, encoding="unicode") + "\n")
    print(f"wrote {args.aggregate}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
