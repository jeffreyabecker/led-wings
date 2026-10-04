#!/usr/bin/env python3
"""Tile a sheets SVG onto physical pages and emit an Inkscape multipage SVG.

Python port of the former ``scripts/tile-sheets.ts``. The Node/npm toolchain it
needed is gone, so this version is standard-library only: XML parsing uses
:mod:`xml.etree.ElementTree` instead of jsdom, and there is nothing to install.

usage: python tile_sheets.py <sheets.svg> [trimWxH] [safeWxH] [overlap] [gap]
                             [--out <path>] [--whatif]
  trimWxH   e.g. "215.9x279.4" or "8.5x11in"   (default 215.9x279.4, portrait)
  safeWxH   e.g. "205.9x269.4" or "8.1x10.6in" (default 205.9x269.4, portrait)
  overlap   e.g. "12" or "0.5in"               (default 12)
  gap       e.g. "10" or "0.4in"               (default 10)
  --out     where to write (default: <input>-multipage.svg beside the input)
  --whatif  parse, tile and build the document, then report what it would
            generate and write nothing (the output file is left untouched)
  Each sheet goes on whichever page orientation -- portrait or landscape -- needs
  the fewest pages; ties prefer unrotated content, then portrait pages. A sheet
  that fits the page gets one centered page even if it overruns the safe margin;
  that overrun is not clipped (only multi-page tiles are clipped).
  Units default to mm; "in" is converted to mm.

Every ``<g>`` whose ``class`` contains "sheet" -- and that carries a direct
``<rect>`` child giving its bounds, plus an ``id`` for ``<use>`` to reference --
becomes one or more physical pages, referenced by ``<use>`` so the output never
duplicates the artwork. Pages are laid out side by side in a single Inkscape
multipage document (portrait and landscape pages may be mixed), with crop ticks
and overlap marks.
"""

import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote

MM_PER_IN = 25.4
CROP_INSET = 5.0
INKSCAPE_VERSION = '1.4 (86a8ad7, 2024-10-11)'

# Physical-sheet CSS appended to the carried-over stylesheet on every page.
CSS2 = (
    '\n.crop { stroke: #999999; stroke-width: 0.25; }\n'
    '.overlap { stroke: #999999; stroke-width: 0.15; stroke-dasharray: 2 2; fill: none; }\n'
    '.note { font-family: sans-serif; fill: #555555; font-size: 4; text-anchor: middle; }\n'
)

NAMESPACES = '\n   '.join([
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
    'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
    'xmlns="http://www.w3.org/2000/svg"',
    'xmlns:svg="http://www.w3.org/2000/svg"',
])

USAGE = (
    'usage: python tile_sheets.py <sheets.svg> [trimWxH] [safeWxH] [overlap] [gap]'
    ' [--out <path>] [--whatif]'
)


@dataclass(frozen=True)
class Size:
    width: float
    height: float


@dataclass(frozen=True)
class Paper:
    """A physical page: trim size, printable safe area, and tile overlap (mm)."""

    trim: Size
    safe_area: Size
    overlap: float | tuple[float, float]


@dataclass(frozen=True)
class SheetDef:
    """A sheet found in the input: its id and logical size in source units."""

    id: str
    width: float
    height: float


@dataclass(frozen=True)
class TiledPage:
    body: str
    transform: str
    tile_index: int
    cols: int
    rows: int


@dataclass(frozen=True)
class TileResult:
    pages: list[TiledPage]
    cols: int
    rows: int
    offset: tuple[float, float] | None


@dataclass(frozen=True)
class EnginePage:
    """One physical page of the output document."""

    body: str
    sheet_id: str
    sheet_title: str
    tile_index: int
    cols: int
    rows: int
    transform: str
    paper: Paper


@dataclass(frozen=True)
class Layout:
    """The page orientation and content rotation chosen for one sheet."""

    paper: Paper
    page: str  # 'portrait' or 'landscape'
    rotated: bool  # content turned 90 deg on the page
    result: TileResult


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def fmt(x: float) -> str:
    """Format a number: up to 6 decimals, trailing zeros/dot stripped."""
    s = f'{x:.6f}'
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def esc(s: str) -> str:
    """XML-escape text interpolated into an attribute or text node."""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


_SLUG_RE = re.compile(r'[^A-Za-z0-9_-]+')


def slug(s: str) -> str:
    """Slugify a title for an SVG id: keep ``[A-Za-z0-9_-]``, collapse other runs
    to ``-``, trim leading/trailing dashes. Returns '' when nothing survives."""
    return _SLUG_RE.sub('-', s.strip()).strip('-')


def js_number(text: str | None) -> float:
    """JavaScript ``Number()`` coercion, as applied to XML attribute values.

    A missing attribute (``None``) and ''/whitespace both coerce to ``0``, which
    is what the original did before checking ``Number.isFinite``. Anything
    unparseable (e.g. ``"100mm"``) is ``nan``. Hex literals differ from JS but do
    not occur in these SVGs.
    """
    if text is None:
        return 0.0
    t = text.strip()
    if not t:
        return 0.0
    try:
        return float(t)
    except ValueError:
        return float('nan')


def local_name(tag: object) -> str:
    """Local name of an ElementTree tag (strips the ``{namespace}`` prefix)."""
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''


def round6(x: float) -> float:
    """Round to 6 decimal places so inch->mm conversions yield clean mm values."""
    # math.floor(x + 0.5) is exactly JavaScript's Math.round (half up, toward +inf).
    return math.floor(x * 1e6 + 0.5) / 1e6


def parse_svg(markup: bytes) -> ET.Element:
    """Parse SVG markup into an ElementTree root element."""
    try:
        return ET.fromstring(markup)
    except ET.ParseError as exc:
        raise ValueError('source SVG failed to parse') from exc


# ---------------------------------------------------------------------------
# Tiler
# ---------------------------------------------------------------------------


def overlap_pair(overlap: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(overlap, (int, float)):
        return (float(overlap), float(overlap))
    return (float(overlap[0]), float(overlap[1]))


def corner_ticks(margin_x: float, margin_y: float, safe_w: float, safe_h: float) -> str:
    """Crop ticks at the four corners of the safe area, pointing inward."""
    length = 5.0
    lo_x = margin_x + CROP_INSET
    hi_x = margin_x + safe_w - CROP_INSET
    lo_y = margin_y + CROP_INSET
    hi_y = margin_y + safe_h - CROP_INSET
    segs: list[str] = []
    for cx in (lo_x, hi_x):
        for cy in (lo_y, hi_y):
            sx = 1.0 if cx == lo_x else -1.0
            sy = 1.0 if cy == lo_y else -1.0
            segs.append(
                f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}"'
                f' x2="{fmt(cx + sx * length)}" y2="{fmt(cy)}"/>'
            )
            segs.append(
                f'<line class="crop" x1="{fmt(cx)}" y1="{fmt(cy)}"'
                f' x2="{fmt(cx)}" y2="{fmt(cy + sy * length)}"/>'
            )
    return '<g>' + ''.join(segs) + '</g>'


def overlap_marks(
    c: int,
    r: int,
    cols: int,
    rows: int,
    margin_x: float,
    margin_y: float,
    safe_w: float,
    safe_h: float,
    overlap_x: float,
    overlap_y: float,
) -> str:
    """Dashed marks showing where the neighbouring tile overlaps this page."""
    segs: list[str] = []
    if c < cols - 1:
        x = margin_x + safe_w - overlap_x
        segs.append(
            f'<line class="overlap" x1="{fmt(x)}" y1="{fmt(margin_y)}"'
            f' x2="{fmt(x)}" y2="{fmt(margin_y + safe_h)}"/>'
        )
    if c > 0:
        x = margin_x + overlap_x
        segs.append(
            f'<line class="overlap" x1="{fmt(x)}" y1="{fmt(margin_y)}"'
            f' x2="{fmt(x)}" y2="{fmt(margin_y + safe_h)}"/>'
        )
    if r < rows - 1:
        y = margin_y + safe_h - overlap_y
        segs.append(
            f'<line class="overlap" x1="{fmt(margin_x)}" y1="{fmt(y)}"'
            f' x2="{fmt(margin_x + safe_w)}" y2="{fmt(y)}"/>'
        )
    if r > 0:
        y = margin_y + overlap_y
        segs.append(
            f'<line class="overlap" x1="{fmt(margin_x)}" y1="{fmt(y)}"'
            f' x2="{fmt(margin_x + safe_w)}" y2="{fmt(y)}"/>'
        )
    return '<g>' + ''.join(segs) + '</g>' if segs else ''


def tile(
    title: str,
    width: float,
    height: float,
    body: str,
    paper: Paper,
    id_prefix: str = 'clip',
    fit: Size | None = None,
) -> TileResult:
    """Map a sheet's logical area onto physical pages: one centered page when it
    fits, else a cols x rows grid with overlap marks.

    ``fit`` bounds the single-page case and defaults to the safe area. Passing the
    page trim instead lets a sheet that overruns the safe margin still land on one
    page -- centered, so the overrun splits evenly into both margins and is *not*
    clipped away. Tiling beyond one page still strides over the safe area.
    """
    trim_w = paper.trim.width
    trim_h = paper.trim.height
    safe_w = paper.safe_area.width
    safe_h = paper.safe_area.height
    overlap_x, overlap_y = overlap_pair(paper.overlap)
    margin_x = (trim_w - safe_w) / 2
    margin_y = (trim_h - safe_h) / 2
    stride_x = safe_w - overlap_x
    stride_y = safe_h - overlap_y
    if stride_x <= 0 or stride_y <= 0:
        raise ValueError('overlap must be smaller than the safe area')

    fit_w = safe_w if fit is None else fit.width
    fit_h = safe_h if fit is None else fit.height
    cols = 1 if width <= fit_w else math.ceil((width - safe_w) / stride_x) + 1
    rows = 1 if height <= fit_h else math.ceil((height - safe_h) / stride_y) + 1

    pages: list[TiledPage] = []
    if cols == 1 and rows == 1:
        ox = margin_x + (safe_w - width) / 2
        oy = margin_y + (safe_h - height) / 2
        tr = f'translate({fmt(ox)} {fmt(oy)})'
        pages.append(TiledPage(
            body=f'<g transform="{tr}">{body}</g>',
            transform=tr,
            tile_index=1,
            cols=1,
            rows=1,
        ))
        return TileResult(pages=pages, cols=cols, rows=rows, offset=(ox, oy))

    for r in range(rows):
        for c in range(cols):
            tx = margin_x - c * stride_x
            ty = margin_y - r * stride_y
            tr = f'translate({fmt(tx)} {fmt(ty)})'
            idx = r * cols + c + 1
            clip_id = f'{id_prefix}-{idx}'
            clip = (
                f'<defs><clipPath id="{clip_id}"><rect x="{fmt(margin_x)}"'
                f' y="{fmt(margin_y)}" width="{fmt(safe_w)}" height="{fmt(safe_h)}"/></clipPath></defs>'
            )
            parts = [
                clip,
                f'<g clip-path="url(#{clip_id})">',
                f'<g transform="{tr}">{body}</g>',
                '</g>',
                corner_ticks(margin_x, margin_y, safe_w, safe_h),
                overlap_marks(c, r, cols, rows, margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y),
                f'<text class="note" x="{fmt(trim_w / 2)}" y="{fmt(trim_h - 2.5)}">'
                f'{esc(title)} \u00b7 tile {idx}/{cols * rows} \u00b7 {cols}x{rows}</text>',
            ]
            pages.append(TiledPage(
                body='\n'.join(parts),
                transform=tr,
                tile_index=idx,
                cols=cols,
                rows=rows,
            ))
    return TileResult(pages=pages, cols=cols, rows=rows, offset=None)


def orientation_papers(
    trim: Size,
    safe_area: Size,
    overlap: float | tuple[float, float],
) -> tuple[Paper, Paper]:
    """Portrait and landscape papers for one physical page.

    Landscape is the portrait page turned 90 deg, so trim and safe area both swap
    (a vector overlap swaps with them; a scalar overlap is orientation-free).
    """
    landscape_overlap: float | tuple[float, float] = overlap
    if not isinstance(overlap, (int, float)):
        landscape_overlap = (overlap[1], overlap[0])
    return (
        Paper(trim=trim, safe_area=safe_area, overlap=overlap),
        Paper(
            trim=Size(width=trim.height, height=trim.width),
            safe_area=Size(width=safe_area.height, height=safe_area.width),
            overlap=landscape_overlap,
        ),
    )


def choose_layout(
    title: str,
    sheet: SheetDef,
    use_ref: str,
    portrait: Paper,
    landscape: Paper,
) -> Layout:
    """Pick the page orientation and content rotation needing the fewest pages.

    Candidates are tried in preference order -- content left unrotated before
    content turned 90 deg, and portrait before landscape at the same rotation --
    and only a *strict* page-count improvement wins. So a sheet keeps upright
    content whenever that costs no extra page, and landscape appears only where it
    saves a page or avoids rotating the content.

    Each candidate may fit its page trim (not just the safe area) as a single
    centered page, which is what keeps a sheet like 269x210 mm off a second page.
    """
    candidates = (
        ('portrait', portrait, False),
        ('landscape', landscape, False),
        ('portrait', portrait, True),
        ('landscape', landscape, True),
    )
    best: Layout | None = None
    for page_name, paper, rotated in candidates:
        if rotated:
            body = f'<g transform="translate({fmt(sheet.height)} 0) rotate(90)">{use_ref}</g>'
            result = tile(title, sheet.height, sheet.width, body, paper, 'clip', fit=paper.trim)
        else:
            result = tile(title, sheet.width, sheet.height, use_ref, paper, 'clip', fit=paper.trim)
        if best is None or len(result.pages) < len(best.result.pages):
            best = Layout(paper=paper, page=page_name, rotated=rotated, result=result)
    assert best is not None  # candidates is never empty
    return best


# ---------------------------------------------------------------------------
# Multipage emitter
# ---------------------------------------------------------------------------


def default_label(page: EnginePage) -> str:
    if page.cols == 1 and page.rows == 1:
        return page.sheet_title
    return f'{page.sheet_title} \u00b7 tile {page.tile_index}/{page.cols * page.rows}'


def page_id(page: EnginePage) -> str:
    name = slug(page.sheet_title) or page.sheet_id
    if page.cols == 1 and page.rows == 1:
        return f'page-{name}'
    return f'page-{name}-tile-{page.tile_index}'


def emit_multipage_svg(
    pages: list[EnginePage],
    style_css: str,
    *,
    gap: float = 10.0,
    label: Callable[[EnginePage, int], str] | None = None,
    doc_name: str | None = None,
) -> str:
    """Emit tiled pages as a single Inkscape multipage SVG document (pages laid
    out side by side; one ``<inkscape:page>`` per physical page).

    Each page carries its own trim size, so portrait and landscape pages can share
    one document: pages are placed left to right by accumulating their widths, and
    the document is as tall as the tallest page.
    """
    total_h = max(page.paper.trim.height for page in pages)

    page_defs: list[str] = []
    page_groups: list[str] = []
    x = 0.0

    for i, page in enumerate(pages):
        trim = page.paper.trim
        text = label(page, i) if label else default_label(page)
        page_defs.append(
            '    <inkscape:page\n'
            f'       x="{fmt(x)}"\n'
            '       y="0"\n'
            f'       width="{fmt(trim.width)}"\n'
            f'       height="{fmt(trim.height)}"\n'
            f'       id="page{i + 1}"\n'
            '       margin="5"\n'
            '       bleed="0"\n'
            f'       inkscape:label="{esc(text)}" />'
        )
        page_groups.append(
            f'  <g id="{esc(page_id(page))}" transform="translate({fmt(x)} 0)">\n'
            f'    <rect x="0" y="0" width="{fmt(trim.width)}" height="{fmt(trim.height)}" fill="#ffffff"/>\n'
            f'{page.body}\n'
            '  </g>'
        )
        x += trim.width + gap

    total_w = x - gap  # n widths plus n-1 gaps

    if doc_name is None:
        doc_name = 'sheets-multipage.svg'

    indented_groups = '\n'.join(
        ('  ' + line) if line else line for line in '\n'.join(page_groups).split('\n')
    )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<!-- Created with Inkscape (http://www.inkscape.org/) -->\n\n'
        '<svg\n'
        f'   width="{fmt(total_w)}mm"\n'
        f'   height="{fmt(total_h)}mm"\n'
        f'   viewBox="0 0 {fmt(total_w)} {fmt(total_h)}"\n'
        '   version="1.1"\n'
        '   id="svg1"\n'
        f'   inkscape:version="{INKSCAPE_VERSION}"\n'
        f'   sodipodi:docname="{esc(doc_name)}"\n'
        f'   {NAMESPACES}>\n'
        '  <sodipodi:namedview\n'
        '     id="namedview1"\n'
        '     pagecolor="#ffffff"\n'
        '     bordercolor="#666666"\n'
        '     borderopacity="1.0"\n'
        '     inkscape:showpageshadow="2"\n'
        '     inkscape:pageopacity="0.0"\n'
        '     inkscape:pagecheckerboard="false"\n'
        '     inkscape:deskcolor="#d1d1d1"\n'
        '     inkscape:document-units="mm"\n'
        '     showborder="true">\n'
        + '\n'.join(page_defs) + '\n'
        '  </sodipodi:namedview>\n'
        '  <defs\n'
        '     id="defs1" />\n'
        f'  <style type="text/css">{style_css}{CSS2}</style>\n'
        '  <g id="pages">\n'
        + indented_groups + '\n'
        '  </g>\n'
        '</svg>\n'
    )


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------


def has_sheet_class(el: ET.Element) -> bool:
    """True when the element's ``class`` contains "sheet".

    Substring match on the whole class attribute (case-sensitive, as CSS class
    names are): ``class="sheet"``, ``class="sheet label"`` and
    ``class="sheet-cover"`` all match. Note that this also matches
    ``class="worksheet"`` or ``class="sheets"`` -- change to an exact token test
    (``'sheet' in el.get('class', '').split()``) if that ever bites.
    """
    return 'sheet' in (el.get('class') or '')


def find_sheets(root: ET.Element) -> list[SheetDef]:
    """Find ``<g>`` groups whose ``class`` contains "sheet" and that carry a
    background ``<rect>`` (the sheet bounds) as a *direct* child -- wrapper groups
    nest their rect one level deeper and are skipped, as are class-marked groups
    with no ``id`` (the emitted ``<use>`` needs one; a warning is printed).

    Sheets are ordered by their ``data-sort-order`` attribute (ascending); sheets
    without one come last in document order."""
    raw: list[dict[str, object]] = []
    for el in root.iter():
        if local_name(el.tag) != 'g':
            continue
        if not has_sheet_class(el):
            continue
        el_id = el.get('id')
        if not el_id:
            print(
                f'warning: skipping <g class="{el.get("class")}">: no id, so the'
                ' page cannot <use> it',
                file=sys.stderr,
            )
            continue
        rect = next((c for c in el if local_name(c.tag) == 'rect'), None)
        if rect is None:
            continue
        w = js_number(rect.get('width'))
        h = js_number(rect.get('height'))
        if not (math.isfinite(w) and math.isfinite(h)):
            continue
        order_attr = el.get('data-sort-order')
        parsed = float('inf') if order_attr is None else js_number(order_attr)
        raw.append({
            'id': el_id,
            'width': w,
            'height': h,
            'order': parsed if math.isfinite(parsed) else float('inf'),
            'index': len(raw),
        })
    raw.sort(key=lambda r: (r['order'], r['index']))
    return [
        SheetDef(id=str(r['id']), width=float(r['width']), height=float(r['height']))
        for r in raw
    ]


def first_style_text(root: ET.Element) -> str:
    """Text content of the first ``<style>`` element ('' when there is none)."""
    for el in root.iter():
        if local_name(el.tag) == 'style':
            return ''.join(el.itertext())
    return ''


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

_DIST_RE = re.compile(r'^([-+]?(?:\d+\.?\d*|\.\d+))\s*(mm|in)?$', re.IGNORECASE)
_UNIT_RE = re.compile(r'(mm|in)$', re.IGNORECASE)


def dist(text: str) -> float:
    """Parse a distance like "12", "12mm", or "0.5in" -> millimetres."""
    m = _DIST_RE.match(text.strip())
    if not m:
        raise ValueError(f'bad distance "{text}" (expected a number with optional mm/in)')
    value = float(m.group(1))
    unit = (m.group(2) or 'mm').lower()
    return round6(value * MM_PER_IN if unit == 'in' else value)


def size(text: str) -> Size:
    """Parse "WxH" with an optional trailing unit ("mm" default; "in" -> mm)."""
    t = text.strip()
    unit_match = _UNIT_RE.search(t)
    unit = (unit_match.group(1) if unit_match else 'mm').lower()
    dims_text = (t[: -len(unit_match.group(1))] if unit_match else t).strip()
    parts = re.split(r'[x\u00d7]', dims_text, flags=re.IGNORECASE)
    if len(parts) != 2:
        raise ValueError(f'bad size "{text}" (expected WxH with optional mm/in)')
    w = js_number(parts[0])
    h = js_number(parts[1])
    if not (math.isfinite(w) and math.isfinite(h)):
        raise ValueError(f'bad size "{text}" (expected WxH with optional mm/in)')
    factor = MM_PER_IN if unit == 'in' else 1.0
    return Size(width=round6(w * factor), height=round6(h * factor))


def parse_args(argv: list[str]) -> tuple[list[str], dict[str, str | None]]:
    """Separate positional arguments from ``--flags`` (and their values)."""
    positional: list[str] = []
    flags: dict[str, str | None] = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            name = a[2:]
            val = argv[i + 1] if i + 1 < len(argv) else None
            if val is not None and not val.startswith('--'):
                flags[name] = val
                i += 1
            else:
                flags[name] = None
        else:
            positional.append(a)
        i += 1
    return positional, flags


# Regexes for the shared-defs rewrite: the first tiled page's per-tile clip path
# and its inline crop ticks are hoisted into document-level defs.
_CLIP_DEFS_RE = re.compile(r'<defs><clipPath id="clip-[^"]+"><rect [^>]*/></clipPath></defs>\n?')
_CLIP_REF_RE = re.compile(r'clip-path="url\(#clip-[^)]*\)"')
_CROP_TICKS_RE = re.compile(r'<g>((?:<line class="crop" [^>]*/>)+)</g>')

# JS encodeURI's unreserved set: whatever a file basename can legitimately hold.
_URI_SAFE = ";/?:@&=+$,-_.!~*'()#"


@dataclass(frozen=True)
class PlannedSheet:
    """What the tiler decided for one sheet (reported by ``--whatif``)."""

    sheet_id: str
    width: float
    height: float
    page: str  # 'portrait' or 'landscape'
    rotated: bool  # content turned 90 deg on the page
    trim: Size  # the page size this sheet landed on
    cols: int
    rows: int
    pages: int


def format_whatif(
    planned: list[PlannedSheet],
    *,
    in_path: str,
    out_path: str,
    trim: Size,
    safe_area: Size,
    overlap: float,
    gap: float,
    svg_bytes: int,
    has_clip: bool,
    has_crop_ticks: bool,
    overwrite_bytes: int | None,
) -> str:
    """Report what a run would generate, without generating it (``--whatif``).

    Deliberately ASCII-only: this is read in a terminal of any code page.
    """
    pages = sum(s.pages for s in planned)
    tiled = sum(1 for s in planned if s.pages > 1)
    doc_w = sum(s.pages * s.trim.width for s in planned) + max(pages - 1, 0) * gap
    doc_h = max(s.trim.height for s in planned)
    margin_x = (trim.width - safe_area.width) / 2
    margin_y = (trim.height - safe_area.height) / 2

    if overwrite_bytes is None:
        out_note = f'would write {svg_bytes:,} bytes'
    else:
        out_note = (
            f'would write {svg_bytes:,} bytes, overwriting the existing '
            f'{overwrite_bytes:,}-byte file'
        )

    features = ['by-reference <use>']
    if has_clip:
        features.append('shared clip path')
    if has_crop_ticks:
        features.append('shared crop ticks')

    lines = [
        'whatif: nothing written, no output generated',
        '',
        f'input       {in_path}',
        f'output      {out_path}',
        f'            {out_note}',
        f'paper       trim {fmt(trim.width)} x {fmt(trim.height)} mm '
        f'(landscape {fmt(trim.height)} x {fmt(trim.width)} mm), '
        f'safe {fmt(safe_area.width)} x {fmt(safe_area.height)} mm, '
        f'margins {fmt(margin_x)} x {fmt(margin_y)} mm',
        f'            overlap {fmt(overlap)} mm, gap {fmt(gap)} mm; page orientation chosen '
        f'per sheet, fitted to the page',
        f'document    {pages} pages across {len(planned)} sheets '
        f'({tiled} tiled over multiple pages, {len(planned) - tiled} fitting one page), '
        f'{fmt(doc_w)} x {fmt(doc_h)} mm',
        f'content     {", ".join(features)}',
        '',
        f'  {"sheet":<38} {"size (mm)":>18}  {"page":<9} {"content":<8} {"grid":>5} {"pages":>5}',
        f'  {"-" * 38} {"-" * 18}  {"-" * 9} {"-" * 8} {"-" * 5} {"-" * 5}',
    ]
    for sheet in planned:
        size_text = f'{fmt(sheet.width)}x{fmt(sheet.height)}'
        grid_text = f'{sheet.cols}x{sheet.rows}'
        content_text = 'rotated' if sheet.rotated else 'as-is'
        lines.append(
            f'  {sheet.sheet_id:<38} {size_text:>18}  {sheet.page:<9} {content_text:<8} '
            f'{grid_text:>5} {sheet.pages:>5}'
        )
    return '\n'.join(lines)


def run(positional: list[str], flags: dict[str, str | None]) -> int:
    input_arg = positional[0]
    in_path = os.path.abspath(input_arg)

    trim = size(positional[1] if len(positional) > 1 else '215.9x279.4')
    safe_area = size(positional[2] if len(positional) > 2 else '205.9x269.4')
    overlap = dist(positional[3] if len(positional) > 3 else '12')
    gap = dist(positional[4] if len(positional) > 4 else '10')

    out_arg = flags.get('out')
    if not out_arg:
        out_arg = re.sub(r'\.svg$', '', input_arg, flags=re.IGNORECASE) + '-multipage.svg'
    out_path = os.path.abspath(out_arg)

    portrait, landscape = orientation_papers(trim, safe_area, overlap)

    with open(in_path, 'rb') as fh:
        doc = parse_svg(fh.read())

    # Sheets are referenced relative to the output file (assumed co-located).
    href = quote(os.path.basename(in_path), safe=_URI_SAFE)

    sheets = find_sheets(doc)
    if not sheets:
        print(
            f'no groups with a "sheet" class (and a direct <rect> child, and an id)'
            f' found in {in_path}',
            file=sys.stderr,
        )
        return 1

    # Carry the sheets' own stylesheet over so their classes resolve in the
    # output (CSS does not cascade across an external <use> reference).
    style_css = first_style_text(doc)

    pages: list[EnginePage] = []
    planned: list[PlannedSheet] = []
    n = 0
    # Crop ticks and the safe-area clip rect depend on the page geometry, so there
    # is one hoisted defs entry per distinct geometry (portrait and landscape).
    shared_clips: dict[tuple[str, ...], str] = {}
    shared_ticks: dict[tuple[str, ...], tuple[str, str]] = {}

    for sheet in sheets:
        title = sheet.id.removeprefix('sheet-')
        use_ref = f'<use href="{esc(f"{href}#{sheet.id}")}"/>'
        layout = choose_layout(title, sheet, use_ref, portrait, landscape)
        planned.append(PlannedSheet(
            sheet_id=sheet.id,
            width=sheet.width,
            height=sheet.height,
            page=layout.page,
            rotated=layout.rotated,
            trim=layout.paper.trim,
            cols=layout.result.cols,
            rows=layout.result.rows,
            pages=len(layout.result.pages),
        ))

        for page in layout.result.pages:
            n += 1
            page_body = page.body
            key = (
                fmt(layout.paper.safe_area.width),
                fmt(layout.paper.safe_area.height),
                fmt((layout.paper.trim.width - layout.paper.safe_area.width) / 2),
                fmt((layout.paper.trim.height - layout.paper.safe_area.height) / 2),
            )
            if '<clipPath' in page_body:
                clip_id = shared_clips.get(key)
                if clip_id is None:
                    # The first geometry keeps the historical plain 'clip' name; any
                    # further ones must NOT look like 'clip-<n>', which is the shape
                    # tile() gives its per-tile ids.
                    clip_id = 'clip' if not shared_clips else f'clip-shared-{len(shared_clips) + 1}'
                    shared_clips[key] = clip_id
                page_body = _CLIP_DEFS_RE.sub('', page_body, count=1)
                page_body = _CLIP_REF_RE.sub(f'clip-path="url(#{clip_id})"', page_body, count=1)
            m = _CROP_TICKS_RE.search(page_body)
            if m:
                tick = shared_ticks.get(key)
                if tick is None:
                    tick_id = ('crop-ticks' if not shared_ticks
                               else f'crop-ticks-shared-{len(shared_ticks) + 1}')
                    tick = (tick_id, m.group(1))
                    shared_ticks[key] = tick
                page_body = page_body[: m.start()] + f'<use href="#{tick[0]}"/>' + page_body[m.end():]
            pages.append(EnginePage(
                body=page_body,
                sheet_id=sheet.id,
                sheet_title=title,
                tile_index=page.tile_index,
                cols=page.cols,
                rows=page.rows,
                transform=page.transform,
                paper=layout.paper,
            ))

    # --- emit ---
    defs: list[str] = []
    for key, clip_id in shared_clips.items():
        safe_w, safe_h, margin_x, margin_y = key
        defs.append(
            f'      <clipPath id="{clip_id}"><rect x="{margin_x}" y="{margin_y}"'
            f' width="{safe_w}" height="{safe_h}"/></clipPath>'
        )
    for key, (tick_id, inner) in shared_ticks.items():
        defs.append(f'      <g id="{tick_id}">{inner}</g>')

    svg = emit_multipage_svg(pages, style_css, gap=gap)
    if defs:
        svg = svg.replace(
            '<defs\n     id="defs1" />',
            '<defs\n     id="defs1">\n' + '\n'.join(defs) + '\n    </defs>',
        )

    if 'whatif' in flags:
        print(format_whatif(
            planned,
            in_path=in_path,
            out_path=out_path,
            trim=trim,
            safe_area=safe_area,
            overlap=overlap,
            gap=gap,
            svg_bytes=len(svg.encode('utf-8')),
            has_clip=bool(shared_clips),
            has_crop_ticks=bool(shared_ticks),
            overwrite_bytes=os.path.getsize(out_path) if os.path.exists(out_path) else None,
        ))
        return 0

    # newline='' keeps the '\n' the emitter produced on every platform.
    with open(out_path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(svg)

    print(f'wrote {out_path} \u2014 {len(pages)} pages from {len(sheets)} sheets')
    return 0


def main(argv: list[str] | None = None) -> int:
    positional, flags = parse_args(list(sys.argv[1:] if argv is None else argv))
    if not positional:
        print(USAGE, file=sys.stderr)
        return 1
    try:
        return run(positional, flags)
    except (ValueError, OSError) as exc:
        print(f'tile_sheets.py: error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
