#!/usr/bin/env python3
"""Tile a sheets master onto physical pages and emit an Inkscape print document.

Python port of the former ``scripts/tile-sheets.ts``. The Node/npm toolchain it
needed is gone, so this version is standard-library only: XML parsing uses
:mod:`xml.etree.ElementTree` instead of jsdom, and there is nothing to install.

usage: python tile_sheets.py <content>/sheets.svg --paper <name> --out <path>
                             [--margin <mm>] [--safe WxH] [--overlap <dist>]
                             [--gap <dist>] [--whatif]
  --paper   paper name; required. One of: letter, legal, tabloid, a3, a4, a5
            (--list-papers prints the table and exits)
  --margin  unprintable margin per edge, in mm (default 5); the safe area is the
            trim inset by it. --safe WxH overrides that derivation
  --size    WxH instead of --paper, for stock not in the table ("210x297",
            "8.5x11in"); --safe WxH still applies
  --overlap how much neighbouring pages print twice, e.g. "12" or "0.5in"
            (default 12)
  --gap     space between pages inside the emitted document, e.g. "10" or "0.4in"
            (default 10)
  --out     where to write; required. The directory is created if needed
  --whatif  parse, tile and build the document, then report what it would
            generate and write nothing (the output file is left untouched)
  Each sheet goes on whichever page orientation -- portrait or landscape -- needs
  the fewest pages; ties prefer unrotated content, then portrait pages. A sheet
  that fits the page gets one centered page even if it overruns the safe margin;
  that overrun is not clipped (only multi-page tiles are clipped).
  Distances and sizes default to mm; "in" is converted to mm.

The print document is written to ``--out`` and references its master by a path
relative to that output directory (``../../../feathers/sheets.svg#sheet-P1``), so
the master and the print documents no longer have to sit side by side. Because
the reference is relative, a print document stops rendering if it is moved away
from its own tree -- the rendered PDF is the portable artefact.

The paper token, the resolved trim and safe area, the overlap, the gap and the
page count are stamped into the output as a comment beside the Inkscape header,
so a shipped print document records how it was produced.

Every ``<g>`` carrying the class token ``sheet`` -- and that has a direct
``<rect>`` child giving its bounds, plus an ``id`` for ``<use>`` to reference --
becomes one or more physical pages, referenced by ``<use>`` so the output never
duplicates the artwork. That rect is taken as both a size and a position: it may
sit anywhere inside its group, and the group may carry a ``transform``, so the
offset is cancelled before the sheet is placed on a page. Pages are laid out side
by side in a single print document (portrait and landscape pages may be mixed).
The root element is sized to the first page rather than to the whole strip -- see
:func:`emit_multipage_svg` for why Inkscape's PDF export needs that.

Reading the marks
-----------------

A join between two pages is one line of the sheet that both of them print, so both
mark it -- a grey dotted line across the printable width, closed at each end by a
solid 5 mm bar pointing inward along the other axis (a bottom line's bars rise, a
top line's bars hang down). The marks carry no text, so read them by shape:

* the line at the very top of a page's printed content is the one to **align**:
  there is nothing printed above it. Lay it exactly on the neighbour's cut;
* a line with printed content continuing below it is the one to **cut** on, and it
  sits one overlap above the bottom of that content. Everything below it is printed
  again by the tile that continues the sheet.

The two lines are the same line on the sheet (on paper they sit ``stride`` apart,
i.e. safe size minus overlap). A grey dashed line marks the *far* edge of the
duplicated band -- where the neighbour's copy stops -- and is information only:
lining that edge up with the neighbour's cut line instead of with the matching
band edge would shift the seam by one overlap. Because the whole band is printed
twice, a cut may fall anywhere in it, not exactly on the line. Corner ticks are
deliberately not drawn: nothing happens at the safe-area corners, and the outer
margin is the printer's unprintable edge, so marks there are useless or missing.
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

# Cut/align marks: a grey dotted line across the page with a solid 5 mm bar at
# each end, perpendicular to it and pointing inward (a line near the page bottom
# gets bars rising from it, one near the top gets bars hanging from it), so the
# marks stay inside the printable area. Grey and dotted keeps them distinct from
# sheet artwork without competing with it. See "Reading the marks" in the module
# docstring.
MARK_COLOR = '#666666'
MARK_BAR = 5.0
MARK_DOT = '0.1 1.6'

INKSCAPE_VERSION = '1.4 (86a8ad7, 2024-10-11)'

# Page furniture the tiler draws itself, appended to the stylesheet it carries
# over from the sheets master. The join marks exist only in the output -- the
# master has no join -- so their rules have no source document to live in.
# Everything else a page needs (`.overlap`, `.note`) already comes from the
# carried stylesheet, which is why this block is this short. See
# :func:`require_style_rules`.
JOIN_CSS = (
    f'\n.join-line {{ stroke: {MARK_COLOR}; stroke-width: 0.3;'
    f' stroke-dasharray: {MARK_DOT}; stroke-linecap: round; fill: none; }}\n'
    f'.join-bar {{ stroke: {MARK_COLOR}; stroke-width: 0.3; fill: none; }}\n'
)

# The rules a generated page must be able to resolve: the tiler's own marks plus
# the overlap band edge and the page note, which the master's stylesheet supplies.
REQUIRED_PAGE_RULES = (
    ('.join-line', 'the dotted line marking a join'),
    ('.join-bar', 'the bar closing each end of a join line'),
    ('.overlap', 'the dashed far edge of the duplicated band'),
    ('.note', 'the tile caption on a multi-page sheet'),
)

# Paper names -> trim size (mm). Only the trim is tabulated: the safe area is
# derived from --margin, or overridden with --safe for stock whose printable area
# is not symmetric. The name is what --paper takes and what belongs in the
# output filename, so `--paper letter --out .../print-letter.svg` agree.
# Defined after :class:`Size`, which the table values are.

DEFAULT_MARGIN = 5.0
DEFAULT_OVERLAP = '12'
DEFAULT_GAP = '10'

NAMESPACES = '\n   '.join([
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
    'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"',
    'xmlns="http://www.w3.org/2000/svg"',
    'xmlns:svg="http://www.w3.org/2000/svg"',
])


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
    """A sheet found in the input: its id, logical size, and bounds offset.

    ``offset`` is where the bounds ``<rect>`` corner sits inside the referenced
    group's *own* coordinate system -- ``(0, 0)`` for a well-formed sheet. The
    group's ``transform`` counts, because ``<use>`` reproduces it, and so does a
    ``transform`` on the rect itself.
    """

    id: str
    width: float
    height: float
    offset: tuple[float, float]


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


PAPERS: dict[str, Size] = {
    'letter': Size(width=215.9, height=279.4),
    'legal': Size(width=215.9, height=355.6),
    'tabloid': Size(width=279.4, height=431.8),
    'a3': Size(width=297.0, height=420.0),
    'a4': Size(width=210.0, height=297.0),
    'a5': Size(width=148.0, height=210.0),
}

USAGE = (
    'usage: python tile_sheets.py <content>/sheets.svg --paper <name> --out <path>'
    ' [--margin <mm>] [--safe WxH] [--overlap <dist>] [--gap <dist>] [--whatif]\n'
    '       python tile_sheets.py <content>/sheets.svg --size WxH [--safe WxH]'
    ' --out <path> [...]\n'
    '       python tile_sheets.py --list-papers'
)

# Which options take a value, so the parser never has to guess (see parse_args).
VALUE_FLAGS = frozenset({
    'paper', 'out', 'size', 'safe', 'margin', 'overlap', 'gap',
})
BOOLEAN_FLAGS = frozenset({'whatif', 'list-papers'})


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


# --- SVG transforms ---------------------------------------------------------

Matrix = tuple[float, float, float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

_TRANSFORM_RE = re.compile(r'(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)')
_NUMBER_RE = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')


def matrix_multiply(m: Matrix, n: Matrix) -> Matrix:
    """The matrix ``m`` followed by ``n`` (i.e. ``n * m`` in SVG terms)."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (
        a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1,
    )


def parse_transform(text: str | None) -> Matrix:
    """Parse a ``transform`` attribute into a 2x3 matrix (identity when absent).

    Handles the whole transform-list grammar, including ``rotate(a cx cy)``, so a
    sheet whose group carries any transform can still be measured. A function whose
    arguments do not parse is skipped rather than aborting the whole attribute.
    """
    m = IDENTITY
    if not text:
        return m
    for name, args in _TRANSFORM_RE.findall(text):
        vals = [float(v) for v in _NUMBER_RE.findall(args)]
        if name == 'matrix' and len(vals) == 6:
            step: Matrix = (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
        elif name == 'translate' and vals:
            step = (1.0, 0.0, 0.0, 1.0, vals[0], vals[1] if len(vals) > 1 else 0.0)
        elif name == 'scale' and vals:
            sy = vals[1] if len(vals) > 1 else vals[0]
            step = (vals[0], 0.0, 0.0, sy, 0.0, 0.0)
        elif name == 'rotate' and vals:
            angle = math.radians(vals[0])
            cos, sin = math.cos(angle), math.sin(angle)
            step = (cos, sin, -sin, cos, 0.0, 0.0)
            if len(vals) == 3:
                cx, cy = vals[1], vals[2]
                step = matrix_multiply(
                    matrix_multiply((1.0, 0.0, 0.0, 1.0, cx, cy), step),
                    (1.0, 0.0, 0.0, 1.0, -cx, -cy),
                )
        elif name == 'skewX' and vals:
            step = (1.0, 0.0, math.tan(math.radians(vals[0])), 1.0, 0.0, 0.0)
        elif name == 'skewY' and vals:
            step = (1.0, math.tan(math.radians(vals[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            continue
        m = matrix_multiply(m, step)
    return m


def is_translation(m: Matrix) -> bool:
    """True when ``m`` only moves things: no rotation, skew or scale."""
    a, b, c, d = m[:4]
    return (
        abs(a - 1.0) < 1e-9 and abs(b) < 1e-9
        and abs(c) < 1e-9 and abs(d - 1.0) < 1e-9
    )


def transform_point(m: Matrix, x: float, y: float) -> tuple[float, float]:
    """Apply ``m`` to a point, rounding away -0.0 so it formats as ``0``."""
    a, b, c, d, e, f = m
    px = round6(a * x + c * y + e)
    py = round6(b * x + d * y + f)
    return (0.0 if px == 0 else px, 0.0 if py == 0 else py)


def bounds_offset(group: ET.Element, rect: ET.Element) -> tuple[float, float]:
    """Where a sheet's bounds rect corner lands in the group's own coordinates.

    ``<use>`` reproduces the referenced group *including* its ``transform``, so an
    offset here shows up verbatim on the page: the tiler cancels it to put the
    bounds -- and with them the artwork -- where the page geometry expects.
    """
    m = matrix_multiply(
        parse_transform(group.get('transform')),
        parse_transform(rect.get('transform')),
    )
    x = js_number(rect.get('x'))
    y = js_number(rect.get('y'))
    return transform_point(m, x if math.isfinite(x) else 0.0, y if math.isfinite(y) else 0.0)


# ---------------------------------------------------------------------------
# Tiler
# ---------------------------------------------------------------------------


def overlap_pair(overlap: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(overlap, (int, float)):
        return (float(overlap), float(overlap))
    return (float(overlap[0]), float(overlap[1]))


def mark_geometry(paper: Paper) -> tuple[float, float, float, float, float, float]:
    """``(margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y)`` for a page."""
    trim_w = paper.trim.width
    trim_h = paper.trim.height
    safe_w = paper.safe_area.width
    safe_h = paper.safe_area.height
    overlap_x, overlap_y = overlap_pair(paper.overlap)
    return (
        (trim_w - safe_w) / 2, (trim_h - safe_h) / 2,
        safe_w, safe_h, overlap_x, overlap_y,
    )


def join_marks(
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
    """Cut/align marks for the joins this page takes part in.

    A join between two pages is one line of the sheet, printed on both of them.
    Both pages mark that same line, and the mark says which job it is by where it
    sits on the page rather than by any text:

    * the upper page cuts on it -- everything below is printed again by the tile
      that continues the sheet, so the cut may fall anywhere in the overlap band;
    * the lower page lays its line on that cut -- its content starts there, so
      nothing is printed above the mark.

    So the upper page marks ``margin + safe - overlap`` (the first duplicated
    line) and the lower page marks the margin (its own content edge): different
    positions on paper, identical position on the sheet. Each line is drawn dotted
    across the printable width and closed at both ends by a solid ``MARK_BAR`` mm
    bar along the page's other axis, always pointing inward -- the bottom line's
    bars rise, the top line's bars hang down -- which both identifies the line and
    keeps the marks out of the unprintable margin. Nothing is marked at the
    safe-area corners, because nothing is done there.
    """
    marks: list[str] = []

    def horizontal(y: float, inward: float) -> None:
        lo = margin_x
        hi = margin_x + safe_w
        marks.append(
            f'<line class="join-line" x1="{fmt(lo)}" y1="{fmt(y)}"'
            f' x2="{fmt(hi)}" y2="{fmt(y)}"/>'
        )
        for x in (lo, hi):
            marks.append(
                f'<line class="join-bar" x1="{fmt(x)}" y1="{fmt(y)}"'
                f' x2="{fmt(x)}" y2="{fmt(y + inward * MARK_BAR)}"/>'
            )

    def vertical(x: float, inward: float) -> None:
        lo = margin_y
        hi = margin_y + safe_h
        marks.append(
            f'<line class="join-line" x1="{fmt(x)}" y1="{fmt(lo)}"'
            f' x2="{fmt(x)}" y2="{fmt(hi)}"/>'
        )
        for y in (lo, hi):
            marks.append(
                f'<line class="join-bar" x1="{fmt(x)}" y1="{fmt(y)}"'
                f' x2="{fmt(x + inward * MARK_BAR)}" y2="{fmt(y)}"/>'
            )

    if r < rows - 1:
        # Near the page's bottom edge: bars rise into the page.
        horizontal(margin_y + safe_h - overlap_y, inward=-1.0)
    if r > 0:
        # Near the page's top edge: bars hang down into the page.
        horizontal(margin_y, inward=1.0)
    if c < cols - 1:
        vertical(margin_x + safe_w - overlap_x, inward=-1.0)
    if c > 0:
        vertical(margin_x, inward=1.0)

    return ''.join(marks)


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
    """Dashed grey line showing the far edge of the duplicated band.

    This is *information*, not an alignment target: it marks where this page's
    copy of the overlap stops being the neighbour's -- the band runs from the
    join line (see :func:`join_marks`) to this line, and the neighbour prints the
    same strip. Lining this edge up with the neighbour's join line instead of
    with the matching band edge would shift the seam by the overlap.
    """
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
    fits, else a cols x rows grid.

    ``fit`` bounds the single-page case and defaults to the safe area. Passing the
    page trim instead lets a sheet that overruns the safe margin still land on one
    page -- centered, so the overrun splits evenly into both margins and is *not*
    clipped away. Tiling beyond one page still strides over the safe area.

    Page furniture (cut/align marks, the overlap band edge, the page note) is
    *not* emitted here: only the clip and the content are, so that marks carrying
    page numbers can be added once the document's page order is known. See
    :func:`join_marks` and :func:`overlap_marks`.
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
    shared_defs: list[str] | None = None,
    provenance: str | None = None,
) -> str:
    """Emit tiled pages as a single Inkscape print document (pages laid out side by
    side; one ``<inkscape:page>`` per physical page).

    Each page carries its own trim size, so portrait and landscape pages can share
    one document: pages are placed left to right by accumulating their widths, and
    the drawing is as tall as the tallest page.

    The root element's own size is the *first* page's trim, not the whole strip:
    Inkscape's multipage PDF export takes page 1's size from the root element and
    ignores that page's ``<inkscape:page>``, so a root spanning the strip would
    export page 1 as the entire strip and drop the real first page. Note that this
    makes page 1 the only page a plain SVG viewer (a browser, say) shows, since it
    clips to the root viewport; Inkscape itself shows every page either way.

    ``shared_defs`` are rendered into the document-level ``<defs>``; an empty
    ``<defs>`` is emitted when there are none, so callers never have to rewrite the
    element after the fact. ``provenance`` becomes a comment before ``<svg>``, where
    it cannot collide with the element structure.
    """
    if not pages:
        raise ValueError('no pages to emit')

    root_w = pages[0].paper.trim.width
    root_h = pages[0].paper.trim.height

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

    if doc_name is None:
        doc_name = 'sheets-print.svg'

    if shared_defs:
        defs_block = (
            '  <defs\n'
            '     id="defs1">\n'
            + '\n'.join(shared_defs) + '\n'
            '  </defs>\n'
        )
    else:
        defs_block = (
            '  <defs\n'
            '     id="defs1" />\n'
        )

    provenance_block = f'<!-- {provenance} -->\n' if provenance else ''

    indented_groups = '\n'.join(
        ('  ' + line) if line else line for line in '\n'.join(page_groups).split('\n')
    )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<!-- Created with Inkscape (http://www.inkscape.org/) -->\n'
        + provenance_block + '\n'
        '<svg\n'
        f'   width="{fmt(root_w)}mm"\n'
        f'   height="{fmt(root_h)}mm"\n'
        f'   viewBox="0 0 {fmt(root_w)} {fmt(root_h)}"\n'
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
        + defs_block
        + f'  <style type="text/css">{style_css}{JOIN_CSS}</style>\n'
        '  <g id="pages">\n'
        + indented_groups + '\n'
        '  </g>\n'
        '</svg>\n'
    )


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------


def has_sheet_class(el: ET.Element) -> bool:
    """True when ``sheet`` is one of the element's ``class`` tokens.

    A token test, not a substring one (case-sensitive, as CSS class names are):
    ``class="sheet"`` and ``class="sheet label"`` match, while ``class="worksheet"``,
    ``class="sheets"`` and ``class="sheet-bounds"`` do not. The sheets documents
    carry generated groups whose names merely *contain* "sheet" -- ``-half``,
    ``-labels``, ``-mirror``, ``-reg``, the ``sheet-bounds`` rect -- so the loose
    match this replaced was one class attribute away from tiling them by mistake.
    """
    return 'sheet' in (el.get('class') or '').split()


def find_sheets(root: ET.Element) -> list[SheetDef]:
    """Find ``<g>`` groups whose ``class`` contains "sheet" and that carry a
    background ``<rect>`` (the sheet bounds) as a *direct* child -- wrapper groups
    nest their rect one level deeper and are skipped, as are class-marked groups
    with no ``id`` (the emitted ``<use>`` needs one; a warning is printed).

    The rect's position is recorded as well as its size: the bounds may sit
    anywhere inside the group (or the group may carry a ``translate``), and since
    ``<use>`` reproduces both, the tiler has to cancel that offset or the page
    shows empty space where the artwork should be. A group that also rotates or
    scales its content is reported, because the tiler then still treats the sheet
    as an axis-aligned rectangle of the rect's own size.

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
        combined = matrix_multiply(
            parse_transform(el.get('transform')),
            parse_transform(rect.get('transform')),
        )
        if not is_translation(combined):
            print(
                f'warning: <g id="{el_id}"> is rotated, skewed or scaled; the tiler'
                ' places it by its bounds rect corner and tiles the rect size as-is',
                file=sys.stderr,
            )
        order_attr = el.get('data-sort-order')
        parsed = float('inf') if order_attr is None else js_number(order_attr)
        raw.append({
            'id': el_id,
            'width': w,
            'height': h,
            'offset': bounds_offset(el, rect),
            'order': parsed if math.isfinite(parsed) else float('inf'),
            'index': len(raw),
        })
    raw.sort(key=lambda r: (r['order'], r['index']))
    return [
        SheetDef(
            id=str(r['id']),
            width=float(r['width']),
            height=float(r['height']),
            offset=r['offset'],  # type: ignore[arg-type]
        )
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
    """Separate positional arguments from ``--flags`` and their values.

    Which flags take a value is known here, rather than guessed from the next
    token: guessing made ``--whatif sheets.svg`` swallow the input document, and it
    turned a typo like ``--saef`` into a value-less flag that was then ignored. An
    unrecognised flag is now an error, and a value-taking flag given no value
    records as present-with-no-value so :func:`run` reports it as a usage error
    rather than misreading the rest of the command line.
    """
    positional: list[str] = []
    flags: dict[str, str | None] = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith('--'):
            positional.append(a)
            i += 1
            continue
        name = a[2:]
        if name in BOOLEAN_FLAGS:
            flags[name] = None
        elif name in VALUE_FLAGS:
            nxt = argv[i + 1] if i + 1 < len(argv) else None
            if nxt is None or nxt.startswith('--'):
                flags[name] = None
            else:
                flags[name] = nxt
                i += 1
        else:
            known = ', '.join(sorted(VALUE_FLAGS | BOOLEAN_FLAGS))
            raise ValueError(f'unknown option --{name}; known options: {known}')
        i += 1
    return positional, flags


def flag_value(flags: dict[str, str | None], name: str, example: str) -> str:
    """The value of a required flag, or a usage error naming how to supply it."""
    value = flags.get(name)
    if value is None:
        raise ValueError(f'--{name} needs a value ({example})')
    return value


def safe_area_for(trim: Size, margin: float) -> Size:
    """The printable area: the trim inset by ``margin`` mm on every edge.

    A trim that cannot hold the margin at all is a usage error rather than a
    negative safe area that fails later inside the tiler.
    """
    width = round6(trim.width - 2 * margin)
    height = round6(trim.height - 2 * margin)
    if width <= 0 or height <= 0:
        raise ValueError(
            f'margin {fmt(margin)} mm leaves no printable area on a '
            f'{fmt(trim.width)} x {fmt(trim.height)} mm sheet'
        )
    return Size(width=width, height=height)


def resolve_paper(flags: dict[str, str | None]) -> tuple[str, Size, Size]:
    """Resolve ``--paper`` (or ``--size``) plus ``--margin``/``--safe``.

    Returns ``(token, trim, safe_area)``. The token is the paper's public name and
    is what the provenance stamp and the caller's filename use; ``--size`` has no
    name to give, so it stamps as ``custom``. Only the trim is tabulated -- the
    safe area is derived from the margin, or given outright by ``--safe``.
    """
    paper_name = flags.get('paper')
    size_spec = flags.get('size')
    if paper_name is not None and size_spec is not None:
        raise ValueError('give either --paper or --size, not both')
    if size_spec is not None:
        token = 'custom'
        trim = size(size_spec)
    elif paper_name is not None:
        token = paper_name.strip().lower()
        if token not in PAPERS:
            names = ', '.join(PAPERS)
            raise ValueError(
                f'unknown --paper "{paper_name}"; choose one of {names}\n'
                + format_paper_table()
            )
        trim = PAPERS[token]
    else:
        raise ValueError(
            'no paper given: pass --paper <name> or --size WxH (--list-papers'
            ' prints the table)\n' + format_paper_table()
        )

    safe_spec = flags.get('safe')
    if safe_spec is not None:
        safe_area = size(safe_spec)
    elif 'margin' in flags:
        safe_area = safe_area_for(trim, dist(flag_value(flags, 'margin', 'e.g. 5')))
    else:
        safe_area = safe_area_for(trim, DEFAULT_MARGIN)
    return token, trim, safe_area


def format_paper_table() -> str:
    """The ``--paper`` table, one line per name (usage errors and --list-papers).

    Dimensions are shown at the default margin, which is what most callers get;
    ``--margin`` moves every safe area in step.
    """
    header = f'{"paper":<8} {"trim (mm)":<16} safe (mm) at margin {fmt(DEFAULT_MARGIN)}'
    lines = [header]
    for name, trim in PAPERS.items():
        safe = safe_area_for(trim, DEFAULT_MARGIN)
        lines.append(
            f'{name:<8} {f"{fmt(trim.width)} x {fmt(trim.height)}":<16} '
            f'{fmt(safe.width)} x {fmt(safe.height)}'
        )
    return '\n'.join(lines)


# Class selectors in a stylesheet: `.join-line`, or the `.a` of `.a.b`/`.a > .b`.
_CLASS_SELECTOR_RE = re.compile(r'\.([A-Za-z_][\w-]*)')


def defined_classes(css: str) -> set[str]:
    """Class names a stylesheet gives a rule to (a selector-level scan)."""
    return set(_CLASS_SELECTOR_RE.findall(css))


def require_style_rules(style_css: str) -> None:
    """Fail unless the carried stylesheet styles everything a page renders.

    The output document styles the sheets it references through ``<use>`` and draws
    its own page furniture, so the style text copied from the master plus
    :data:`JOIN_CSS` has to cover both. A missing rule is not an error any later
    step reports -- the page simply renders unstyled -- so it is checked here,
    where the cause is still known.
    """
    defined = defined_classes(style_css + JOIN_CSS)
    missing = [
        f'  {sel} ({what})'
        for sel, what in REQUIRED_PAGE_RULES
        if sel.lstrip('.') not in defined
    ]
    if missing:
        raise ValueError(
            'the source stylesheet does not style the generated pages; missing:\n'
            + '\n'.join(missing)
        )


# Regexes for the shared-defs rewrite: the first tiled page's per-tile clip path is
# hoisted into document-level defs.
_CLIP_DEFS_RE = re.compile(r'<defs><clipPath id="clip-[^"]+"><rect [^>]*/></clipPath></defs>\n?')
_CLIP_REF_RE = re.compile(r'clip-path="url\(#clip-[^)]*\)"')

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
    href: str,
    paper_token: str,
    trim: Size,
    safe_area: Size,
    overlap: float,
    gap: float,
    provenance: str,
    svg_bytes: int,
    has_clip: bool,
    join_lines: int,
    overwrite_bytes: int | None,
) -> str:
    """Report what a run would generate, without generating it (``--whatif``).

    Prints the resolved sheet href as well as the output path: the href depends on
    where the output goes, so a wrong ``--out`` shows up here as a reference that
    does not resolve, before anything is written.

    Deliberately ASCII-only: this is read in a terminal of any code page. That is
    also why the legend spells the marks out in words: these lines are the only
    place the cut/align convention is stated where a user will actually see it
    before printing.
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
    if join_lines:
        features.append(f'cut/align marks on {join_lines} tiled pages')

    lines = [
        'whatif: nothing written, no output generated',
        '',
        f'input       {in_path}',
        f'reference   {href}',
        f'output      {out_path}',
        f'            {out_note}',
        f'paper       {paper_token}: trim {fmt(trim.width)} x {fmt(trim.height)} mm '
        f'(landscape {fmt(trim.height)} x {fmt(trim.width)} mm), '
        f'safe {fmt(safe_area.width)} x {fmt(safe_area.height)} mm, '
        f'margins {fmt(margin_x)} x {fmt(margin_y)} mm',
        f'            overlap {fmt(overlap)} mm, gap {fmt(gap)} mm; page orientation chosen '
        f'per sheet, fitted to the page',
        f'document    {pages} pages across {len(planned)} sheets '
        f'({tiled} tiled over multiple pages, {len(planned) - tiled} fitting one page), '
        f'{fmt(doc_w)} x {fmt(doc_h)} mm',
        f'content     {", ".join(features)}',
        f'provenance  {provenance}',
        '',
        'marks       every tiled page marks its join line in grey, dotted, closed by',
        '            a solid 5 mm bar at each end pointing into the page. The line at',
        '            the top of a page is the one to align on the neighbouring cut; a',
        '            line with content below it is the one to cut. The cut may fall',
        '            anywhere in the overlap band. The grey dashed line is the far edge',
        '            of that band only - never an alignment target.',
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


def rel_href(in_path: str, out_path: str) -> str:
    """The sheet reference to write, relative to the output file's directory.

    The master and its print documents live in different trees, so the reference is
    computed from where the output goes rather than assumed co-located. Separators
    are normalised to ``/``: ``relpath`` returns backslashes on Windows, and a
    backslash in an IRI is either an escape or a malformed reference.
    """
    rel = os.path.relpath(in_path, start=os.path.dirname(out_path)).replace(os.sep, '/')
    return quote(rel, safe=_URI_SAFE)


def provenance_comment(
    *,
    source: str,
    paper_token: str,
    trim: Size,
    safe_area: Size,
    overlap: float,
    gap: float,
    pages: int,
) -> str:
    """A one-comment record of the parameters this document was tiled with.

    Reads back the paper's *name* as well as its resolved millimetres: the name is
    what the caller asked for, the millimetres are what the table gave, and a
    tabulated size that later drifts shows up as the two disagreeing. Written as
    one XML comment, wrapped to keep the line readable in an editor.
    """
    return (
        f'tiled by tile_sheets.py: source={esc(source)} paper={esc(paper_token)}'
        f' trim={fmt(trim.width)}x{fmt(trim.height)}mm'
        f' safe={fmt(safe_area.width)}x{fmt(safe_area.height)}mm'
        f' overlap={fmt(overlap)}mm gap={fmt(gap)}mm'
        f' pages={pages} orientation=per-sheet'
    )


def run(positional: list[str], flags: dict[str, str | None]) -> int:
    if not positional:
        raise ValueError('no input document given\n' + USAGE)
    if len(positional) > 1:
        raise ValueError(
            f'unexpected argument "{positional[1]}"; the page size is given by'
            ' --paper or --size, not positionally\n' + USAGE
        )

    input_arg = positional[0]
    in_path = os.path.abspath(input_arg)

    out_arg = flags.get('out')
    if out_arg is None:
        raise ValueError(
            '--out is required: the master and its print documents live in'
            ' different trees, so the output location cannot be inferred\n' + USAGE
        )
    out_path = os.path.abspath(out_arg)

    paper_token, trim, safe_area = resolve_paper(flags)
    overlap = (
        dist(flag_value(flags, 'overlap', 'e.g. 12'))
        if 'overlap' in flags else float(DEFAULT_OVERLAP)
    )
    gap = (
        dist(flag_value(flags, 'gap', 'e.g. 10'))
        if 'gap' in flags else float(DEFAULT_GAP)
    )

    portrait, landscape = orientation_papers(trim, safe_area, overlap)

    with open(in_path, 'rb') as fh:
        doc = parse_svg(fh.read())

    # The href is relative to the output file, not to the master: the print
    # documents sit three levels below the masters under targets/<target>/<content>/.
    href = rel_href(in_path, out_path)

    sheets = find_sheets(doc)
    if not sheets:
        print(
            f'no groups with a "sheet" class (and a direct <rect> child, and an id)'
            f' found in {in_path}',
            file=sys.stderr,
        )
        return 1

    # Carry the sheets' own stylesheet over so their classes resolve in the output.
    # A <use> clone takes its class names from the referencing document, so the
    # output has to carry the rules itself to render standalone; the rules the pages
    # need beyond that are the tiler's own (JOIN_CSS).
    style_css = first_style_text(doc)
    require_style_rules(style_css)

    pages: list[EnginePage] = []
    planned: list[PlannedSheet] = []
    # The safe-area clip rect depends on the page geometry, so there is one hoisted
    # defs entry per distinct geometry (portrait and landscape). The cut/align marks
    # are not hoisted: their labels name the page numbers on either side of the
    # join, so they differ per page.
    shared_clips: dict[tuple[str, ...], str] = {}

    for sheet in sheets:
        title = sheet.id.removeprefix('sheet-')
        use_ref = f'<use href="{esc(f"{href}#{sheet.id}")}"/>'
        # The sheet's bounds rect need not sit at its group's origin, and the group
        # itself may be translated; <use> copies that faithfully, so cancel it here
        # or the page would show whatever happens to lie at the group origin --
        # often nothing at all.
        ox, oy = sheet.offset
        if ox or oy:
            use_ref = f'<g transform="translate({fmt(-ox)} {fmt(-oy)})">{use_ref}</g>'
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
            margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y = mark_geometry(layout.paper)
            col = (page.tile_index - 1) % page.cols
            row = (page.tile_index - 1) // page.cols
            page_body += overlap_marks(
                col, row, page.cols, page.rows,
                margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y,
            )
            page_body += join_marks(
                col, row, page.cols, page.rows,
                margin_x, margin_y, safe_w, safe_h, overlap_x, overlap_y,
            )
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
    shared_defs: list[str] = []
    for key, clip_id in shared_clips.items():
        safe_w, safe_h, margin_x, margin_y = key
        shared_defs.append(
            f'    <clipPath id="{clip_id}"><rect x="{margin_x}" y="{margin_y}"'
            f' width="{safe_w}" height="{safe_h}"/></clipPath>'
        )
    provenance = provenance_comment(
        source=href,
        paper_token=paper_token,
        trim=trim,
        safe_area=safe_area,
        overlap=overlap,
        gap=gap,
        pages=len(pages),
    )
    svg = emit_multipage_svg(
        pages,
        style_css,
        gap=gap,
        doc_name=os.path.basename(out_path),
        shared_defs=shared_defs,
        provenance=provenance,
    )

    if 'whatif' in flags:
        print(format_whatif(
            planned,
            in_path=in_path,
            out_path=out_path,
            href=href,
            paper_token=paper_token,
            trim=trim,
            safe_area=safe_area,
            overlap=overlap,
            gap=gap,
            provenance=provenance,
            svg_bytes=len(svg.encode('utf-8')),
            has_clip=bool(shared_clips),
            join_lines=sum(1 for p in pages if p.cols > 1 or p.rows > 1),
            overwrite_bytes=os.path.getsize(out_path) if os.path.exists(out_path) else None,
        ))
        return 0

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # newline='' keeps the '\n' the emitter produced on every platform.
    with open(out_path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(svg)

    print(f'wrote {out_path} \u2014 {len(pages)} pages from {len(sheets)} sheets')
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        positional, flags = parse_args(list(sys.argv[1:] if argv is None else argv))
        if 'list-papers' in flags:
            print(format_paper_table())
            return 0
        return run(positional, flags)
    except (ValueError, OSError) as exc:
        print(f'tile_sheets.py: error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
