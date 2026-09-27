#!/usr/bin/env python3
"""
hide_geometry_source.py
=======================

Move feathers-aggregate-min.svg's geometry out of <defs> and into a hidden
<g>, so the outlines stay in the document tree where they can be selected and
edited instead of being buried in the defs section.

Why a hidden <g> and not just "a group":

    display:none on a container is INHERITED into the shadow tree of any <use>
    that references something inside it. Hiding the geometry the obvious way
    therefore hides every placed copy too. The fix is to re-state the visible
    value on each <use>, which is what this script does.

    Measured in Inkscape, against the <defs> build:
      container display:none + <use> display:inline   -> 0 of 2,019,235 px differ
      container visibility:hidden + visibility:visible -> 151,404 px differ
      bare hidden attribute                           -> 151,404 px differ

    So the override is load-bearing, not belt-and-braces. The script asserts
    every <use> carries it.

Intended to run once, against the post-consolidation aggregate. It is the
migration that produced the current file; re-running it is a no-op.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AGG = ROOT / "mechanical" / "templates" / "feathers-aggregate-min.svg"

CONTAINER_ID = "geometry-source"
CONTAINER_NOTE = (
    "<!-- Feather + topline geometry, kept out of <defs> so it stays selectable\n"
    "       and editable. The container is display:none, so it never draws; every\n"
    "       <use> below re-states display:inline, because display is inherited\n"
    "       into a <use>'s shadow tree and would otherwise hide the placed\n"
    "       copies too. Selecting a placed feather and pressing Shift+D\n"
    "       (Edit > Select original) jumps straight to its outline here. -->")

USE_RE = re.compile(r"<use\b[^>]*?/>", re.S)


def read_text(path):
    return path.read_text(encoding="utf-8", newline="")


def write_text(path, text):
    path.write_text(text, encoding="utf-8", newline="")


def main():
    text = read_text(AGG)

    if f'id="{CONTAINER_ID}"' in text:
        print(f"already migrated: {CONTAINER_ID} is present in {AGG.name}")
        return 0
    if "<defs" not in text:
        raise SystemExit(f"{AGG.name}: no <defs> to migrate from")

    # 1. Swap the populated <defs> container for the hidden <g>.
    m = re.search(r'<defs\b[^>]*id="defs1"[^>]*>(.*?)</defs>', text, re.S)
    if not m:
        raise SystemExit("could not find the populated <defs id=\"defs1\">")
    inner = m.group(1)
    if "</g>" not in inner:
        raise SystemExit("the <defs> section does not look populated")
    # The container sits at the same indentation the <defs> did, so the body
    # needs no shift at all.
    text = (text[:m.start()]
            + f'<g\n     id="{CONTAINER_ID}"\n     style="display:none">'
            + inner + "</g>"
            + text[m.end():])

    # 2. Re-state display on every <use>, or the placed copies vanish with it.
    def fix(mm):
        chunk = mm.group(0)
        if 'style="' in chunk:
            return chunk.replace('style="', 'style="display:inline;', 1)
        return chunk.replace("/>", 'style="display:inline" />', 1)

    text, n = USE_RE.subn(fix, text)
    if n == 0:
        raise SystemExit("found no <use> elements to re-enable")

    # 3. Park the note next to the container.
    text = text.replace(f'<g\n     id="{CONTAINER_ID}"',
                        CONTAINER_NOTE + f'\n  <g\n     id="{CONTAINER_ID}"', 1)

    # 4. Keep an empty <defs> so the document still has the usual structure.
    text = text.replace(CONTAINER_NOTE, '<defs\n     id="defs1" />\n  '
                        + CONTAINER_NOTE, 1)

    check(text, n)
    write_text(AGG, text)
    print(f"moved geometry into <g id=\"{CONTAINER_ID}\">; "
          f"re-stated display:inline on {n} <use> elements")
    print(f"wrote {AGG} ({AGG.stat().st_size} bytes)")
    return 0


def check(text, n_uses):
    """Every <use> must re-state display, or the geometry disappears."""
    root = ET.fromstring(text)

    container = None
    for el in root.iter():
        if el.get("id") == CONTAINER_ID:
            container = el
    if container is None:
        raise SystemExit(f"no <g id=\"{CONTAINER_ID}\"> after the rewrite")
    if "display:none" not in (container.get("style") or ""):
        raise SystemExit("the geometry container is not display:none")

    uses = [el for el in root.iter() if el.tag.endswith("}use")]
    if len(uses) != n_uses:
        raise SystemExit(f"expected {n_uses} <use> elements, parsed {len(uses)}")
    missing = [u.get("id") for u in uses
               if "display:inline" not in (u.get("style") or "")]
    if missing:
        raise SystemExit(f"<use> without a display override: {missing}")

    # The scripts read these; the move must not have dropped any.
    frames = [el for el in root.iter() if el.get("data-wh")]
    if len(frames) != 36:
        raise SystemExit(f"expected 36 def groups with data-wh, found {len(frames)}")


if __name__ == "__main__":
    sys.exit(main())
