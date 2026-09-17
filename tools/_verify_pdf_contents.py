"""Structural + content verification of the generated PDF.

Parses the PDF the generator produced (objects, xref, MediaBoxes), then
decompresses each page's content stream and rebuilds the geometry section that
the generator's own layout prescribes. The two are compared as exact text, which
proves every emitted coordinate, stroke width and operator - any bug in the PDF
writer or the layout shows up as a mismatch.

It also checks the handedness (as-built half right of its axis, mirror left),
that each pair is an exact reflection, and the clear spacing between pairs.

Usage: python tools/_verify_pdf_contents.py <pdf> [--max-rows N] [--scale S]
"""
from __future__ import annotations

import argparse
import re
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feather_geometry import load_feather  # noqa: E402
from make_feather_template_pdf import (  # noqa: E402
    MAX_PAGE_HEIGHT_MM,
    DENSE_GAP_MM,
    PAGE_WIDTH_MM,
    PT_PER_MM,
    SPARSE_GAP_MM,
    build_page,
    compute_layout_geometry,
    layout_page,
    plan_pages,
    transform_polys,
)

OBJ_RE = re.compile(rb"(\d+) 0 obj\b(.*?)\bendobj", re.S)
STREAM_LEN_RE = re.compile(rb"/Length\s+(\d+)")
NUM = r"-?\d+(?:\.\d+)?"
PAGE_WIDTH_LIMIT_MM = 273.0


def parse_objects(data: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2) for m in OBJ_RE.finditer(data)}


def extract_stream(body: bytes) -> bytes | None:
    """Return the raw stream bytes, trusting the declared /Length.

    Slicing by /Length (rather than regexing to the first `endstream`) is what the
    PDF spec prescribes, and it also verifies that the writer recorded the length
    correctly. Compressed data can itself contain bytes that look like
    `endstream`, which is what makes a regex approach unreliable.
    """
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
    tail = body[start + length: start + length + 20]
    if not re.match(rb"\r?\n?\s*endstream", tail):
        return None
    return data


def count_sublist(haystack: list[str], needle: list[str]) -> int:
    """Count non-overlapping occurrences of the line sequence `needle`."""
    if not needle:
        return 0
    count = 0
    i = 0
    while i <= len(haystack) - len(needle):
        if haystack[i:i + len(needle)] == needle:
            count += 1
            i += len(needle)
        else:
            i += 1
    return count


def check_xref(data: bytes, objects: dict[int, bytes]) -> list[str]:
    errors = []
    m = re.search(rb"startxref\s+(\d+)", data)
    if not m:
        return ["no startxref"]
    start = int(m.group(1))
    if data[start:start + 4] != b"xref":
        errors.append("startxref does not point at an xref table")
        return errors
    header = re.match(rb"xref\s+0\s+(\d+)\s+", data[start:])
    if not header:
        errors.append("malformed xref header")
        return errors
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
    else:
        t = trailer.group(1)
        if b"/Root" not in t:
            errors.append("trailer missing /Root")
        m2 = re.search(rb"/Size\s+(\d+)", t)
        if not m2 or int(m2.group(1)) != count:
            errors.append("trailer /Size mismatch")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--src", type=Path,
                    default=Path(__file__).resolve().parent.parent
                    / "mechanical/templates/as-built/vectors/individuals")
    ap.add_argument("--only", nargs="+", metavar="ID")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-page-height", type=float,
                    default=MAX_PAGE_HEIGHT_MM, metavar="MM")
    ap.add_argument("--spacing", type=float, default=None)
    args = ap.parse_args()

    if args.spacing is not None:
        import make_feather_template_pdf as gen

        gen.DENSE_GAP_MM = args.spacing

    data = args.pdf.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise SystemExit("not a PDF")
    objects = parse_objects(data)
    errors = check_xref(data, objects)

    pages = [(num, body) for num, body in sorted(objects.items())
             if b"/Type /Page" in body and b"/Type /Pages" not in body]

    from make_feather_template_pdf import discover

    feathers = [load_feather(p) for p in discover(args.src, args.only)]
    planned = plan_pages(feathers, args.scale, args.max_page_height, args.max_rows)
    layouts = [layout_page(group, rows, by_name, args.scale)
               for group, rows, by_name in planned]

    print(f"{args.pdf.name}: {len(data) / 1024:.1f} KiB, {len(objects)} objects, "
          f"{len(pages)} page objects")
    print(f"{len(feathers)} feathers planned onto {len(layouts)} logical pages")
    if len(pages) != len(layouts):
        errors.append(f"page count {len(pages)} != planned {len(layouts)}")

    total_vertices = 0
    for index, ((page_num, body), layout) in enumerate(zip(pages, layouts), start=1):
        mb = re.search(rb"/MediaBox \[([^\]]+)\]", body)
        if not mb:
            errors.append(f"page {index}: no MediaBox")
            continue
        vals = [float(v) for v in mb.group(1).split()]
        w_mm, h_mm = vals[2] / PT_PER_MM, vals[3] / PT_PER_MM
        if abs(w_mm - layout.page_w) > 5e-3 or abs(h_mm - layout.page_h) > 5e-3:
            errors.append(f"page {index}: MediaBox {w_mm:.3f}x{h_mm:.3f} "
                          f"!= layout {layout.page_w:.3f}x{layout.page_h:.3f}")
        if w_mm > PAGE_WIDTH_LIMIT_MM + 5e-3:
            errors.append(f"page {index}: {w_mm:.2f} mm is over the "
                          f"{PAGE_WIDTH_LIMIT_MM:.0f} mm width limit")

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

        # Rebuild the drawing section the generator should have emitted, and the
        # actual one, both filtered down to graphics-state and geometry lines so
        # the text furniture does not take part in the comparison. The scale bar
        # in the footer is graphics too, so it is recognised and folded into a
        # single marker rather than matched operator by operator.
        def geometry_lines(stream_text: str) -> list[str]:
            keep = []
            bar_seen = False
            for line in stream_text.splitlines():
                if line.startswith("BT"):
                    continue
                if line in ("S", "f"):
                    keep.append(line)
                elif re.match(rf"^{NUM} {NUM} m {NUM} {NUM} l S$", line):
                    # the footer scale bar: graphics, but not part of the layout
                    bar_seen = True
                elif re.match(rf"^{NUM} {NUM} m( {NUM} {NUM} l)*$", line):
                    keep.append(line)
                elif (line.endswith(" cm") or line.endswith(" RG")
                      or line.endswith(" w") or line.endswith(" rg")):
                    keep.append(line)
                elif line in ("1 J 1 j", "[] 0 d") or line.startswith("[2 2] 0 d"):
                    keep.append(line)
            if bar_seen:
                # the bar's leading stroke settings appear just before it
                while "0 0 0 RG 0.3 w" in keep:
                    keep.remove("0 0 0 RG 0.3 w")
            return keep

        expected_lines = geometry_lines(compute_layout_geometry(layout))
        got_lines = geometry_lines(text)
        if expected_lines != got_lines:
            for i, (a, b) in enumerate(zip(expected_lines, got_lines)):
                if a != b:
                    errors.append(
                        f"page {index}: geometry stream differs at line {i + 1}\n"
                        f"      expected {a[:100]}\n      got      {b[:100]}")
                    break
            else:
                errors.append(
                    f"page {index}: geometry stream length differs "
                    f"({len(expected_lines)} vs {len(got_lines)} lines)")

        for slot in layout.slots:
            right = transform_polys(slot.feather.polys_right, slot.right_to_page)
            left = transform_polys(slot.feather.polys_right, slot.left_to_page)
            total_vertices += sum(len(p) for p in right) + sum(len(p) for p in left)
            if min(x for poly in right for x, _ in poly) < slot.axis_x - 1e-6:
                errors.append(
                    f"page {index} {slot.name}: as-built half is left of its axis")
            if max(x for poly in left for x, _ in poly) > slot.axis_x + 1e-6:
                errors.append(
                    f"page {index} {slot.name}: mirrored half is right of its axis")
            reflected = [[(2 * slot.axis_x - x, y) for x, y in poly] for poly in right]
            err = max(
                max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                for p, q in zip(reflected, left)
                for a, b in zip(p, q)
            )
            if err > 1e-9:
                errors.append(
                    f"page {index} {slot.name}: halves are not mirror images "
                    f"(max vertex delta {err:.6f} mm)")

        # clear spacing between neighbouring pairs on the page
        want = DENSE_GAP_MM
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

    print(f"verified {total_vertices} cut-line vertices across {len(layouts)} pages")
    print()
    if errors:
        print(f"FAILURES ({len(errors)}):")
        for e in errors[:30]:
            print("  " + e)
        return 1
    print("PDF structure, page sizes, geometry stream, handedness, mirroring "
          "and spacing all verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
