#!/usr/bin/env python3
"""
consolidate_aggregate.py
========================

The inverse of the commit that broke the feathers out into individuals/: fold
mechanical/templates/individuals/*.svg back into feathers-aggregate-min.svg so
the aggregate is the single source of truth for feather geometry.

The rewrite is deliberately dumb about geometry. For every external reference

    <use id="B1" href="individuals/B1.svg#B1-def" width=... height=...
         transform="matrix(...)"/>

it copies the referenced <g> VERBATIM into <defs> and changes **only** the
href, to "#B1-def". Every id, width, height, style and transform on the <use>
is left byte-for-byte, so the arrangement -- and every one of its rotations --
is untouched. Nothing has to be recomputed because the split never applied the
source file's viewBox: the <use> matrices already encode the whole placement.

Blocks are moved as TEXT, not re-serialised, so the hand-authored Inkscape
formatting of the aggregate and of the individual files survives exactly. Each
moved block keeps its own relative indentation and is shifted to sit inside
<defs>.

Two things do not fold in by that rule alone:

  * outline-toplines.svg is a 300x300mm document whose viewBox origin is the
    frame the print script measures against, and it is built from three groups
    (top-lines, total-outline, upper-outline) plus eight <use>s pointing at the
    *-topline.svg files. Its groups are re-homed with a "placement-" id prefix
    and its inner <use>s are retargeted at the inlined defs.

  * seven def groups carry inkscape:label on a <path>. The logical pages are
    written with a default-namespace-rooted ElementTree, which cannot serialise
    a prefixed attribute, so namespaced attributes are stripped here and their
    absence is asserted.

Usage:
    python consolidate_aggregate.py            # rewrite the aggregate in place
    python consolidate_aggregate.py --out X    # write elsewhere (dry runs)

This was run once, to produce the current aggregate; individuals/ has since
been deleted, so it now exits with "unresolved reference" if run again. It is
kept because it is the only record of how the aggregate was assembled, and
because it is the inverse of the commit that broke the feathers out.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TPL = ROOT / "mechanical" / "templates"
AGG = TPL / "feathers-aggregate-min.svg"
IND = TPL / "individuals"

INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"

# Groups whose plain ids would collide with the per-feather def group ids.
PLACEMENT_PREFIX = "placement-"
# The 8 topline <use>s inside outline-toplines' "top-lines" group are renamed
# so their ids do not collide with the "X-topline-def" def groups.
TOPLINE_USE_PREFIX = "toplines-"
# The <use> inside total-outline that pulls in upper-outline.svg.
UPPER_USE_ID = "placement-upper-outline-ref"

USE_RE = re.compile(r"<use\b[^>]*?/>", re.S)
ATTR_RE = re.compile(r'(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*"(?P<value>[^"]*)"')


# --------------------------------------------------------------------------
# Text surgery helpers
# --------------------------------------------------------------------------

def open_tag(text, start):
    """Return (tag, end_of_open_tag) for the element whose '<' is at `start`."""
    m = re.match(r"<([A-Za-z_][-A-Za-z0-9_.:]*)", text[start:])
    if not m:
        raise ValueError(f"no element at offset {start} ({text[start:start + 30]!r})")
    tag = m.group(1)
    i = start
    while True:
        i = text.index(">", i + 1)
        if text[i - 1] != "/":
            return tag, i + 1
        i += 1


def element_span(text, start):
    """(start, end, tag) of the whole element beginning at `start`."""
    tag, after_open = open_tag(text, start)
    if text[after_open - 2:after_open] == "/>":
        return start, after_open, tag
    if tag.startswith("!--"):
        end = text.index("-->", after_open) + 3
        return start, end, tag
    close = f"</{tag}>"
    depth = 1
    i = after_open
    while depth:
        nxt = text.find(f"<{tag}", i)
        clo = text.find(close, i)
        if clo == -1:
            raise ValueError(f"unclosed <{tag}>")
        if nxt != -1 and nxt < clo:
            _, end = open_tag(text, nxt)
            if text[end - 2:end] == "/>":
                i = end
            else:
                depth += 1
                i = end
        else:
            depth -= 1
            i = clo + len(close)
    return start, i, tag


def find_element(text, opener):
    """The whole element whose opening tag matches `opener` exactly."""
    start = text.index(opener)
    return element_span(text, start)


def indent(block, spaces):
    """Sit a moved block inside <defs> without reflowing its attribute lines.

    The first line goes to column `spaces`. Each further line keeps the extra
    indentation the source file gave it -- so a <g>/<path>'s attributes stay in
    their original relative positions, just shifted as a whole.
    """
    lines = block.split("\n")
    lead = len(lines[0]) - len(lines[0].lstrip(" "))
    pad = " " * spaces
    out = [pad + lines[0].lstrip(" ")]
    for ln in lines[1:]:
        out.append(pad + ln[lead:] if len(ln) >= lead else ln)
    return "\n".join(out)


def attr_of(attrs, name, default=None):
    m = re.search(rf'\b{re.escape(name)}\s*=\s*"([^"]*)"', attrs)
    return m.group(1) if m else default


def strip_namespaced(block):
    """Drop inkscape:*/sodipodi:* attributes; return what was removed."""
    removed = []

    def drop(m):
        val = m.group("value")
        if m.group("name").startswith(("inkscape:", "sodipodi:")):
            removed.append(m.group("name"))
            return ""
        return f'{m.group("name")}="{val}"'
    out = ATTR_RE.sub(drop, block)
    return re.sub(r"[ \t]+\n", "\n", out), removed


def read_text(path):
    """Read as text without newline translation (.gitattributes pins LF)."""
    return path.read_text(encoding="utf-8", newline="")


def write_text(path, text):
    path.write_text(text, encoding="utf-8", newline="")


def source_frame(path):
    """(width, height, viewBox) off a source file's root <svg>."""
    root = ET.parse(path).getroot()
    return root.get("width"), root.get("height"), root.get("viewBox")


def source_text(path):
    try:
        return read_text(path)
    except FileNotFoundError:
        raise SystemExit(
            f"{path.name} no longer exists -- this script needs the "
            f"pre-consolidation mechanical/templates/individuals/ tree")


# --------------------------------------------------------------------------
# Inlining
# --------------------------------------------------------------------------

def hoist_def(src_text, def_id, attrs_extra=""):
    """The `<g id="def_id">…</g>` block, with namespaced attrs stripped.

    The file's own line breaking is preserved, so both

        <g\\n   id="X-def">
        <g id="X-def">

    work. `attrs_extra` is injected as new lines right after the id.
    """
    m = re.search(rf'<g\b[^>]*?\bid="{re.escape(def_id)}"', src_text)
    if not m:
        raise ValueError(f"no <g id={def_id!r}> in source")
    start = src_text.rindex("<", 0, m.start() + 1)
    block = src_text[slice(*element_span(src_text, start)[:2])]
    block, removed = strip_namespaced(block)
    if attrs_extra:
        block = re.sub(rf'(\bid="{re.escape(def_id)}")', rf"\1{attrs_extra}", block, count=1)
    return block, removed


def hoist_reference(href, sources, defs_markup, hoisted, stripped):
    """Hoist the target of an external href into defs; return its internal id.

    The def group is copied verbatim and gains data-wh/data-vb (the frame the
    print script needs). Calling it twice for the same target is a no-op.
    """
    fname, frag = href.split("#", 1)
    src = IND / Path(fname).name
    if not src.exists():
        raise SystemExit(f"unresolved reference: {href}")
    if frag in hoisted:
        return frag

    src_text = sources.setdefault(src, source_text(src))
    extra = ""
    if frag.endswith("-def"):
        w, h, vb = source_frame(src)
        if not (w and h and vb):
            raise SystemExit(f"{src.name}: missing width/height/viewBox")
        # Bare numbers, like viewBox: the scripts parse these with parse_mm().
        w = w.replace("mm", "").strip()
        h = h.replace("mm", "").strip()
        extra = (f'\n   data-wh="{w} {h}"'
                 f'\n   data-vb="{vb}"')
    block, removed = hoist_def(src_text, frag, extra)
    stripped.extend(f"{src.name}:{r}" for r in removed)
    hoisted[frag] = block
    defs_markup.append(block)
    return frag


def build_defs(agg_text, sources):
    """Move every def group the aggregate references into <defs>."""
    entries, rewrites, hoisted, stripped = [], [], {}, []

    for m in USE_RE.finditer(agg_text):
        href = attr_of(m.group(0), "href")
        if not href or "#" not in href:
            continue
        fname = href.split("#", 1)[0]
        if not fname:
            continue
        if Path(fname).name == "outline-toplines.svg":
            # Handled by build_placement(), which re-homes its three groups
            # under the placement- id prefix and recurses into their own <use>s.
            continue
        frag = hoist_reference(href, sources, entries, hoisted, stripped)
        rewrites.append((href, f"#{frag}"))

    return entries, rewrites, hoisted, stripped


def build_placement(sources):
    """Re-home outline-toplines' three groups; retarget its inner <use>s.

    The eight *-topline defs are only reachable from here -- the aggregate body
    never references them directly -- so they are hoisted as we walk the group.
    """
    src = IND / "outline-toplines.svg"
    up_src = IND / "upper-outline.svg"
    text = sources.setdefault(src, source_text(src))
    up_text = sources.setdefault(up_src, source_text(up_src))

    topline_defs, hoisted, stripped = [], {}, []
    groups = []

    top, removed = hoist_def(text, "top-lines")
    stripped.extend(f"outline-toplines.svg:{r}" for r in removed)
    top = top.replace('id="top-lines"', f'id="{PLACEMENT_PREFIX}top-lines"', 1)
    for um in list(USE_RE.finditer(top)):
        chunk = um.group(0)
        h = attr_of(chunk, "href")
        if not h or "#" not in h:
            continue
        frag = hoist_reference(h, sources, topline_defs, hoisted, stripped)
        new = chunk.replace(f'href="{h}"', f'href="#{frag}"', 1)
        old_id = attr_of(chunk, "id")
        if old_id:
            new = new.replace(f'id="{old_id}"',
                              f'id="{TOPLINE_USE_PREFIX}{old_id}"', 1)
        top = top.replace(chunk, new, 1)
    groups.append(top)

    total, removed = hoist_def(text, "total-outline")
    stripped.extend(f"outline-toplines.svg:{r}" for r in removed)
    total = total.replace('id="total-outline"',
                          f'id="{PLACEMENT_PREFIX}total-outline"', 1)
    for um in list(USE_RE.finditer(total)):
        chunk = um.group(0)
        h = attr_of(chunk, "href")
        if not h or "#" not in h:
            continue
        fname, frag = h.split("#", 1)
        new = chunk.replace(f'href="{h}"', f'href="#{frag}"', 1)
        new = new.replace(f'id="{frag}"', f'id="{UPPER_USE_ID}"', 1)
        total = total.replace(chunk, new, 1)
    groups.append(total)

    upper, removed = hoist_def(up_text, "upper-outline-def")
    stripped.extend(f"upper-outline.svg:{r}" for r in removed)
    # upper-outline.svg's path carries id="upper-outline", which the <use> in
    # total-outline also carried before it was renamed. Follow the convention
    # the other feathers use -- the path is "<feather>-outline".
    upper = upper.replace('id="upper-outline"', 'id="upper-outline-path"', 1)
    groups.append(upper)

    return topline_defs, groups, set(hoisted), stripped


def restructure(text, entries, rewrites):
    """Swap the empty <defs/> for a populated one and retarget the hrefs."""
    if "<defs" not in text:
        raise SystemExit("no <defs> in the aggregate to fill")

    body = "\n".join(indent(e, 6) for e in entries)
    defs_block = f'<defs\n     id="defs1">\n{body}\n  </defs>'

    text, n = re.subn(r"<defs\b[^>]*/>", lambda _: defs_block, text, count=1)
    if n != 1:
        raise SystemExit("could not replace the empty <defs/> element")

    for old, new in rewrites:
        needle = f'href="{old}"'
        if text.count(needle) != 1:
            raise SystemExit(f"expected exactly one {needle!r}, found {text.count(needle)}")
        text = text.replace(needle, f'href="{new}"')

    return text


def check(text, expect_defs):
    """Assert the consolidated file is self-contained, id-clean and complete."""
    external = [m.group(0)[:80] for m in USE_RE.finditer(text)
                if (h := attr_of(m.group(0), "href")) and not h.startswith("#")]
    if external:
        raise SystemExit(f"external references remain: {external[:3]}")

    root = ET.fromstring(text)
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"duplicate ids: {dupes}")

    missing = [d for d in expect_defs if d not in ids]
    if missing:
        raise SystemExit(f"def groups not hoisted: {missing}")

    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == "use":
            h = el.get("href") or ""
            if h.startswith("#") and h[1:] not in ids:
                raise SystemExit(f"dangling internal reference: {h}")

    # Def groups are copied out into the logical pages, so the prefixed
    # attributes the editor left on them must be gone. (The document's own
    # placement elements keep their inkscape:label -- they are never copied.)
    defs = root.find("{http://www.w3.org/2000/svg}defs")
    if defs is None:
        raise SystemExit("no <defs> in the consolidated document")
    for el in defs.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        for name in el.attrib:
            if name.startswith(f"{{{INKSCAPE}}}") or name.startswith(f"{{{SODIPODI}}}"):
                raise SystemExit(f"prefixed attribute survived: {tag}@{name}")
    return len(ids)


def main():
    ap = argparse.ArgumentParser(description="inline individuals/ into the aggregate")
    ap.add_argument("--out", type=Path, default=AGG,
                    help="where to write (default: the aggregate itself)")
    args = ap.parse_args()

    agg_text = read_text(AGG)
    sources = {}

    defs_entries, rewrites, hoisted, stripped = build_defs(agg_text, sources)
    topline_defs, placement_groups, topline_ids, placement_stripped = build_placement(sources)

    # build_defs() deliberately skips outline-toplines.svg; the one <use> that
    # pulls it in is retargeted here, at the group build_placement() re-homed.
    for m in USE_RE.finditer(agg_text):
        href = attr_of(m.group(0), "href")
        if href and href.startswith("individuals/outline-toplines.svg#"):
            rewrites.append(
                (href, f"#{PLACEMENT_PREFIX}{href.split('#', 1)[1]}"))

    entries = (
        ["<!-- Per-feather geometry, copied verbatim from the old individuals/\n"
         "       files. data-wh / data-vb carry the frame the print script needs;\n"
         "       the <use>s below carry the placement. -->"]
        + defs_entries
        + ["<!-- Per-topline alignment geometry. -->"]
        + topline_defs
        + ["<!-- The whole-wing placement template, re-homed from outline-toplines.svg.\n"
           "       The placement- id prefix keeps its ids from colliding. -->"]
        + placement_groups)

    out = restructure(agg_text, entries, rewrites)
    n_ids = check(out, set(hoisted) | set(topline_ids))

    write_text(args.out, out)
    print(f"hoisted {len(hoisted)} feather defs + {len(topline_ids)} topline defs "
          f"+ {len(placement_groups)} placement groups")
    print(f"retargeted {len(rewrites)} hrefs")
    print(f"stripped {len(stripped) + len(placement_stripped)} namespaced attributes")
    print(f"{n_ids} ids, no duplicates; wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
