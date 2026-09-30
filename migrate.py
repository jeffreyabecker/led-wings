#!/usr/bin/env python3
"""
migrate.py -- one-time transcription: write templates/layout.yaml from the
corrected feathers-aggregate.svg.

The source is now placement-ready (paths origin-framed, B family still
horizontal and marked data-rot90="1"), so this only computes sizes and writes
explicit sheet declarations. It makes no layout decisions beyond transcribing
today's grouping; the spec is the hand-editable artifact afterwards.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

import prepare_source as ps

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
AGG = TEMPLATES / "feathers-aggregate.svg"
SPEC = TEMPLATES / "layout.yaml"
NS = "{http://www.w3.org/2000/svg}"

GAP = 10.0
MAX_WIDTH = 260.0
PAD = 8.0
COVER_W = 260.0
COVER_H = 205.9

OUTPUT_STYLE = """\
.outline { stroke: #000000; stroke-width: 0.5; fill: none; }
.guide { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: round; stroke-linejoin: round; }
.arrow { stroke: #000000; stroke-width: 0.264583; fill: none; stroke-linecap: butt; stroke-linejoin: miter; }
.mark { fill: #000000; stroke: none; }
.label { font-family: sans-serif; fill: #000000; text-anchor: middle; dominant-baseline: middle; font-size: 5; }
.title { font-family: sans-serif; fill: #000000; font-size: 9; text-anchor: middle; font-weight: bold; }
.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }
.cal { stroke: #000000; stroke-width: 0.5; }
.minor { stroke: #000000; stroke-width: 0.15; }
.major { stroke: #000000; stroke-width: 0.5; }
.num { font-family: sans-serif; fill: #000000; font-size: 3.5; text-anchor: middle; }
.caltext { font-family: sans-serif; fill: #000000; font-size: 6; text-anchor: middle; font-weight: bold; }
"""

# Ordered section manifest, mirroring the old SECTIONS list.
SECTIONS = [
    ("cover", None),
    ("pair", ["P1"]), ("pair", ["P2"]), ("pair", ["P3"]), ("pair", ["P4"]), ("pair", ["P5"]),
    ("pair", ["S1"]), ("pair", ["S2"]), ("pair", ["S3"]), ("pair", ["S4"]),
    ("pair", ["B1"]), ("pair", ["B2"]), ("pair", ["B3"]),
    ("pair", ["A1", "A2", "A3"]),
    ("pair", ["PC1", "PC2"]),
    ("pair", ["SC1", "SC2"]), ("pair", ["SC3"]), ("pair", ["SC4"]),
    ("pair", ["MC1", "MC2"]), ("pair", ["MC3", "MC4"]),
    ("pair", ["LC1", "LC2", "LC3"]),
    ("assembly", None),
    ("align", ["B-align", "P-align", "PC-align", "A-align", "SC-align", "MC-align", "LC-align", "S-align"]),
]


def fmt(x):
    s = f"{float(x):.6f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", "-0."):
        return "0"
    return s


def index_by_id(root):
    return {e.get("id"): e for e in root.iter() if e.get("id")}


def extent(group):
    """(w, h) of a group's origin-framed ink (control-point bbox top-right)."""
    box = ps.ink_bbox(group)
    assert box is not None, f"{group.get('id')}: no ink"
    return box[2], box[3]


def flow_layout(sizes, max_width=MAX_WIDTH, pad=PAD):
    """Left-to-right wrapping layout; rows centered in max_width."""
    rows, cur, cur_w = [], [], 0.0
    for w, h in sizes:
        add = w if not cur else pad + w
        if cur and cur_w + add > max_width:
            rows.append(cur)
            cur, cur_w = [], 0.0
            add = w
        cur.append((w, h))
        cur_w += add
    if cur:
        rows.append(cur)

    out, y = [], 0.0
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


def pair_elements(name, w, h, rot90, x, y):
    """Elements for one mirrored pair at (x, y); w/h are the origin-framed extents.
    rot90: the feather is stored horizontal (B family) and is rotated in place."""
    if not rot90:
        pw, ph = w, h
        elems = [
            {"source-id": f'//g[@id="{name}"]/path',
             "position": {"x": round(x + w, 3), "y": round(y, 3)},
             "transform": {"scale": [-1.0, 1.0]}},
            {"source-id": f'//g[@id="{name}"]/path',
             "position": {"x": round(x + w + GAP, 3), "y": round(y, 3)}},
            {"text": f"{name}-left", "position": {"x": round(x + w / 2, 3), "y": round(y + h / 2, 3)}},
            {"text": f"{name}-right", "position": {"x": round(x + w + GAP + w / 2, 3), "y": round(y + h / 2, 3)}},
        ]
        return elems, 2.0 * w + GAP, h

    # B family: horizontal, rotated 90 in place. placed width = h, placed height = w.
    elems = [
        {"source-id": f'//g[@id="{name}"]/path',
         "position": {"x": round(x + h, 3), "y": round(y + w, 3)},
         "transform": {"rotate": 90, "scale": [-1.0, 1.0]}},
        {"source-id": f'//g[@id="{name}"]/path',
         "position": {"x": round(x + 2 * h + GAP, 3), "y": round(y, 3)},
         "transform": {"rotate": 90}},
        {"text": f"{name}-left", "position": {"x": round(x + h / 2, 3), "y": round(y + w / 2, 3)}},
        {"text": f"{name}-right", "position": {"x": round(x + 1.5 * h + GAP, 3), "y": round(y + w / 2, 3)}},
    ]
    return elems, 2.0 * h + GAP, w


def feather_sheets(by_id):
    sheets = []
    for kind, items in SECTIONS:
        if kind != "pair":
            continue
        sizes = []
        for name in items:
            g = by_id[name]
            w, h = extent(g)
            rot90 = (g.get("data-rot90") or "") == "1"
            _, pw, ph = pair_elements(name, w, h, rot90, 0, 0)
            sizes.append((pw, ph))
        positions, total_h = flow_layout(sizes)
        elems = []
        for name, (x, y, _, _) in zip(items, positions):
            g = by_id[name]
            w, h = extent(g)
            rot90 = (g.get("data-rot90") or "") == "1"
            e, _, _ = pair_elements(name, w, h, rot90, x, y)
            elems += e
        sheets.append({
            "title": "/".join(items),
            "dimensions": {"width": round(MAX_WIDTH, 3), "height": round(total_h, 3)},
            "elements": elems,
        })
    return sheets


def assembly_sheets(by_id):
    g = by_id["assembly-template"]
    W, H = extent(g)
    label_x = W / 2
    return [
        {"title": "assembly-template-right",
         "dimensions": {"width": round(W, 3), "height": round(H, 3)},
         "elements": [
             {"source-id": '//g[@id="assembly-template"]/g', "position": {"x": 0, "y": 0}},
             {"text": "assembly-template right", "position": {"x": round(label_x, 3), "y": 3}},
         ]},
        {"title": "assembly-template-left",
         "dimensions": {"width": round(W, 3), "height": round(H, 3)},
         "elements": [
             {"source-id": '//g[@id="assembly-template"]/g',
              "position": {"x": round(W, 3), "y": 0},
              "transform": {"scale": [-1.0, 1.0]}},
             {"text": "assembly-template left", "position": {"x": round(label_x, 3), "y": 3}},
         ]},
    ]


def align_sheets(by_id):
    sheets = []
    for kind, names in SECTIONS:
        if kind != "align":
            continue
        for name in names:
            g = by_id[name]
            W, H = extent(g)
            sheets.append({
                "title": f"{name}-left",
                "dimensions": {"width": round(W, 3), "height": round(H, 3)},
                "elements": [
                    {"source-id": f'//g[@id="{name}"]/g', "position": {"x": 0, "y": 0}},
                    {"text": name, "position": {"x": round(W / 2, 3), "y": 3}},
                ]})
            sheets.append({
                "title": f"{name}-right",
                "dimensions": {"width": round(W, 3), "height": round(H, 3)},
                "elements": [
                    {"source-id": f'//g[@id="{name}"]/g',
                     "position": {"x": round(W, 3), "y": 0},
                     "transform": {"scale": [-1.0, 1.0]}},
                    {"text": name, "position": {"x": round(W / 2, 3), "y": 3}},
                ]})
    return sheets


def cover_sheet():
    return {
        "title": "cover",
        "dimensions": {"width": COVER_W, "height": COVER_H},
        "elements": [
            {"text": "Feather templates — mirrored pairs",
             "position": {"x": 130, "y": 25}, "class": "title"},
            {"text": "Print at 100% / actual size. Do not fit or scale. Verify with the bars below.",
             "position": {"x": 130, "y": 36}, "class": "note"},
            {"source-id": '//g[@id="calibration-ruler-metric"]', "position": {"x": 40, "y": 70}},
            {"source-id": '//g[@id="calibration-ruler-us"]', "position": {"x": 40, "y": 115}},
        ],
    }


def build_spec():
    root = ET.parse(AGG).getroot()
    by_id = index_by_id(root)
    spec = {
        "source-file": "feathers-aggregate.svg",
        "paper": {
            "trim": {"width": 279.4, "height": 215.9},
            "safe-area": {"width": 269.4, "height": 205.9},
            "overlap": 12.0,
        },
        "output-style": OUTPUT_STYLE,
        "sheets": [cover_sheet()] + feather_sheets(by_id) + assembly_sheets(by_id) + align_sheets(by_id),
    }
    return spec


def main():
    spec = build_spec()
    SPEC.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True,
                                   default_flow_style=False, width=1000),
                    encoding="utf-8")
    print(f"wrote {SPEC} ({len(spec['sheets'])} sheets)")


if __name__ == "__main__":
    main()
