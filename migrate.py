#!/usr/bin/env python3
"""
migrate.py -- one-time migration from the old script pipeline to the new
declarative pipeline.

Reads the current feather geometry (via make_logical_pages.py's readers) and
writes two artifacts:

  templates/feathers-source.svg   prepared source: placement-ready groups
  templates/layout.yaml           the spec: sheets + elements, transcribed

This script is the *transcription* step from declarative-layout-plan.md. It is
meant to be run once; afterwards the spec is the hand-editable artifact and
assemble_sheets.py is the runtime. Nothing here is byte-for-byte magic -- it
captures today's layout as explicit data so you can edit it.
"""

from pathlib import Path

import yaml

import make_logical_pages as mlp

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
SRC_OUT = TEMPLATES / "feathers-source.svg"
SPEC_OUT = TEMPLATES / "layout.yaml"

GAP = mlp.GAP
MAX_WIDTH = mlp.MAX_WIDTH
PAD = mlp.PAD
LABEL_BAND = mlp.LABEL_BAND
BAND_LABEL_Y = mlp.BAND_LABEL_Y

OUTPUT_STYLE = """\
.outline { stroke: #000000; stroke-width: 0.5; fill: none; }
.guide { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: round; stroke-linejoin: round; }
.label { font-family: sans-serif; fill: #000000; text-anchor: middle; dominant-baseline: middle; font-size: 5; }
.title { font-family: sans-serif; fill: #000000; font-size: 9; text-anchor: middle; font-weight: bold; }
.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
.cal { stroke: #000000; stroke-width: 0.5; }
.minor { stroke: #000000; stroke-width: 0.15; }
.major { stroke: #000000; stroke-width: 0.5; }
.num { font-family: sans-serif; fill: #000000; font-size: 3.5; text-anchor: middle; }
.caltext { font-family: sans-serif; fill: #000000; font-size: 6; text-anchor: middle; font-weight: bold; }
.arrow { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: butt; stroke-linejoin: miter; }
.arrowhead { fill: #000000; stroke: none; }
"""


def fmt(x):
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def ruler(length, major_step, major_labels, minor_step, minor_count, unit):
    """A calibration ruler in its own frame: bar at y=0, labels above/below."""
    e = []
    e.append(f'<line class="cal" x1="0" y1="0" x2="{fmt(length)}" y2="0"/>')
    for k in range(minor_count + 1):
        x = k * minor_step
        e.append(f'<line class="minor" x1="{fmt(x)}" y1="-1.2" x2="{fmt(x)}" y2="1.2"/>')
    for k, label in enumerate(major_labels):
        x = k * major_step
        e.append(f'<line class="major" x1="{fmt(x)}" y1="-3" x2="{fmt(x)}" y2="3"/>')
        e.append(f'<text class="num" x="{fmt(x)}" y="7">{label}</text>')
    e.append(f'<text class="caltext" x="{fmt(length / 2)}" y="-9">{unit}</text>')
    return "".join(e)


def flow_layout(sizes, max_width=MAX_WIDTH, pad=PAD):
    """Left-to-right wrapping layout; rows centered in max_width.

    Returns ([(x, y, w, h), ...], total_height)."""
    rows = []
    cur = []
    cur_w = 0.0
    for w, h in sizes:
        add = w if not cur else pad + w
        if cur and cur_w + add > max_width:
            rows.append(cur)
            cur = []
            cur_w = 0.0
            add = w
        cur.append((w, h))
        cur_w += add
    if cur:
        rows.append(cur)

    out = []
    y = 0.0
    for row in rows:
        row_w = sum(w for w, _ in row) + pad * (len(row) - 1)
        row_h = max(h for _, h in row)
        x = (max_width - row_w) / 2.0
        for w, h in row:
            out.append((x, y, w, h))
            x += w + pad
        y += row_h + pad
    total_h = (y - pad) if rows else 0.0
    return out, total_h


def feather_groups():
    """Clean placement-ready groups for every feather the manifest names."""
    names = []
    for section in mlp.SECTIONS:
        names += list(section.items)
    feather_names = [n for n in names if n != mlp.PLACEMENT_GROUP and not n.endswith("-align")]

    out = []
    for name in feather_names:
        f = mlp.read_feather(name)
        d = mlp._path_d(name, mlp._def_group(name))
        rt = mlp.right_transform(f)
        out.append(f'<g id="{name}"><path class="outline" d="{esc(d)}" transform="{rt}"/></g>')
    return out


def build_source_svg():
    groups = feather_groups()

    # calibration rulers
    metric = ruler(100.0, 10.0, [str(i * 10) for i in range(11)], 1.0, 100, "100 mm")
    us = ruler(101.6, 25.4, ["0", "1", "2", "3", "4"], 25.4 / 8.0, 32, "4 in  (101.6 mm)")
    groups.append(f'<g id="calibration-ruler-metric">{metric}</g>')
    groups.append(f'<g id="calibration-ruler-us">{us}</g>')

    # whole-wing placement template
    item = mlp.read_placement()
    groups.append(f'<g id="{mlp.PLACEMENT_GROUP}">{item.body}</g>')

    # alignment overlays
    for name in [n for s in mlp.SECTIONS for n in s.items if n.endswith("-align")]:
        el = mlp._def_group(name)
        ai = mlp.read_align(name, el)
        groups.append(f'<g id="{name}-geometry">{ai.body}</g>')
        groups.append(f'<g id="{name}-origins">{ai.origins}</g>')
        groups.append(f'<g id="{name}-origins-flipped">{ai.origins_flipped}</g>')

    body = "\n".join(f"  {g}" for g in groups)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1mm" height="1mm" '
            f'viewBox="0 0 1 1">\n{body}\n</svg>\n')


def pair_spec(name, Wp, Hp, x, y):
    """Elements for one mirrored pair, placed with its top-left at (x, y)."""
    elems = [
        {"source-id": f'//g[@id="{name}"]/path',
         "position": {"x": round(x + Wp, 3), "y": round(y, 3)},
         "transform": {"scale": [-1.0, 1.0]}},
        {"source-id": f'//g[@id="{name}"]/path',
         "position": {"x": round(x + Wp + GAP, 3), "y": round(y, 3)}},
        {"text": f"{name}-left",
         "position": {"x": round(x + Wp / 2.0, 3), "y": round(y + Hp / 2.0, 3)}},
        {"text": f"{name}-right",
         "position": {"x": round(x + Wp + GAP + Wp / 2.0, 3), "y": round(y + Hp / 2.0, 3)}},
    ]
    return elems


def feather_sheets():
    sheets = []
    for section in mlp.SECTIONS:
        if type(section).__name__ not in ("MirroredPairs", "MirroredPairsRot90"):
            continue
        # Build the pair fragments to know their placed sizes.
        ctx = mlp.Context(frags=_frags(section.items), raw=_raw(section.items))
        sizes = []
        for name in section.items:
            item = ctx.raw[name]
            Wp, Hp = item.W, item.H
            sizes.append((2.0 * Wp + GAP, Hp))
        positions, total_h = flow_layout(sizes)
        elems = []
        for (name, (x, y, w, h)) in zip(section.items, positions):
            Wp, Hp = ctx.raw[name].W, ctx.raw[name].H
            elems += pair_spec(name, Wp, Hp, x, y)
        sheets.append({
            "title": "/".join(section.items),
            "dimensions": {"width": round(MAX_WIDTH, 3), "height": round(total_h, 3)},
            "elements": elems,
        })
    return sheets


def _frags(items):
    frags = {}
    for name in items:
        f = mlp.read_feather(name)
        item = mlp.feather_item(f)
        frag, w, h = mlp.build_pair(item)
        frags[name] = (frag, w, h)
    return frags


def _raw(items):
    raw = {}
    for name in items:
        f = mlp.read_feather(name)
        raw[name] = mlp.feather_item(f)
    return raw


def placement_sheets():
    """outline-toplines -> two sheets (right, then left)."""
    item = mlp.read_placement()
    W, H = item.W, item.H
    xr = W / 2.0
    right = {
        "title": "outline-toplines-right",
        "dimensions": {"width": round(MAX_WIDTH, 3), "height": round(H, 3)},
        "elements": [
            {"source-id": f'//g[@id="{mlp.PLACEMENT_GROUP}"]', "position": {"x": 0, "y": 0}},
            {"text": "outline-toplines right", "position": {"x": round(xr, 3), "y": 3}},
        ],
    }
    left = {
        "title": "outline-toplines-left",
        "dimensions": {"width": round(MAX_WIDTH, 3), "height": round(H, 3)},
        "elements": [
            {"source-id": f'//g[@id="{mlp.PLACEMENT_GROUP}"]',
             "position": {"x": round(W, 3), "y": 0},
             "transform": {"scale": [-1.0, 1.0]}},
            {"text": "outline-toplines left", "position": {"x": round(xr, 3), "y": 3}},
        ],
    }
    return [right, left]


def align_sheets():
    sheets = []
    names = [n for s in mlp.SECTIONS for n in s.items if n.endswith("-align")]
    for name in names:
        el = mlp._def_group(name)
        ai = mlp.read_align(name, el)
        W, H = ai.W, ai.H
        down = LABEL_BAND - 1.0
        note_x = W / 2.0
        left = {
            "title": f"{name}-left",
            "dimensions": {"width": round(W, 3), "height": round(H + down, 3)},
            "elements": [
                {"source-id": f'//g[@id="{name}-geometry"]', "position": {"x": 0, "y": round(down, 3)}},
                {"source-id": f'//g[@id="{name}-origins"]', "position": {"x": 0, "y": round(down, 3)}},
                {"text": name, "position": {"x": round(note_x, 3), "y": round(BAND_LABEL_Y, 3)}},
            ],
        }
        right = {
            "title": f"{name}-right",
            "dimensions": {"width": round(W, 3), "height": round(H + down, 3)},
            "elements": [
                {"source-id": f'//g[@id="{name}-geometry"]',
                 "position": {"x": round(W, 3), "y": round(down, 3)},
                 "transform": {"scale": [-1.0, 1.0]}},
                {"source-id": f'//g[@id="{name}-origins-flipped"]', "position": {"x": 0, "y": round(down, 3)}},
                {"text": name, "position": {"x": round(note_x, 3), "y": round(BAND_LABEL_Y, 3)}},
            ],
        }
        sheets += [left, right]
    return sheets


def build_spec():
    cover = {
        "title": "cover",
        "dimensions": {"width": round(MAX_WIDTH, 3), "height": 205.9},
        "elements": [
            {"text": "Feather templates — mirrored pairs",
             "position": {"x": 130, "y": 25}, "class": "title"},
            {"text": "Print at 100% / actual size. Do not fit or scale. Verify with the bars below.",
             "position": {"x": 130, "y": 36}, "class": "note"},
            {"source-id": '//g[@id="calibration-ruler-metric"]', "position": {"x": 40, "y": 70}},
            {"source-id": '//g[@id="calibration-ruler-us"]', "position": {"x": 40, "y": 115}},
        ],
    }

    spec = {
        "source-file": "feathers-aggregate.svg",
        "paper": {
            "trim": {"width": 279.4, "height": 215.9},
            "safe-area": {"width": 269.4, "height": 205.9},
            "overlap": 12.0,
        },
        "output-style": OUTPUT_STYLE,
        "sheets": [cover] + feather_sheets() + placement_sheets() + align_sheets(),
    }
    return spec


def main():
    SRC_OUT.write_text(build_source_svg(), encoding="utf-8")
    spec = build_spec()
    SPEC_OUT.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True,
                                       default_flow_style=False, width=1000),
                        encoding="utf-8")
    print(f"wrote {SRC_OUT}")
    print(f"wrote {SPEC_OUT} ({len(spec['sheets'])} sheets)")


if __name__ == "__main__":
    main()
