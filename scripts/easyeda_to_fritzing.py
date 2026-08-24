#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a Fritzing part (.fzpz) from an EasyEDA/LCSC part.

Two input modes
---------------
1. Fetch from the EasyEDA API using an LCSC part number (recommended):
       python easyeda_to_fritzing.py --lcsc C8678
       python easyeda_to_fritzing.py C8678.html      # id is read from the filename
   The JSON response is used directly: the schematic symbol is parsed from the
   "svg" string, and the footprint pads are read straight from the dataStr
   "shape" list (no intermediate SVG files, no footprint SVG rendering).

2. From local EasyEDA SVG exports:
       python easyeda_to_fritzing.py symbol.svg footprint.svg

Coordinate mapping
------------------
EasyEDA SVG exports use 1 unit = 10 mil (0.254 mm); Fritzing views use mils,
so SVG coordinates are scaled by 10. The API dataStr coordinates are assumed
to be mils already (verify with --dump: a 0.8 mm pad pitch reads ~31.5).
Breadboard + icon views are synthesised (SMD parts are not breadboard parts).

Output
------
Writes <dir-of-source>/fritzing/<name>.fzpz (File -> Import in Fritzing).
Loose files are built in <dir-of-source>/fritzing/<name>/ then removed by
default; pass --keep-exploded to keep them:

    part.<name>.fzp
    svg.<name>.breadboard_breadboard.svg
    svg.<name>.schematic_schematic.svg
    svg.<name>.pcb_pcb.svg
    svg.<name>.icon_icon.svg

Options
-------
    --lcsc ID        LCSC part number to fetch (e.g. C8678)
    --name NAME      override the part name
    --out DIR        override the output directory
    --keep-exploded  keep the loose .fzp + view SVGs
    --dump PATH      save the raw EasyEDA API JSON response (for debugging)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

SCALE = 10.0  # EasyEDA SVG-export units -> Fritzing mils
DATASTR_UNIT_TO_MIL = 1.0  # API dataStr unit -> mil (assumed; verify via --dump)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def local(tag):
    """'{http://www.w3.org/2000/svg}rect' -> 'rect'"""
    return tag.rsplit("}", 1)[-1]


def parse_c_para(text):
    """Split EasyEDA ``key`value`key`value`...`` metadata into a dict."""
    d = {}
    parts = text.split("`")
    for i in range(0, len(parts) - 1, 2):
        if parts[i]:
            d[parts[i]] = parts[i + 1]
    return d


def fnum(v):
    """Format a scaled mil coordinate compactly (no trailing zeros)."""
    s = "%.2f" % v
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def xmlescape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def scale_d(d):
    """Multiply every number in an SVG path 'd' string by SCALE."""
    def repl(m):
        return fnum(float(m.group(0)) * SCALE)

    return re.sub(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", repl, d)


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #
def _symbol_from_root(root):
    """Return (name, pins, body_shapes, meta) from an EasyEDA symbol <svg> root."""
    name = None
    pins = []
    body = []
    meta = {}

    for g in root.iter():
        if local(g.tag) != "g":
            continue
        a = g.attrib

        if "c_para" in a:
            para = parse_c_para(a["c_para"])
            meta.update(para)
            if "name" in para:
                name = para["name"]

        if a.get("c_partid") == "part_pin":
            num = int(a.get("c_spicepin", "0"))
            ox, oy = (float(v) for v in a.get("c_origin", "0,0").split(","))
            rotation = int(float(a.get("c_rotation", "0")))
            label = None
            color = "#000000"
            for child in g.iter():
                t = local(child.tag)
                ca = child.attrib
                if t == "text":
                    txt = (child.text or "").strip()
                    if txt and txt != a.get("c_spicepin"):
                        label = txt
                elif t == "path" and ca.get("stroke"):
                    color = ca["stroke"]
            pins.append(
                dict(num=num, name=label or str(num), x=ox, y=oy,
                     rotation=rotation, color=color)
            )

    # body = visible-outline rects outside pin groups (skip grid/bounding rects)
    for el in root.iter():
        t = local(el.tag)
        a = el.attrib
        if t == "rect" and a.get("stroke") not in (None, "none") and a.get("fill") == "none":
            if a.get("id", "").startswith(("grid",)):
                continue
            body.append(("rect", a))

    pins.sort(key=lambda p: p["num"])
    return name, pins, body, meta


def parse_symbol(path):
    """Return (name, pins, body_shapes, meta) from an EasyEDA symbol.svg file."""
    return _symbol_from_root(ET.parse(path).getroot())


def parse_symbol_str(svg_string):
    """Return (name, pins, body_shapes, meta) from an EasyEDA symbol SVG string."""
    return _symbol_from_root(ET.fromstring(svg_string))


def parse_footprint(path):
    """Return (pads, silkscreen_shapes) from an EasyEDA footprint.svg."""
    tree = ET.parse(path)
    root = tree.getroot()

    pads = []
    silk = []

    for el in root.iter():
        t = local(el.tag)
        a = el.attrib

        if t == "g" and a.get("c_partid") == "part_pad":
            num = int(a.get("number", "0"))
            ox, oy = (float(v) for v in a.get("c_origin", "0,0").split(","))
            w = float(a.get("c_width", "0"))
            h = float(a.get("c_height", "0"))
            shape = a.get("c_shape", "RECT")
            pads.append(dict(num=num, x=ox, y=oy, w=w, h=h, shape=shape))

        # silkscreen (layer 3) + document/direction marks (layer 12)
        elif a.get("layerid") in ("3", "12"):
            silk.append((t, dict(a)))

    pads.sort(key=lambda p: p["num"])
    return pads, silk


def _find_shape_list(obj):
    """Recursively find the first list stored under a 'shape' key."""
    if isinstance(obj, dict):
        if isinstance(obj.get("shape"), list):
            return obj["shape"]
        for v in obj.values():
            found = _find_shape_list(v)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_shape_list(v)
            if found is not None:
                return found
    return None


def _collect_c_para(obj, out):
    """Merge every EasyEDA 'c_para' (string or list of 'key`value' items) into out."""
    if isinstance(obj, dict):
        cp = obj.get("c_para")
        if isinstance(cp, str):
            out.update(parse_c_para(cp))
        elif isinstance(cp, list):
            for item in cp:
                if isinstance(item, str):
                    out.update(parse_c_para(item))
        for v in obj.values():
            _collect_c_para(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_c_para(v, out)


def parse_footprint_data_str(result):
    """Return pads from an EasyEDA /api/products/{lcsc}/svgs JSON 'result'.

    The footprint is stored as dataStr shape strings:
        PAD~x~y~width~height~layer~net~number~holeR~points~rotation~shape~...
    We read only the PAD entries (silkscreen is skipped here). Coordinates are
    assumed to be in mils (DATASTR_UNIT_TO_MIL) and are converted to the same
    EasyEDA SVG-export units that build_pcb() expects (1 unit = 10 mil).
    """
    shapes = _find_shape_list(result) or []
    pads = []
    for line in shapes:
        if not isinstance(line, str) or not line.startswith("PAD~"):
            continue
        f = line.split("~")
        if len(f) < 8:
            continue
        try:
            x = float(f[1])
            y = float(f[2])
            w = float(f[3])
            h = float(f[4])
            num = int(float(f[7]))
            shape = f[11] if len(f) > 11 else "RECT"
        except (ValueError, IndexError):
            continue
        pads.append(dict(
            num=num,
            x=x * DATASTR_UNIT_TO_MIL / SCALE,
            y=y * DATASTR_UNIT_TO_MIL / SCALE,
            w=w * DATASTR_UNIT_TO_MIL / SCALE,
            h=h * DATASTR_UNIT_TO_MIL / SCALE,
            shape=shape,
        ))
    pads.sort(key=lambda p: p["num"])
    return pads


def fetch_easyeda(lcsc):
    """Download the EasyEDA symbol+footprint JSON for an LCSC part number."""
    url = f"https://easyeda.com/api/products/{lcsc}/svgs"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - report any network/HTTP/JSON error
        sys.exit(f"failed to fetch {url}: {e}")


# --------------------------------------------------------------------------- #
# view builders
# --------------------------------------------------------------------------- #
def _svg(vb, content):
    x, y, w, h = vb
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{fnum(x)} {fnum(y)} {fnum(w)} {fnum(h)}">\n'
        f"{content}\n</svg>\n"
    )


def _terminal(px, py):
    """Small snappable point Fritzing wires attach to."""
    return (
        f'<rect x="{fnum(px - 2)}" y="{fnum(py - 2)}" width="4" height="4" '
        'fill="none" stroke="none"/>'
    )


def build_schematic(pins, body):
    """Schematic view from the EasyEDA symbol (coords already in mils)."""
    GRID = 100.0  # Fritzing schematic snaps wires to a 0.1" grid

    # body bounding box (mil) — fall back to pin bounding box
    if body:
        r = dict(body[0][1])
        bl = float(r["x"]) * SCALE
        bt = float(r["y"]) * SCALE
        br = bl + float(r.get("width", 0)) * SCALE
        bb = bt + float(r.get("height", 0)) * SCALE
    else:
        xs = [p["x"] * SCALE for p in pins]
        ys = [p["y"] * SCALE for p in pins]
        bl, br = min(xs) - 100, max(xs) + 100
        bt, bb = min(ys) - 50, max(ys) + 50

    # translate so the top-left pin lands on the 0.1" grid
    dx = -(min(p["x"] for p in pins) * SCALE) % GRID
    dy = -(min(p["y"] for p in pins) * SCALE) % GRID
    bl, bt, br, bb = bl + dx, bt + dy, br + dx, bb + dy

    parts = []
    for i, p in enumerate(pins):
        tx, ty = p["x"] * SCALE + dx, p["y"] * SCALE + dy
        left = p["rotation"] in (180, -180) or tx < (bl + br) / 2
        x1 = bl if left else br
        x2 = tx
        color = p["color"] or "#880000"
        cid = f"connector{i}"

        parts.append(f'<g id="{cid}pin">')
        parts.append(
            f'<line x1="{fnum(x1)}" y1="{fnum(ty)}" x2="{fnum(x2)}" '
            f'y2="{fnum(ty)}" stroke="{color}" stroke-width="8"/>'
        )
        parts.append("</g>")
        parts.append(f'<g id="{cid}terminal">{_terminal(tx, ty)}</g>')

        # pin name inside the body, number next to the terminal
        if left:
            parts.append(
                f'<text x="{fnum(bl + 15)}" y="{fnum(ty + 14)}" '
                'font-family="Droid Sans" font-size="40" fill="#000000" '
                f'text-anchor="start">{xmlescape(p["name"])}</text>'
            )
            parts.append(
                f'<text x="{fnum(tx + 16)}" y="{fnum(ty - 8)}" '
                'font-family="Droid Sans" font-size="28" fill="#555555" '
                f'text-anchor="start">{p["num"]}</text>'
            )
        else:
            parts.append(
                f'<text x="{fnum(br - 15)}" y="{fnum(ty + 14)}" '
                'font-family="Droid Sans" font-size="40" fill="#000000" '
                f'text-anchor="end">{xmlescape(p["name"])}</text>'
            )
            parts.append(
                f'<text x="{fnum(tx - 16)}" y="{fnum(ty - 8)}" '
                'font-family="Droid Sans" font-size="28" fill="#555555" '
                f'text-anchor="end">{p["num"]}</text>'
            )

    # body rect(s)
    for _, a in body:
        parts.append(
            f'<rect x="{fnum(float(a["x"]) * SCALE + dx)}" y="{fnum(float(a["y"]) * SCALE + dy)}" '
            f'width="{fnum(float(a.get("width", 0)) * SCALE)}" '
            f'height="{fnum(float(a.get("height", 0)) * SCALE)}" '
            f'rx="{fnum(float(a.get("rx", 0)) * SCALE)}" '
            f'stroke="{a.get("stroke", "#880000")}" stroke-width="8" fill="none"/>'
        )

    xs = [p["x"] * SCALE + dx for p in pins] + [bl, br]
    ys = [p["y"] * SCALE + dy for p in pins] + [bt, bb]
    vb = (min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 40, max(ys) - min(ys) + 40)
    return _svg(vb, "<g id=\"schematic\">\n" + "\n".join(parts) + "\n</g>")


def build_pcb(pads, silk):
    """PCB view from the EasyEDA footprint (coords already in mils)."""
    parts = []
    for i, p in enumerate(pads):
        cx, cy = p["x"] * SCALE, p["y"] * SCALE
        w, h = p["w"] * SCALE, p["h"] * SCALE
        x, y = cx - w / 2, cy - h / 2
        cid = f"connector{i}"
        parts.append(
            f'<rect id="{cid}pad" x="{fnum(x)}" y="{fnum(y)}" '
            f'width="{fnum(w)}" height="{fnum(h)}" '
            'fill="#F7BD13" stroke="#8C7B3D" stroke-width="1"/>'
        )

    copper = "\n".join(parts)

    silk_parts = []
    sx = []
    sy = []
    for t, a in silk:
        s = SCALE
        if t == "circle":
            cx, cy, r = float(a["cx"]) * s, float(a["cy"]) * s, float(a["r"]) * s
            sx += [cx - r, cx + r]
            sy += [cy - r, cy + r]
            silk_parts.append(
                f'<circle cx="{fnum(cx)}" cy="{fnum(cy)}" r="{fnum(r)}" '
                f'fill="{a.get("fill", "#FFFFFF")}" '
                f'stroke="{a.get("stroke", "#FFFFFF")}" '
                f'stroke-width="{fnum(float(a.get("stroke-width", 0.5)) * s)}"/>'
            )
        elif t == "path":
            d = scale_d(a.get("d", ""))
            nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", d)]
            if nums:
                sx += [min(nums[0::2]), max(nums[0::2])]
                sy += [min(nums[1::2]), max(nums[1::2])]
            silk_parts.append(
                f'<path d="{d}" fill="{a.get("fill", "#FFFFFF")}" '
                f'stroke="{a.get("stroke", "#FFFFFF")}" '
                f'stroke-width="{fnum(float(a.get("stroke-width", 0.5)) * s)}"/>'
            )
        elif t == "line":
            x1, y1 = float(a["x1"]) * s, float(a["y1"]) * s
            x2, y2 = float(a["x2"]) * s, float(a["y2"]) * s
            sx += [x1, x2]
            sy += [y1, y2]
            silk_parts.append(
                f'<line x1="{fnum(x1)}" y1="{fnum(y1)}" x2="{fnum(x2)}" y2="{fnum(y2)}" '
                f'stroke="{a.get("stroke", "#FFFFFF")}" '
                f'stroke-width="{fnum(float(a.get("stroke-width", 0.5)) * s)}"/>'
            )

    # bounding box over pads + silkscreen
    xs = [(p["x"] - p["w"] / 2) * SCALE for p in pads] + \
         [(p["x"] + p["w"] / 2) * SCALE for p in pads] + sx
    ys = [(p["y"] - p["h"] / 2) * SCALE for p in pads] + \
         [(p["y"] + p["h"] / 2) * SCALE for p in pads] + sy
    vb = (min(xs) - 20, min(ys) - 20, max(xs) - min(xs) + 40, max(ys) - min(ys) + 40)

    content = (
        "<g id=\"pcb\">\n"
        f'<g id="copper0">\n{copper}\n</g>\n'
        f'<g id="silkscreen">\n{"\n".join(silk_parts)}\n</g>\n'
        "</g>"
    )
    return _svg(vb, content)


def build_breadboard(pins):
    """Synthesised breadboard view: DIP-style 2x3 layout on a 0.1" grid."""
    left = [p for p in pins if p["rotation"] in (180, -180)]
    right = [p for p in pins if p["rotation"] not in (180, -180)]
    if not left and not right:  # fall back to first half / second half
        left, right = pins[: len(pins) // 2], pins[len(pins) // 2:]

    bl, bt = 200, 50
    br, bb = 400, 350

    parts = []
    rows = [100, 200, 300]
    for k, group in enumerate((left, right)):
        x1 = bl if k == 0 else br
        tx = 100 if k == 0 else 500
        anchor = "start" if k == 0 else "end"
        for j, p in enumerate(group):
            ty = rows[j] if j < len(rows) else rows[-1] + (j - len(rows) + 1) * 100
            cid = f"connector{p['num'] - 1}"
            parts.append(f'<g id="{cid}pin">')
            parts.append(
                f'<line x1="{x1}" y1="{ty}" x2="{tx}" y2="{ty}" '
                f'stroke="{p["color"] or "#000000"}" stroke-width="20"/>'
            )
            parts.append("</g>")
            parts.append(f'<g id="{cid}terminal">{_terminal(tx, ty)}</g>')
            nx = bl - 12 if k == 0 else br + 12
            parts.append(
                f'<text x="{nx}" y="{ty + 6}" font-family="Droid Sans" font-size="30" '
                f'fill="#000000" text-anchor="{anchor}">{xmlescape(p["name"])}</text>'
            )

    body = (
        f'<rect x="{bl}" y="{bt}" width="{br - bl}" height="{bb - bt}" rx="12" '
        'fill="#303030" stroke="#000000" stroke-width="4"/>'
    )
    vb = (40, 0, 560, 400)
    return _svg(vb, "<g id=\"breadboard\">\n" + body + "\n" + "\n".join(parts) + "\n</g>")


def build_icon(name, pads):
    """Simple icon: body + pad dots."""
    n = len(pads)
    cols = 2 if n >= 4 else 1
    rows = (n + cols - 1) // cols
    size = 132.0
    pad = 18.0
    xs = [size / 2] if cols == 1 else [size * 0.3, size * 0.7]
    ys = [size * (r + 1) / (rows + 1) for r in range(rows)]

    parts = [
        '<rect x="8" y="8" width="116" height="116" rx="14" '
        'fill="#202020" stroke="#000000" stroke-width="3"/>'
    ]
    for i in range(n):
        c, r = i % cols, i // cols
        cx, cy = xs[c], ys[r]
        parts.append(
            f'<rect x="{fnum(cx - pad / 2)}" y="{fnum(cy - pad / 2)}" '
            f'width="{fnum(pad)}" height="{fnum(pad)}" '
            'fill="#F7BD13" stroke="#000000"/>'
        )
    return _svg((0, 0, size, size), "<g id=\"icon\">\n" + "\n".join(parts) + "\n</g>")


# --------------------------------------------------------------------------- #
# .fzp builder
# --------------------------------------------------------------------------- #
def build_fzp(name, pins, pad_map, extra_meta):
    conns = []
    for p in pins:
        i = p["num"] - 1
        desc = p["name"]
        conns.append(
            f'    <connector id="connector{i}" type="male" name="{xmlescape(p["name"])}">\n'
            f'      <description>{xmlescape(desc)}</description>\n'
            '      <views>\n'
            '        <breadboardView>\n'
            f'          <p svgId="connector{i}pin" terminalId="connector{i}terminal" layer="breadboard"/>\n'
            '        </breadboardView>\n'
            '        <schematicView>\n'
            f'          <p svgId="connector{i}pin" terminalId="connector{i}terminal" layer="schematic"/>\n'
            '        </schematicView>\n'
            '        <pcbView>\n'
            f'          <p svgId="connector{i}pad" layer="copper0"/>\n'
            '        </pcbView>\n'
            '      </views>\n'
            '    </connector>'
        )

    mfr = extra_meta.get("Manufacturer", "")
    supplier = extra_meta.get("Supplier", "")
    supplier_part = extra_meta.get("Supplier Part", "")
    package = extra_meta.get("package", "")

    pin_desc = ", ".join(f"{p['num']}:{p['name']}" for p in pins)
    desc = f"Addressable RGB LED ({name}), 6 pins [{pin_desc}]."
    if mfr:
        desc += f" Manufacturer: {mfr}."
    if supplier and supplier_part:
        desc += f" {supplier} part {supplier_part}."
    if package:
        desc += f" Package: {package}."

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<module fritzingVersion="0.9.4" moduleId="{xmlescape(name)}">\n'
        '  <version>4</version>\n'
        '  <author>easyeda_to_fritzing.py</author>\n'
        f'  <title>{xmlescape(name)}</title>\n'
        f'  <label>{xmlescape(name)}</label>\n'
        '  <date>2024-01-01</date>\n'
        f'  <description>{xmlescape(desc)}</description>\n'
        f'  <url>{xmlescape(extra_meta.get("link", ""))}</url>\n'
        '  <properties>\n'
        '    <property name="family">led</property>\n'
        '    <property name="variant">smd</property>\n'
        '  </properties>\n'
        '  <views>\n'
        '    <breadboardView>\n'
        f'      <layers image="svg.{name}.breadboard_breadboard.svg">\n'
        '        <layer layerId="breadboard"/>\n'
        '      </layers>\n'
        '    </breadboardView>\n'
        '    <schematicView>\n'
        f'      <layers image="svg.{name}.schematic_schematic.svg">\n'
        '        <layer layerId="schematic"/>\n'
        '      </layers>\n'
        '    </schematicView>\n'
        '    <pcbView>\n'
        f'      <layers image="svg.{name}.pcb_pcb.svg">\n'
        '        <layer layerId="copper0"/>\n'
        '        <layer layerId="silkscreen"/>\n'
        '      </layers>\n'
        '    </pcbView>\n'
        '    <iconView>\n'
        f'      <layers image="svg.{name}.icon_icon.svg">\n'
        '        <layer layerId="icon"/>\n'
        '      </layers>\n'
        '    </iconView>\n'
        '  </views>\n'
        '  <connectors>\n'
        + "\n".join(conns)
        + "\n  </connectors>\n"
        '  <tags>\n'
        '    <tag>led</tag>\n'
        '    <tag>rgb</tag>\n'
        '    <tag>addressable</tag>\n'
        '  </tags>\n'
        '</module>\n'
    )


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Convert EasyEDA symbol+footprint SVGs to a Fritzing part.")
    ap.add_argument("symbol", help="EasyEDA symbol.svg")
    ap.add_argument("footprint", help="EasyEDA footprint.svg")
    ap.add_argument("--name", default=None, help="Part name (default: from symbol metadata)")
    ap.add_argument("--out", default=None, help="Output directory (default: next to symbol.svg, fritzing/<name>)")
    ap.add_argument(
        "--keep-exploded",
        action="store_true",
        help="Keep the loose .fzp + view SVGs after zipping (default: clean them up)",
    )
    args = ap.parse_args()

    name, pins, body = parse_symbol(args.symbol)
    if args.name:
        name = args.name
    name = re.sub(r"[^\w.\-]+", "-", name.strip())

    pads, silk = parse_footprint(args.footprint)

    if not pins:
        sys.exit("no pins found in symbol")
    if not pads:
        sys.exit("no pads found in footprint")

    # sanity check: pads must cover every pin number
    pad_nums = {p["num"] for p in pads}
    pin_nums = {p["num"] for p in pins}
    if pin_nums - pad_nums:
        print(f"warning: symbol pins without pads: {sorted(pin_nums - pad_nums)}")

    # default: write next to the source symbol.svg, so a part's Fritzing files
    # live beside that part (e.g. docs/<part>/fritzing/<name>/)
    outdir = args.out or os.path.join(
        os.path.dirname(os.path.abspath(args.symbol)), "fritzing", name
    )
    os.makedirs(outdir, exist_ok=True)

    # pull manufacturer/supplier/package metadata from both SVGs for the .fzp
    meta = {}
    for src in (args.symbol, args.footprint):
        tree = ET.parse(src)
        for g in tree.getroot().iter():
            if local(g.tag) == "g" and "c_para" in g.attrib:
                meta.update(parse_c_para(g.attrib["c_para"]))

    files = {
        f"part.{name}.fzp": build_fzp(name, pins, pads, meta),
        f"svg.{name}.schematic_schematic.svg": build_schematic(pins, body),
        f"svg.{name}.pcb_pcb.svg": build_pcb(pads, silk),
        f"svg.{name}.breadboard_breadboard.svg": build_breadboard(pins),
        f"svg.{name}.icon_icon.svg": build_icon(name, pads),
    }

    for fname, content in files.items():
        path = os.path.join(outdir, fname)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    # package as .fzpz
    zpath = os.path.join(os.path.dirname(outdir), name + ".fzpz")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files:
            zf.write(os.path.join(outdir, fname), arcname=fname)
    print("wrote", zpath)

    if args.keep_exploded:
        print("kept exploded files in", outdir)
    else:
        # remove only the files we generated, then the folder if now empty
        for fname in files:
            p = os.path.join(outdir, fname)
            if os.path.isfile(p):
                os.remove(p)
        try:
            os.rmdir(outdir)
        except OSError:
            pass  # directory had other content; leave it in place
        print("cleaned up exploded files (use --keep-exploded to keep them)")


if __name__ == "__main__":
    main()
