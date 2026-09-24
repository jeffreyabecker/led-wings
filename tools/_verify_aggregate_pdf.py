"""Verify a PDF produced by make_feather_template_pdf_from_aggregate.py.

Four independent passes over the same artifact:

* the PDF's own structure -- objects, xref offsets, trailer, per-page MediaBox --
  is parsed straight out of the bytes;
* each page's *emitted geometry stream* is compared, line for line, against the
  layout rebuilt from the aggregate: this is what proves every coordinate, stroke
  width and operator the writer emitted;
* the placement rules are re-derived from the layout: the as-drawn half on one side
  of its mirror axis and its reflection on the other, the two halves exact
  reflections, the gap between them, the gap between neighbouring pairs, nothing
  escaping the page;
* every feather must be standing on its own long axis -- the whole point of reading
  the aggregate, which stores most of them rotated.

Usage:
    python tools/_verify_aggregate_pdf.py <pdf> [--aggregate FILE] [--scale S]
                                          [--pair-orientation auto]
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_feather_template_pdf_from_aggregate as gen  # noqa: E402

OBJ_RE = re.compile(rb"(\d+) 0 obj\b(.*?)\bendobj", re.S)
STREAM_LEN_RE = re.compile(rb"/Length\s+(\d+)")
NUM = r"-?\d+(?:\.\d+)?"
UPRIGHT_TOL_DEG = 1.0        # how far a straightened long axis may sit off vertical


def parse_objects(data: bytes) -> dict:
    return {int(m.group(1)): m.group(2) for m in OBJ_RE.finditer(data)}


def extract_stream(body: bytes):
    """Return the raw stream bytes, trusting the declared /Length."""
    m = re.search(rb"stream\r?\n", body)
    if not m:
        return None
    length_m = STREAM_LEN_RE.search(body[: m.start()])
    if not length_m:
        return None
    length = int(length_m.group(1))
    start = m.end()
    data = body[start: start + length]
    if len(data) != length:
        return None
    if not re.match(rb"\r?\n?\s*endstream", body[start + length: start + length + 20]):
        return None
    return data


def check_xref(data: bytes, objects: dict) -> list:
    errors = []
    m = re.search(rb"startxref\s+(\d+)", data)
    if not m:
        return ["no startxref"]
    start = int(m.group(1))
    if data[start:start + 4] != b"xref":
        return ["startxref does not point at an xref table"]
    header = re.match(rb"xref\s+0\s+(\d+)\s+", data[start:])
    if not header:
        return ["malformed xref header"]
    count = int(header.group(1))
    if count != len(objects) + 1:
        errors.append(f"xref count {count} != objects {len(objects)} + 1")
    body_start = start + header.end()
    for i in range(1, count):
        entry = data[body_start + i * 20: body_start + (i + 1) * 20]
        mm = re.match(rb"(\d{10}) (\d{5}) ([nf])", entry)
        if not mm:
            errors.append(f"xref entry {i} malformed: {entry!r}")
            continue
        offset, _, kind = mm.groups()
        if kind == b"n":
            actual = data.find(b"%d 0 obj" % i)
            if int(offset) != actual:
                errors.append(f"xref entry {i} offset {int(offset)} != actual {actual}")
    trailer = re.search(rb"trailer\s*<<(.*?)>>", data, re.S)
    if not trailer:
        errors.append("no trailer")
    elif b"/Root" not in trailer.group(1):
        errors.append("trailer missing /Root")
    return errors


def geometry_lines(stream_text: str) -> list:
    """The graphics-state and geometry lines, with text and the footer bar folded out."""
    keep = []
    bar_seen = False
    for line in stream_text.splitlines():
        if line.startswith("BT"):
            continue
        if line in ("S", "f"):
            keep.append(line)
        elif re.match(rf"^{NUM} {NUM} m {NUM} {NUM} l S$", line):
            bar_seen = True
        elif re.match(rf"^{NUM} {NUM} m( {NUM} {NUM} l)*$", line):
            keep.append(line)
        elif (line.endswith(" cm") or line.endswith(" RG")
              or line.endswith(" w") or line.endswith(" rg")):
            keep.append(line)
        elif line in ("1 J 1 j", "[] 0 d") or line.startswith("[2 2] 0 d"):
            keep.append(line)
    if bar_seen:
        while "0 0 0 RG 0.3 w" in keep:
            keep.remove("0 0 0 RG 0.3 w")
    return keep


def long_axis_angle(polys) -> float:
    """Angle of the shape's long axis in page mm: 0 = horizontal, 90 = vertical."""
    return gen.min_width_angle([p for poly in polys for p in poly])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--aggregate", type=Path, default=gen.DEFAULT_SRC)
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-page-height", type=float, default=gen.MAX_PAGE_HEIGHT_MM,
                    metavar="MM")
    ap.add_argument("--small-page-height", type=float,
                    default=gen.SMALL_PAGE_HEIGHT_MM, metavar="MM",
                    help="the cap the small coverts' pages were built to; 0 lifts it")
    ap.add_argument("--pair-orientation", choices=("auto", "upright", "headless"),
                    default="auto")
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--page-width", type=float, default=None, metavar="MM",
                    help="nominal logical page width the build used (default "
                         f"{gen.PAGE_WIDTH_MM:g} mm); a build that widened its "
                         "pages settles the same way the generator does")
    args = ap.parse_args()

    if args.spacing is not None:
        gen.DENSE_GAP_MM = args.spacing
    small_page_h = args.small_page_height or None

    data = args.pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise SystemExit("not a PDF")
    objects = parse_objects(data)
    errors = check_xref(data, objects)

    feathers = gen.load_aggregate_feathers(args.aggregate, args.only)
    mode = args.pair_orientation
    # The generator widens the page when a pair needs more, so the verifier has to
    # settle the same width or it would rebuild a layout the file was not made from.
    nominal = gen.PAGE_WIDTH_MM if args.page_width is None else args.page_width
    gen.PAGE_WIDTH_MM, width_note = gen.settle_page_width(feathers, args.scale,
                                                          mode, nominal)
    if width_note:
        print(f"  page width {width_note}")
    planned = gen.plan_pages(feathers, args.scale, args.max_page_height,
                             args.max_rows, mode, small_page_h)
    layouts = [gen.layout_page(group, rows, by_name, args.scale, mode)
               for group, rows, by_name in planned]

    pages = [(num, body) for num, body in sorted(objects.items())
             if b"/Type /Page" in body and b"/Type /Pages" not in body]
    print(f"{args.pdf.name}: {len(data) / 1024:.1f} KiB, {len(objects)} objects, "
          f"{len(pages)} page object(s)")
    print(f"  {len(feathers)} feathers from {args.aggregate.name} planned onto "
          f"{len(layouts)} logical page(s), --pair-orientation {mode}")
    if len(pages) != len(layouts):
        errors.append(f"page count {len(pages)} != planned {len(layouts)}")

    # every feather must be standing on its own long axis before layout. The angle
    # is measured by the width-minimising rotation, whose zero is one of the two
    # ends of the axis, so 0 and 180 both mean "vertical".
    for feather in feathers:
        angle = long_axis_angle(feather.polys_right) % 180.0
        off = min(angle, abs(angle - 180.0))
        if off > UPRIGHT_TOL_DEG:
            errors.append(
                f"{feather.name}: long axis sits {off:.2f} deg off vertical "
                f"(angle {angle:.2f} deg)")

    total_vertices = 0
    for index, ((page_num, body), layout) in enumerate(zip(pages, layouts), start=1):
        mb = re.search(rb"/MediaBox \[([^\]]+)\]", body)
        if not mb:
            errors.append(f"page {index}: no MediaBox")
            continue
        vals = [float(v) for v in mb.group(1).split()]
        w_mm, h_mm = vals[2] / gen.PT_PER_MM, vals[3] / gen.PT_PER_MM
        if abs(w_mm - layout.page_w) > 5e-3 or abs(h_mm - layout.page_h) > 5e-3:
            errors.append(f"page {index}: MediaBox {w_mm:.3f}x{h_mm:.3f} "
                          f"!= layout {layout.page_w:.3f}x{layout.page_h:.3f}")
        if w_mm > gen.PAGE_WIDTH_MM + 5e-3:
            errors.append(f"page {index}: {w_mm:.2f} mm is over the "
                          f"{gen.PAGE_WIDTH_MM:.0f} mm width limit")

        cref = re.search(rb"/Contents (\d+) 0 R", body)
        if not cref:
            errors.append(f"page {index}: no /Contents")
            continue
        content_obj = objects.get(int(cref.group(1)))
        if content_obj is None or b"/FlateDecode" not in content_obj:
            errors.append(f"page {index}: content object missing or uncompressed spec")
            continue
        stream = extract_stream(content_obj)
        if stream is None:
            errors.append(f"page {index}: content stream not found or /Length wrong")
            continue
        try:
            text = zlib.decompress(stream).decode("ascii")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"page {index}: cannot decompress content ({exc})")
            continue

        expected = geometry_lines(gen.compute_layout_geometry(layout))
        got = geometry_lines(text)
        if expected != got:
            for i, (a, b) in enumerate(zip(expected, got)):
                if a != b:
                    errors.append(
                        f"page {index}: geometry stream differs at line {i + 1}\n"
                        f"      expected {a[:100]}\n      got      {b[:100]}")
                    break
            else:
                errors.append(
                    f"page {index}: geometry stream length differs "
                    f"({len(expected)} vs {len(got)} lines)")

        for slot in layout.slots:
            as_drawn = gen.transform_polys(slot.feather.polys_right, slot.right_to_page)
            mirrored = gen.transform_polys(slot.feather.polys_right, slot.left_to_page)
            total_vertices += sum(len(p) for p in as_drawn) + sum(len(p) for p in mirrored)
            want_gap = slot.gap_mm

            if not slot.headless:
                if min(x for poly in as_drawn for x, _ in poly) < slot.axis_x - 1e-6:
                    errors.append(
                        f"page {index} {slot.name}: as-drawn half is left of its axis")
                if max(x for poly in mirrored for x, _ in poly) > slot.axis_x + 1e-6:
                    errors.append(
                        f"page {index} {slot.name}: mirrored half is right of its axis")
                got_gap = min(x for poly in as_drawn for x, _ in poly) - \
                    max(x for poly in mirrored for x, _ in poly)
                reflected = [[(2 * slot.axis_x - x, y) for x, y in poly]
                             for poly in as_drawn]
            else:
                if max(y for poly in as_drawn for _, y in poly) > slot.axis_y + 1e-6:
                    errors.append(
                        f"page {index} {slot.name}: as-drawn half is above its axis")
                if min(y for poly in mirrored for _, y in poly) < slot.axis_y - 1e-6:
                    errors.append(
                        f"page {index} {slot.name}: mirrored half is below its axis")
                got_gap = min(y for poly in mirrored for _, y in poly) - \
                    max(y for poly in as_drawn for _, y in poly)
                reflected = [[(x, 2 * slot.axis_y - y) for x, y in poly]
                             for poly in as_drawn]

            if got_gap < want_gap - 1e-6:
                errors.append(
                    f"page {index} {slot.name}: the halves are {got_gap:.2f} mm apart, "
                    f"need {want_gap:.2f} mm")
            err = max(
                max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                for p, q in zip(reflected, mirrored)
                for a, b in zip(p, q)
            )
            if err > 1e-9:
                errors.append(
                    f"page {index} {slot.name}: halves are not mirror images "
                    f"(max vertex delta {err:.6f} mm)")

            # nothing may escape the page
            for half, polys in (("as-drawn", as_drawn), ("mirrored", mirrored)):
                half_stroke = slot.feather.stroke_mm * args.scale / 2.0 * args.scale
                xs = [x for poly in polys for x, _ in poly]
                ys = [y for poly in polys for _, y in poly]
                if (min(xs) - half_stroke < -0.05
                        or max(xs) + half_stroke > layout.page_w + 0.05
                        or min(ys) - half_stroke < -0.05
                        or max(ys) + half_stroke > layout.page_h + 0.05):
                    errors.append(
                        f"page {index} {slot.name}: the {half} half escapes the page")

            # the feather must read vertical in page space. The angle comes back as
            # 0 or 180 when the long axis is vertical, and 90 or 270 when the pair is
            # headless and the feather's long axis runs across the page.
            angle = long_axis_angle(as_drawn) % 180.0
            if slot.headless:
                off = min(abs(angle - 90.0), abs(angle - 90.0))
            else:
                off = min(angle, abs(angle - 180.0))
            if off > UPRIGHT_TOL_DEG:
                errors.append(
                    f"page {index} {slot.name}: "
                    f"{'headless' if slot.headless else 'upright'} half's long axis "
                    f"sits {off:.2f} deg off "
                    f"{'horizontal' if slot.headless else 'vertical'}")

        # clear spacing between neighbouring pairs
        want = gen.DENSE_GAP_MM
        slots = layout.slots
        for i, a in enumerate(slots):
            for b in slots[i + 1:]:
                gap_x = max(a.cell_left - b.cell_right, b.cell_left - a.cell_right)
                gap_y = max(a.pair_bottom - b.pair_top, b.pair_bottom - a.pair_top)
                if gap_x >= 0 and gap_y >= 0:
                    continue
                gap = gap_y if gap_x < 0 else gap_x
                if gap < want - 1e-6:
                    errors.append(
                        f"page {index}: {a.name}/{b.name} spacing {gap:.2f} mm "
                        f"is under {want:.2f} mm")

    print(f"  verified {total_vertices} cut-line vertices across {len(layouts)} pages")
    print()
    if errors:
        print(f"FAILURES ({len(errors)}):")
        for e in errors[:40]:
            print("  " + e)
        return 1
    print("PDF structure, page sizes, emitted geometry, mirroring, spacing, page fit "
          "and vertical feather axes all verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
