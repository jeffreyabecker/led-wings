"""Generate a printable, multi-page PDF of feather templates.

Each logical page holds one feather pair: the as-built (right-hand) feather from
mechanical/templates/as-built/vectors/individuals and its mirror image placed
side-to-side, so the pair can be cut as a left/right wing set.

Pages print at TRUE SCALE: the source SVGs are authored 1 user unit = 1 mm, so
geometry is emitted unchanged and the PDF MediaBox simply uses that grain.
Every page is 279 mm wide (the requested maximum) with a height that adapts to
the feather; the pair straddles the page's vertical mirror axis.

Usage:
    python tools/make_feather_template_pdf.py
    python tools/make_feather_template_pdf.py --only P1 B5 LC1
    python tools/make_feather_template_pdf.py --scale 0.8      # shrink to fit a smaller printer
    python tools/make_feather_template_pdf.py --out some/other.pdf
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feather_geometry import (  # noqa: E402
    Feather,
    load_feather,
    mat_apply,
    mat_mul,
    mat_scale,
    mat_translate,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = REPO_ROOT / "mechanical" / "templates" / "as-built" / "vectors" / "individuals"
DEFAULT_OUT = (
    REPO_ROOT / "mechanical" / "templates" / "as-built" / "print" / "feathers-mirrored-pairs.pdf"
)
FLATTEN_TOL_MM = 0.005          # max chord deviation when flattening curves
PT_PER_MM = 72.0 / 25.4

# Feather order: inner primary (P1) through to the small lower coverts.
FEATHER_ORDER = (
    [f"P{i}" for i in range(1, 7)]
    + [f"S{i}" for i in range(1, 7)]
    + [f"B{i}" for i in range(1, 6)]
    + [f"SC{i}" for i in range(1, 9)]
    + [f"PC{i}" for i in range(1, 4)]
    + [f"A{i}" for i in range(1, 5)]
    + [f"MC{i}" for i in range(1, 6)]
    + [f"LC{i}" for i in range(1, 6)]
)

# ---------------------------------------------------------------------------
# layout constants (millimetres)
# ---------------------------------------------------------------------------
PAGE_WIDTH_MM = 273.0           # hard maximum page width
MARGIN_MM = 12.0                # page edge to the outermost content
# Clear space between pairs, measured between cut outlines so there is room to
# paint over the stencil edges. Sparse pages get a much wider berth.
SPARSE_GAP_MM = 70.0            # around a row that holds a single pair
DENSE_GAP_MM = 30.0             # between pairs sharing a row, and between rows
# Vertical furniture above the first pair: a title line and a subtitle line.
HEAD_MM = 18.0
# Per-pair band above each pair, holding two stacked text lines: the half labels
# ("LEFT - mirror" / "RIGHT - as built") and, below them, the feather ID. Two
# lines rather than one so the ID can never collide with a half label on a narrow
# pair, where the labels reach inwards.
LABEL_BAND_MM = 11.6
FOOT_MM = 15.0
LABEL_SIZE_MM = 4.4
ID_SIZE_MM = 6.0                # feather ID inside a half
ID_LINE_MM = 7.6                # baseline of the ID line, above the pair
FOOT_SIZE_MM = 3.0
LABEL_GAP_MM = 0.9              # gap from the pair to its ID line
MIN_PAGE_HEIGHT_MM = 60.0
SCALE_BAR_MM = 50.0
MAX_PAGE_HEIGHT_MM = 1050.0     # pages are packed up to about this height
GROUP_JOIN = (("SC", "PC", "A"), ("MC", "LC"))

HALF_FILL = (0.93, 0.93, 0.93)
GUIDE_GREY = (0.55, 0.55, 0.55)
TEXT_GREY = (0.25, 0.25, 0.25)

HELVETICA_WIDTHS = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, "0": 556, "1": 556, "2": 556, "3": 556, "4": 556,
    "5": 556, "6": 556, "7": 556, "8": 556, "9": 556, ":": 278, ";": 278,
    "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015, "A": 667, "B": 667,
    "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722, "I": 278,
    "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778, "P": 667,
    "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469,
    "_": 556, "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556,
    "f": 278, "g": 556, "h": 556, "i": 222, "j": 222, "k": 500, "l": 222,
    "m": 833, "n": 556, "o": 556, "p": 556, "q": 556, "r": 333, "s": 500,
    "t": 278, "u": 556, "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584,
}


def text_width_mm(text: str, size_mm: float) -> float:
    """Width of `text` in Helvetica at `size_mm` cap-to-descender size (1/1000 em units)."""
    return sum(HELVETICA_WIDTHS.get(c, 556) for c in text) / 1000.0 * size_mm


# ---------------------------------------------------------------------------
# PDF primitives
# ---------------------------------------------------------------------------
def num(value: float, places: int = 3) -> str:
    out = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return out if out not in ("", "-0", "-0.", "0.") else "0"


def pdf_string(text: str) -> str:
    out = []
    for ch in text:
        if ch in "()\\":
            out.append("\\" + ch)
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            out.append(f"\\{ord(ch) & 0xFF:03o}")
    return "".join(out)


def rgb(color) -> str:
    return " ".join(num(c, 3) for c in color)


def text_cmd(x: float, y: float, size: float, text: str, color=TEXT_GREY,
             align: str = "left", halo_mm: float = 0.0) -> str:
    """Emit text with `size` as the em size in millimetres.

    `halo_mm` gives the text an opaque white backing so it stays legible over the
    drawing. Stroking glyphs in white is deliberately avoided: renderers differ
    on how they composite a stroke-only or fill+stroke glyph, and PDFium erases
    the text entirely. An explicit white rectangle is unambiguous.
    """
    width = text_width_mm(text, size)
    if align == "center":
        x -= width / 2.0
    elif align == "right":
        x -= width
    body = (
        f"/F1 {num(size)} Tf 1 0 0 1 {num(x)} {num(y)} Tm ({pdf_string(text)}) Tj"
    )
    if halo_mm <= 0:
        return f"BT {rgb(color)} rg {body} ET"
    pad = halo_mm
    backing = (
        f"{rgb((1, 1, 1))} rg "
        f"{num(x - pad)} {num(y - pad)} m "
        f"{num(x + width + pad)} {num(y - pad)} l "
        f"{num(x + width + pad)} {num(y + size + pad)} l "
        f"{num(x - pad)} {num(y + size + pad)} l h f"
    )
    return f"{backing}\nBT {rgb(color)} rg {body} ET"


def path_cmd(transformed_polys, close: bool = True) -> str:
    """Emit PDF path construction operators for already page-space polylines."""
    parts = []
    for poly in transformed_polys:
        if len(poly) < 2:
            continue
        parts.append(f"{num(poly[0][0])} {num(poly[0][1])} m")
        for x, y in poly[1:]:
            parts.append(f"{num(x)} {num(y)} l")
        if close:
            parts.append("h")
    return "\n".join(parts)


def transform_polys(polys, matrix):
    return [[mat_apply(matrix, x, y) for x, y in poly] for poly in polys]


def mat_fit(box, x0: float, y0: float) -> tuple:
    """Map a bbox onto the rectangle whose lower-left corner is (x0, y0), flipping y."""
    bx0, by0, bx1, by1 = box
    sx = 1.0
    sy = -1.0
    tx = x0 - bx0
    ty = y0 + by1
    return (sx, 0.0, 0.0, sy, tx, ty)


# ---------------------------------------------------------------------------
# page building
# ---------------------------------------------------------------------------
@dataclass
class PairSlot:
    """One mirrored feather pair placed at a known position on a page."""

    feather: Feather
    axis_x: float
    cell_left: float           # left edge of the pair's cell (feather only)
    cell_right: float          # right edge of the pair's cell
    pair_top: float            # y of the feather apex
    pair_bottom: float
    label_y: float             # baseline of the half labels
    right_box: tuple           # page rect of the right-wing (as-built) half
    left_box: tuple            # page rect of the left-wing (mirrored) half
    right_to_page: tuple       # as-built geometry -> page (right of the axis)
    left_to_page: tuple        # as-built geometry -> page (mirror, left of the axis)

    @property
    def name(self) -> str:
        return self.feather.name


@dataclass
class PageLayout:
    """A logical page holding one or more mirrored pairs."""

    page_w: float
    page_h: float
    slots: list
    title: str
    stroke_scale: float

    @property
    def names(self) -> list:
        return [s.name for s in self.slots]


def mat_scale_about(sx: float, sy: float, cx: float, cy: float) -> tuple:
    """Uniform scale by (sx, sy) about the point (cx, cy)."""
    return mat_mul(
        mat_mul(mat_translate(cx, cy), mat_scale(sx, sy)),
        mat_translate(-cx, -cy),
    )


def make_slot(feather: Feather, axis_x: float, pair_bottom: float,
              scale: float) -> PairSlot:
    """Place one mirrored pair so its apex is at `pair_bottom + height`.

    The source geometry is the right wing as built. On the page the as-built half
    occupies the RIGHT-hand side of the axis and its reflection occupies the
    LEFT-hand side, matching how the two wings sit on the bird.
    """
    cut = feather.cut_box
    half_w = (cut[2] - cut[0]) * scale
    half_h = (cut[3] - cut[1]) * scale
    pair_top = pair_bottom + half_h

    # as-built geometry goes on the right-hand side of the axis
    right_to_page = mat_fit(cut, axis_x, pair_bottom)
    # Reflect it about the axis for the left wing. The reflection is composed in
    # page space (translate-to-origin, scale -1 on x, translate back) and applied
    # to the already-fitted page coordinates.
    reflect = mat_mul(
        mat_mul(mat_translate(axis_x, 0.0), mat_scale(-1.0, 1.0)),
        mat_translate(-axis_x, 0.0),
    )
    left_to_page = mat_mul(reflect, right_to_page)

    if scale != 1.0:
        # Shrink about the mirror axis, not the page origin: scaling about the
        # origin would also scale the axis position and collapse the mirrored
        # half onto the as-built one.
        shrink = mat_scale_about(scale, scale, axis_x, 0.0)
        right_to_page = mat_mul(shrink, right_to_page)
        left_to_page = mat_mul(shrink, left_to_page)
        pair_top = pair_bottom + (cut[3] - cut[1]) * scale

    return PairSlot(
        feather=feather,
        axis_x=axis_x,
        cell_left=axis_x - half_w,
        cell_right=axis_x + half_w,
        pair_top=pair_top,
        pair_bottom=pair_bottom,
        label_y=pair_top + LABEL_GAP_MM,
        right_box=fit_bbox(cut, right_to_page),
        left_box=fit_bbox(cut, left_to_page),
        right_to_page=right_to_page,
        left_to_page=left_to_page,
    )


def pair_size(feather: Feather, scale: float = 1.0) -> tuple:
    """(width, height) of one mirrored pair's cut footprint, in millimetres."""
    cut = feather.cut_box
    return ((cut[2] - cut[0]) * 2.0 * scale, (cut[3] - cut[1]) * scale)


def fit_bbox(box, transform) -> tuple:
    x0, y0, x1, y1 = box
    corners = [mat_apply(transform, x, y) for x in (x0, x1) for y in (y0, y1)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def row_gap(row: dict) -> float:
    """Clear space this row keeps from its neighbours."""
    return DENSE_GAP_MM if len(row["items"]) > 1 else SPARSE_GAP_MM


def _pack_rows(pairs: list) -> list:
    """Pack (key, width, height) pairs into rows, tallest-first (LPT).

    Each pair goes into the shortest row it still fits in, which keeps the rows
    close to level. Pairs sharing a row keep DENSE_GAP_MM between their cut
    outlines, so a row only ever becomes multi-pair when there is really room for
    it; a pair that will not fit beside another gets a row to itself.
    """
    content_w = PAGE_WIDTH_MM - 2.0 * MARGIN_MM
    rows: list = []
    for key, width, height in sorted(pairs, key=lambda p: -p[2]):
        if width > content_w + 1e-9:
            raise ValueError(
                f"{key}: mirrored pair is {width:.2f} mm wide, which exceeds the "
                f"{content_w:.2f} mm printable width"
            )
        best = None
        for row in rows:
            needed = width + (DENSE_GAP_MM if row["items"] else 0.0)
            if row["width"] + needed <= content_w + 1e-9:
                if best is None or row["height"] < best["height"] - 1e-9:
                    best = row
        if best is None:
            best = {"items": [], "width": 0.0, "height": 0.0}
            rows.append(best)
        best["items"].append((key, width, height))
        best["width"] += width + (DENSE_GAP_MM if len(best["items"]) > 1 else 0.0)
        best["height"] = max(best["height"], height)

    order = {key: i for i, (key, _, _) in enumerate(pairs)}
    for row in rows:
        row["items"].sort(key=lambda item: order[item[0]])
        row["width"] = sum(w for _, w, _ in row["items"]) + DENSE_GAP_MM * (
            len(row["items"]) - 1
        )
    rows.sort(key=lambda row: order[row["items"][0][0]])
    return rows


def shelf_pack(pairs: list) -> list:
    """Pack (key, width, height) pairs into rows of the content width."""
    return _pack_rows(pairs)


def page_height_for_rows(rows: list) -> float:
    """Page height a list of packed rows would need, including its row gaps."""
    body_h = sum(LABEL_BAND_MM + row["height"] for row in rows)
    for upper, lower in zip(rows, rows[1:]):
        body_h += max(row_gap(upper), row_gap(lower))
    return max(HEAD_MM + body_h + FOOT_MM, MIN_PAGE_HEIGHT_MM)


def split_rows_by_height(rows: list, max_page_h: float,
                         max_rows: int | None = None) -> list:
    """Split packed rows into pages, balanced in height and within the budget.

    A greedy fill knocks the last page down to a single row whenever the total is
    not a clean multiple of the budget, which wastes a sheet for one pair. This
    instead works out how many pages the rows need, then splits them as evenly as
    possible, so the sheets come out close to the same length.

    A single row taller than the budget still gets its own chunk, so an
    exceptionally long pair can never prevent the document from being built.
    """
    row_count = len(rows)
    if row_count == 0:
        return []
    if max_rows is not None:
        chunks = [rows[i: i + max_rows] for i in range(0, row_count, max_rows)]
        # rebalance only within the row cap, keeping each chunk legal
        return chunks

    # fewest pages that can hold the rows without exceeding the budget
    pages = 1
    while pages < row_count:
        size = row_count / pages
        fits = True
        for i in range(pages):
            start = round(i * size)
            end = round((i + 1) * size)
            if page_height_for_rows(rows[start:end]) > max_page_h + 1e-9:
                fits = False
                break
        if fits:
            break
        pages += 1

    size = row_count / pages
    chunks = []
    for i in range(pages):
        start = round(i * size)
        end = round((i + 1) * size)
        if end > start:
            chunks.append(rows[start:end])
    return chunks


def plan_pages(feathers: list, scale: float = 1.0,
               max_page_h: float = MAX_PAGE_HEIGHT_MM,
               max_rows: int | None = None) -> list:
    """Group feathers into logical pages, packing several pairs per page.

    Feathers are grouped by family (the leading letters of the ID), with
    `GROUP_JOIN` merging the families that share a page. Each group is packed into
    rows, and the rows are split across pages so no page exceeds `max_page_h`.
    `max_rows` optionally caps the rows on a page independently.
    """
    joins = {name: group for group in GROUP_JOIN for name in group}

    def family(name: str) -> str:
        letters = "".join(c for c in name if c.isalpha())
        return joins.get(letters, letters)

    groups: dict[str, list] = {}
    for feather in feathers:
        groups.setdefault(family(feather.name), []).append(feather)

    pages: list = []
    for group, members in groups.items():
        rows = _pack_rows([(f.name, *pair_size(f, scale)) for f in members])
        by_name = {f.name: f for f in members}
        title = " / ".join(group)
        for chunk in split_rows_by_height(rows, max_page_h, max_rows):
            pages.append((title, chunk, by_name))
    return pages


def layout_page(title: str, rows: list, by_name: dict, scale: float) -> PageLayout:
    """Give a page's packed rows concrete coordinates and build its slots."""
    if not rows:
        raise ValueError("a page needs at least one row")

    # Vertical budget: header, then for each row a label band plus the pairs, with
    # the row gap between rows, then the footer furniture. A row holding a single
    # pair keeps the wider sparse gap from its neighbours.
    page_h = page_height_for_rows(rows)
    content_w = PAGE_WIDTH_MM - 2.0 * MARGIN_MM
    body_h = page_h - HEAD_MM - FOOT_MM

    slots: list = []
    # rows are laid out bottom-up; the last packed row sits at the bottom
    row_bottom = page_h - HEAD_MM - body_h
    n_rows = len(rows)
    for index, row in enumerate(reversed(rows)):
        row_width = sum(w for _, w, _ in row["items"]) + DENSE_GAP_MM * (
            len(row["items"]) - 1
        )
        x = MARGIN_MM + (content_w - row_width) / 2.0
        for key, width, height in row["items"]:
            axis_x = x + width / 2.0
            slot = make_slot(by_name[key], axis_x, row_bottom + LABEL_BAND_MM, scale)
            slots.append(slot)
            x += width + DENSE_GAP_MM
        row_bottom += LABEL_BAND_MM + row["height"]
        if index != n_rows - 1:
            # the gap between these two rows is the larger of the two rows' own gaps
            upper = rows[n_rows - 2 - index]
            row_bottom += max(row_gap(row), row_gap(upper))

    return PageLayout(
        page_w=PAGE_WIDTH_MM,
        page_h=page_h,
        slots=slots,
        title=title,
        stroke_scale=scale,
    )


def slot_labels(slot: PairSlot) -> list:
    """(text, x, y, align) for a pair's half labels, as drawn on the page.

    Shared with the verifier so the label positions are not restated twice.
    """
    return [
        ("LEFT - mirror", slot.left_box[0], slot.label_y, "left"),
        ("RIGHT - as built", slot.right_box[2], slot.label_y, "right"),
    ]


def slot_id_labels(slot: PairSlot) -> list:
    """(text, x, y, align) for the feather ID above each half of a pair.

    Sits on its own line between the half labels and the pair, so it cannot
    collide with them. Anchored to each half's inner edge and pushed one em clear
    of the axis, so the two IDs of a pair never overlap.
    """
    inset = slot.axis_x - slot.cell_left
    y = slot.pair_top + ID_LINE_MM
    return [
        (f"{slot.name} L", slot.axis_x - inset, y, "left"),
        (f"{slot.name} R", slot.axis_x + inset, y, "right"),
    ]


def compute_layout_geometry(layout: PageLayout) -> str:
    """The drawing section of a page: CTMs, mirror-axis ticks and the geometry.

    Kept separate from the text furniture so the verifier can rebuild exactly this
    part and compare it against what the writer emitted.
    """
    cmds: list[str] = [
        "1 0 0 1 0 0 cm",
        f"{num(PT_PER_MM)} 0 0 {num(PT_PER_MM)} 0 0 cm",
    ]

    # The tick below each pair is drawn first because the feather apex is at the
    # top of its bounding box, so only the lower tick can touch the geometry; the
    # upper tick goes over everything once the geometry is down.
    cmds.append(f"{rgb(GUIDE_GREY)} RG {num(0.25)} w [2 2] 0 d")
    for slot in layout.slots:
        cmds.append(f"{num(slot.axis_x)} {num(slot.pair_bottom - 5.0)} m "
                    f"{num(slot.axis_x)} {num(slot.pair_bottom)} l S")
    cmds.append("[] 0 d")

    # Draw each wing from the single set of as-built outlines: the right wing
    # (as built) on the right of the axis, its reflection on the left.
    for slot in layout.slots:
        stroke = slot.feather.stroke_mm * layout.stroke_scale
        for to_page in (slot.left_to_page, slot.right_to_page):
            geometry = path_cmd(transform_polys(slot.feather.polys_right, to_page))
            # 1. halo stroke in the fill colour rounds the fill edge off under the cut line
            cmds.append(f"{rgb(HALF_FILL)} RG {num(stroke)} w")
            cmds.append(geometry)
            cmds.append("S")
            # 2. paper-coloured fill so the cut line reads clearly
            cmds.append(f"{rgb((1, 1, 1))} rg")
            cmds.append(geometry)
            cmds.append("f")
            # 3. the cut line itself
            cmds.append(f"{rgb((0, 0, 0))} RG {num(stroke)} w")
            cmds.append("1 J 1 j")
            cmds.append(geometry)
            cmds.append("S")

    # Upper axis ticks, over the geometry so the mirror axis stays visible.
    cmds.append(f"{rgb(GUIDE_GREY)} RG {num(0.25)} w [2 2] 0 d")
    for slot in layout.slots:
        cmds.append(f"{num(slot.axis_x)} {num(slot.pair_top)} m "
                    f"{num(slot.axis_x)} {num(slot.pair_top + 5.0)} l S")
    cmds.append("[] 0 d")
    return "\n".join(cmds)


def footer_pair_line(layout: PageLayout) -> str:
    """The footer line listing a page's pairs, as drawn."""
    return (f"{len(layout.slots)} pair(s): "
            + " ".join(slot.name for slot in layout.slots)
            + "   (mm, stroke centreline)")


def _check_text_fits(layout: PageLayout, scale: float) -> None:
    """Fail loudly rather than emit a header or footer that runs off the page."""
    usable = layout.page_w - 2.0 * MARGIN_MM
    scale_note = "1:1" if scale == 1.0 else f"1:{1.0 / scale:.1f} reduced"
    header = f"{layout.title}  -  mirrored pairs  ({scale_note})"
    header_w = text_width_mm(header, ID_SIZE_MM)
    if header_w > usable:
        raise ValueError(
            f"header {header_w:.1f} mm is wider than the {usable:.1f} mm content area")
    footer = footer_pair_line(layout)
    footer_w = text_width_mm(footer, FOOT_SIZE_MM)
    if footer_w > usable:
        raise ValueError(
            f"footer listing {len(layout.slots)} pairs is {footer_w:.1f} mm wide, "
            f"wider than the {usable:.1f} mm content area")


def build_page(layout: PageLayout, page_no: int, page_total: int,
               generated: str, scale: float) -> str:
    cmds: list[str] = [compute_layout_geometry(layout)]

    # Half labels sit just above their pair. The feather apex is the widest point
    # of a half, so a label anchored to the outer edge of a half cannot reach the
    # cut line; a white backing keeps it legible regardless.
    for slot in layout.slots:
        for text, x, y, align in slot_labels(slot):
            cmds.append(text_cmd(x, y, LABEL_SIZE_MM, text, color=(0, 0, 0),
                                 align=align, halo_mm=0.7))

    # Feather ID written above both halves of its pair, on its own line, so a
    # loose template can always be identified and the two sides cannot be confused.
    for slot in layout.slots:
        for text, x, y, align in slot_id_labels(slot):
            cmds.append(text_cmd(x, y, LABEL_SIZE_MM, text, color=(0, 0, 0),
                                 align=align))

    scale_note = "1:1" if scale == 1.0 else f"1:{1.0 / scale:.1f} reduced"
    header = f"{layout.title}  -  mirrored pairs  ({scale_note})"
    subtitle = "as-built geometry mirrored about each centre line"
    cmds.append(text_cmd(layout.page_w / 2.0, layout.page_h - ID_SIZE_MM, ID_SIZE_MM,
                         header, color=(0, 0, 0), align="center"))
    cmds.append(text_cmd(layout.page_w / 2.0, layout.page_h - ID_SIZE_MM - 4.6,
                         FOOT_SIZE_MM, subtitle, color=TEXT_GREY, align="center"))

    # Footer: a scale-check bar plus provenance. The bar is only meaningful at
    # true size, so a reduced print says so instead of claiming 50 mm.
    bar_y = 8.0
    bar_x = MARGIN_MM
    if scale == 1.0:
        cmds.append(f"{rgb((0, 0, 0))} RG {num(0.3)} w")
        cmds.append(f"{num(bar_x)} {num(bar_y)} m {num(bar_x + SCALE_BAR_MM)} {num(bar_y)} l S")
        for x in (bar_x, bar_x + SCALE_BAR_MM):
            cmds.append(f"{num(x)} {num(bar_y)} m {num(x)} {num(bar_y + 2.5)} l S")
        bar_note = f"{num(SCALE_BAR_MM)} mm - verify before cutting"
    else:
        bar_note = (f"reduced print: 1 mm here = {num(1.0 / scale, 2)} mm actual - "
                    f"not full size")
    cmds.append(text_cmd(bar_x, bar_y - 0.8, FOOT_SIZE_MM,
                         bar_note, color=TEXT_GREY))
    cmds.append(text_cmd(layout.page_w - MARGIN_MM, bar_y - 0.8, FOOT_SIZE_MM,
                         f"page {page_no} of {page_total}   generated {generated}",
                         color=TEXT_GREY, align="right"))
    # Pair list kept to bare IDs, and drawn from the same string the width guard
    # measures, so it can never overrun the page.
    _check_text_fits(layout, scale)
    cmds.append(text_cmd(layout.page_w / 2.0, bar_y + 4.6, FOOT_SIZE_MM,
                         footer_pair_line(layout), color=TEXT_GREY, align="center"))
    return "\n".join(cmds)


# ---------------------------------------------------------------------------
# document assembly
# ---------------------------------------------------------------------------
class PdfDocument:
    """Multi-page PDF with per-page point dimensions."""

    def __init__(self, title: str) -> None:
        self.pages: list[tuple[float, float, str]] = []
        self.metadata = {
            "Title": title,
            "Creator": "tools/make_feather_template_pdf.py (wings-pcbs)",
            "Producer": "wings-pcbs template generator",
            "CreationDate": dt.datetime.now().astimezone().strftime("D:%Y%m%d%H%M%S%z"),
        }

    def add_page(self, width_mm: float, height_mm: float, content: str) -> None:
        self.pages.append((width_mm, height_mm, content))

    def build(self) -> bytes:
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        font_obj = add(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        )
        pages_obj = add(b"")
        info_obj = add(b"")
        catalog_obj = add(b"")

        page_objs: list[int] = []
        for width_mm, height_mm, content in self.pages:
            packed = zlib.compress(content.encode("ascii"), 9)
            content_obj = add(
                b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(packed)
                + packed
                + b"\nendstream"
            )
            page_obj = add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] "
                b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
                % (
                    pages_obj,
                    num(width_mm * PT_PER_MM).encode(),
                    num(height_mm * PT_PER_MM).encode(),
                    font_obj,
                    content_obj,
                )
            )
            page_objs.append(page_obj)

        kids = b" ".join(b"%d 0 R" % n for n in page_objs)
        objects[pages_obj - 1] = b"<< /Type /Pages /Count %d /Kids [%s] >>" % (
            len(page_objs),
            kids,
        )
        info_parts = [b"<<"]
        for key, value in self.metadata.items():
            info_parts.append(b" /%s (%s)" % (key.encode(), pdf_string(value).encode()))
        info_parts.append(b" >>")
        objects[info_obj - 1] = b"".join(info_parts)
        objects[catalog_obj - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj

        out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0] * (len(objects) + 1)
        for i, body in enumerate(objects, start=1):
            offsets[i] = len(out)
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref_pos = len(out)
        out += b"xref\n0 %d\n" % (len(objects) + 1)
        out += b"0000000000 65535 f \n"
        for i in range(1, len(objects) + 1):
            out += b"%010d 00000 n \n" % offsets[i]
        out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objects) + 1,
            catalog_obj,
            info_obj,
            xref_pos,
        )
        return bytes(out)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.build())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def discover(src: Path, only: list[str] | None) -> list[Path]:
    found = {p.stem: p for p in sorted(src.glob("*.svg"))}
    if only:
        missing = [n for n in only if n not in found]
        if missing:
            raise SystemExit(f"unknown feather(s): {', '.join(missing)}")
        names = only
    else:
        names = [n for n in FEATHER_ORDER if n in found]
        names += [n for n in sorted(found) if n not in FEATHER_ORDER]
    return [found[n] for n in names]


def main(argv: list[str] | None = None) -> int:
    global SPARSE_GAP_MM, DENSE_GAP_MM

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help="directory of individual feather SVGs")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output PDF path")
    ap.add_argument("--only", nargs="+", metavar="ID", help="restrict to these feather IDs")
    ap.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="uniform print scale (1.0 = true size; 0.5 = half size)",
    )
    ap.add_argument("--list", action="store_true", help="list the pages that would be generated")
    ap.add_argument(
        "--max-page-height", type=float, default=MAX_PAGE_HEIGHT_MM, metavar="MM",
        help="fill each logical page up to about this height (default "
             f"{MAX_PAGE_HEIGHT_MM:.0f} mm)",
    )
    ap.add_argument(
        "--max-rows", type=int, default=None, metavar="N",
        help="also cap the rows stacked on one logical page (default: no cap)",
    )
    ap.add_argument("--spacing", type=float, default=None, metavar="MM",
                    help="clear space between pairs sharing a row (default "
                         f"{DENSE_GAP_MM:g} mm; a lone pair keeps "
                         f"{SPARSE_GAP_MM:g} mm from its neighbours)")
    args = ap.parse_args(argv)

    if args.spacing is not None:
        if args.spacing < 0:
            raise SystemExit("--spacing cannot be negative")
        DENSE_GAP_MM = args.spacing
        SPARSE_GAP_MM = max(SPARSE_GAP_MM, args.spacing)
    if args.max_rows is not None and args.max_rows < 1:
        raise SystemExit("--max-rows must be at least 1")
    if args.max_page_height <= 0:
        raise SystemExit("--max-page-height must be positive")
    if args.scale <= 0:
        raise SystemExit("--scale must be positive")

    paths = discover(args.src, args.only)
    if not paths:
        raise SystemExit(f"no feather SVGs found in {args.src}")
    feathers = [load_feather(p) for p in paths]

    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]

    if args.list:
        for index, layout in enumerate(layouts, start=1):
            names = ", ".join(layout.names)
            print(f"page {index:2}  {layout.page_w:6.1f} x {layout.page_h:7.1f} mm  "
                  f"{len(layout.slots)} pair(s)  {names}")
        return 0

    doc = PdfDocument("Feather templates - mirrored left/right pairs")
    generated = dt.date.today().isoformat()
    for index, layout in enumerate(layouts, start=1):
        content = build_page(layout, index, len(layouts), generated, args.scale)
        doc.add_page(layout.page_w, layout.page_h, content)
    doc.write(args.out)

    heights = [l.page_h for l in layouts]
    print(f"wrote {args.out}")
    print(f"  pages       : {len(layouts)} (from {len(feathers)} feather pairs)")
    print(f"  scale       : {args.scale:g} : 1")
    print(f"  page width  : {PAGE_WIDTH_MM:g} mm (max)")
    print(f"  page height : {min(heights):.1f} .. {max(heights):.1f} mm")
    print(f"  spacing     : {DENSE_GAP_MM:g} mm between pairs in a row, "
          f"{SPARSE_GAP_MM:g} mm around a lone pair")
    for index, layout in enumerate(layouts, start=1):
        print(f"    page {index:2}: {len(layout.slots)} pair(s) "
              f"{layout.page_w:.0f}x{layout.page_h:.0f} mm  "
              f"[{', '.join(layout.names)}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
