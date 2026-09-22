#!/usr/bin/env python3
"""Remove the quill centre lines from the aggregate, in place.

They are being redrawn by hand in the aggregate, so the generated ones come out. Edits the file
textually to leave everything else exactly as it stands (the file is hand-maintained and has been
through Inkscape, so re-serialising it would reformat all of it).

Usage
-----
    python remove-aggregate-centerlines.py --check
    python remove-aggregate-centerlines.py
"""
from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AGG = os.path.join(HERE, "as-built", "vectors", "feathers-aggregate.svg")
SVG_NS = "http://www.w3.org/2000/svg"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregate", default=DEFAULT_AGG,
                    help=f"aggregate to update (default {DEFAULT_AGG})")
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    with open(args.aggregate, encoding="utf-8", newline="") as fh:
        text = fh.read()
    root = ET.fromstring(text)

    wanted = [el.get("id") for el in root.iter(f"{{{SVG_NS}}}path")
              if (el.get("id") or "").endswith("-center-line")]
    if not wanted:
        print("no centre lines in the file")
        return 0
    for cid in wanted:
        if text.count(f'id="{cid}"') != 1:
            raise SystemExit(f'{cid}: id is not unique in the file; nothing written')

    lines = text.splitlines(keepends=True)
    kept, removed = [], 0
    skip_until = None
    for line in lines:
        if skip_until is not None:
            if skip_until in line:            # the line closing the element
                skip_until = None
            removed += 1
            continue
        if any(f'id="{cid}"' in line for cid in wanted):
            tag = line.lstrip()
            if tag.startswith("<path"):
                if tag.rstrip().endswith("/>"):
                    removed += 1
                    continue
                skip_until = "/>"
            removed += 1
            continue
        kept.append(line)

    new_text = "".join(kept)
    check = ET.fromstring(new_text)
    left = [el.get("id") for el in check.iter(f"{{{SVG_NS}}}path")
            if (el.get("id") or "").endswith("-center-line")]
    if left:
        raise SystemExit(f"{len(left)} centre lines survived; nothing written")

    # the removal must not have touched anything else
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, lines, kept, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag != "delete":
            raise SystemExit(f"the edit changed lines near {i1 + 1}; nothing written")

    print(f"{os.path.basename(args.aggregate)}: {len(wanted)} centre lines, "
          f"{removed} lines removed")
    for cid in wanted[:4]:
        print(f"  {cid}")
    if len(wanted) > 4:
        print(f"  ... and {len(wanted) - 4} more")
    if args.check:
        print("(--check: nothing written)")
        return 0

    with open(args.aggregate, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    print(f"wrote {args.aggregate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
