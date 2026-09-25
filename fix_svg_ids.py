#!/usr/bin/env python3
"""Sync SVG element ids to their inkscape:label.

Inkscape hides ids in dedicated dialogs while still exposing
inkscape:label, so a renamed element keeps a stale id. This walks the
document and, for any element whose inkscape:label differs from its id,
rewrites the id to the label value.

Usage:
    python fix_svg_ids.py file.svg            # rewrite in place
    python fix_svg_ids.py file.svg --dry-run  # just report
    python fix_svg_ids.py file.svg -o out.svg # write elsewhere
"""

import argparse
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
INK_LABEL = f"{{{INKSCAPE_NS}}}label"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# keep the namespace prefixes stable-ish; ET drops the inkscape prefix
# declaration unless we register it back.
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")


def sync_ids(root):
    """Yield (old_id, new_id) for every element we rewrote."""
    for el in root.iter():
        old = el.get("id")
        label = el.get(INK_LABEL)
        if label is None or old is None:
            continue
        if label == old:
            continue
        el.set("id", label)
        yield old, label


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("svg")
    ap.add_argument("-o", "--output", help="write here instead of in place")
    ap.add_argument("-n", "--dry-run", action="store_true")
    args = ap.parse_args()

    tree = ET.parse(args.svg)
    root = tree.getroot()

    changes = list(sync_ids(root))

    for old, new in changes:
        print(f"{old} -> {new}")

    if not changes:
        print("nothing to do")
        return 0

    if args.dry_run:
        print(f"[dry-run] {len(changes)} id(s) would change")
        return 0

    out = args.output or args.svg
    tree.write(out, encoding="UTF-8", xml_declaration=True)
    print(f"wrote {out} ({len(changes)} id(s) changed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
