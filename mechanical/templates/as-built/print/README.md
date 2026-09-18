# As-built feather templates

Printable cutting templates derived from the measured feather outlines of the
built wing. The source of truth is `vectors/individuals/*.svg`: one file per
feather, authored so that **one user unit equals one millimetre**, with the
geometry already placed by the calibration matrix that was fitted to the
photographed grid (`outlines/calibration.json`).

The feather set is the **right-hand (as built)** side. The left wing is the
side-to-side mirror of it.

Two documents are generated from that one source. They differ only in how the
small feathers are laid out; the P, S and B groups are identical in both.

| file | pages | small-feather pages | for |
| --- | --- | --- | --- |
| `feathers-mirrored-pairs.pdf` | 16 | 707-938 mm tall | roll / large-format printer, fewest sheets |
| `feathers-200mm-rotated.pdf` | 37 | **all 200 mm or less** (20 pages) | anything a home printer takes, tiled |

## Printing: use Acrobat's poster mode

Neither document is meant to come out on one sheet. Print both through
**Acrobat Reader -> Print -> Page Sizing & Handling -> Poster**, which tiles each
logical page across as many sheets as the paper needs and joins them with an
overlap you trim to. The page sizes here are *logical*; the paper in the printer
is what tiling takes care of.

Settings that matter:

* **Tile Scale 100%** - the templates are true size and any other value loses
  that. Check the 50 mm bar at the foot of a page once the tiles are joined.
* **Overlap** - Acrobat defaults to 0.5 in (12.7 mm). Every page keeps at least
  **5.6 mm of clear margin on all four edges**, so the default works and a
  smaller overlap will not clip anything: every feather outline and both ID
  labels sit well inside that margin. Only the title, subtitle and footer text
  come near it, and those are labels rather than cut lines.
* **Cut Marks** - optional; the overlap is enough to register tiles by eye.
* **Labels** - leave on, so each sheet is stamped with its logical page number.

A 273 x 938 mm logical page tiles into roughly 2 x 6 sheets of A4 landscape. The
16-page document needs about 150 A4 sheets in total, the 37-page one about 190 -
so the 200 mm document's advantage is not paper, it is that it prints at all on a
printer that refuses the taller sheets.

## `print/feathers-mirrored-pairs.pdf`

16 logical pages holding all 42 feather pairs. Each pair is the as-built feather
plus its mirror placed side-to-side, so one page yields both templates.

The halves are laid out the way the wings sit on the bird: the **as-built
(right) feather on the right** of the pair's centre line, its **mirror (left
feather) on the left**. The labels name them, not the page position.

The two halves of a pair are held apart across the centre line, so the
mirror-image outline is never sitting on the cut edge you are working on:

* **70 mm** between the halves of a P or S pair (the long primaries and secondaries)
* **30 mm** between the halves of every other pair, and between neighbouring pairs

Each pair also carries its own identification, so a loose template can always be
traced:

* above each half, the feather ID with its side: `P1 L`, `P1 R`, `SC4 L`, `SC4 R`, ...
  - the `L` / `R` suffix is what distinguishes the two halves, so there is no
  separate side caption
* the page footer lists every pair on the sheet

Other properties:

* printed at **1:1** - measure the 50 mm bar at the foot of any page before cutting
* every page is **273 mm wide**; heights run from 395 mm to 929 mm
* cut lines are the calibrated outlines at 0.5 mm stroke; the grey/white fills
  only exist so the cut line stands out
* a thin dashed tick marks each pair's mirror axis above and below it
* the header names the group

### Why some pairs get a page or a row to themselves

A pair is now two half-widths plus its own 70 mm or 30 mm gap, and the big
feathers are wide: P1's pair is 259 mm and S1's is 244 mm, against 263 mm of
usable width once the margins shrink to 5 mm. With 30 mm also required beside a
neighbour there is no room for a second pair, so each P gets a page and each S
pair gets a row.

| page | content | page size |
| --- | --- | --- |
| 1-6 | P1 ... P6, one pair per page | 273 x 395-558 mm |
| 7-9 | S2+S1, S4+S3, S6+S5 | 273 x 828 / 742 / 611 mm |
| 10 | B1 + B2 | 273 x 719 mm |
| 11 | B3 + B4 + B5 | 273 x 826 mm |
| 12-13 | SC1-8 | 273 x 888 / 929 mm |
| 14 | PC1-3 | 273 x 700 mm |
| 15 | A1-4 | 273 x 834 mm |
| 16 | MC1-5 and LC1-5 | 273 x 728 mm |

Feathers are ordered inner primary outwards:
`P1-6`, `S1-6`, `B1-5`, `SC1-8`, `PC1-3`, `A1-4`, `MC1-5`, `LC1-5`.

Pages are packed to `MAX_PAGE_HEIGHT_MM` (1050 mm), divided as evenly as possible
between a group's pages. With the wide pair gaps the groups make more rows than
the budget alone would allow, so 1050 mm is not reached in practice.

`--max-rows 1` gives one pair per page. `--spacing 50` widens the gap between
pairs sharing a row. `--scale` shrinks the drawing to a stated reduced scale (the
footer then says so instead of printing a 50 mm bar); `--only` regenerates a
subset to test the fit.

## `print/feathers-200mm-rotated.pdf`

37 pages, of which the **20 that hold SC, PC, A, MC and LC are all 200 mm or
less** (133-194 mm). P, S and B keep the larger pages they need, up to 567 mm.

Under 200 mm those pages tile into a single row of sheets rather than a grid,
which is what makes them work on a printer with a short maximum sheet length.

To get the tall small-feather pairs onto a 200 mm sheet, the SC, PC and A pairs
are laid down **rotated 90 degrees clockwise** — the feather's long axis runs
across the page. Rotation swaps a pair's extents, so a pair that was 169.7 mm
tall by 145.5 mm wide becomes 145.5 mm tall by 169.7 mm wide, and fits.

The halves are then stacked rather than side-by-side: the **as-built (right)
feather below the pair's centre line**, its **mirror above it**, with the same
clear gap between them. The ID labels sit at the ends of the pair, so `SC3 L` is
still the mirror and `SC3 R` the as-built piece.

* 42 pairs across 37 pages; P/S/B pages are the same as the other document
* rotating is the only lever that works here: the non-fitters are too tall as
  *single* pairs, so closing up the spacing cannot help them
* each rotated pair is wider than half the page, so it takes a sheet to itself
* the price is sheet count — 37 pages against 16

```sh
python tools/make_feather_template_pdf.py --max-page-height 200 --rotate SC PC A \
    --out mechanical/templates/as-built/print/feathers-200mm-rotated.pdf
```

## Regenerating

```sh
python tools/make_feather_template_pdf.py                      # the 16-page document
python tools/make_feather_template_pdf.py --list               # page plan, no output
python tools/make_feather_template_pdf.py --only P1 B5 LC1     # a subset
python tools/make_feather_template_pdf.py --spacing 50         # wider gap within a row
python tools/make_feather_template_pdf.py --max-page-height 900 # shorter pages, more of them
python tools/make_feather_template_pdf.py --scale 0.5 --out half.pdf
```

`--rotate FAMILY ...` lays those families' pairs down a quarter turn clockwise.
It is what the 200 mm document uses; the default is to rotate nothing.

Builds are reproducible: set `SOURCE_DATE_EPOCH` and both the PDF's CreationDate
and the date in each footer are taken from it, so a rebuild is byte-identical and
a diff means the content really changed.

```sh
SOURCE_DATE_EPOCH=$(date +%s) python tools/make_feather_template_pdf.py
```

`tools/feather_geometry.py` holds the SVG parsing (path data, transform
composition, curve flattening) and is shared by the generator and the verifiers.

## Verification

The generated file is checked by four independent passes:

| script | what it establishes |
| --- | --- |
| `_check_feather_geometry.py` | parsed outlines match each SVG's declared page size |
| `_verify_mirror_layout.py` | placement, handedness, exact mirroring, the half-to-half gap, pair spacing and page fit, in either orientation (rasterised by Chrome) |
| `_verify_pdf_contents.py` | PDF objects, xref, MediaBoxes, and the emitted geometry stream rebuilt from the layout and compared line for line |
| `_verify_pdf_pypdf.py` | independent parse (pypdf) of pages, boxes and text layer |
| `_verify_pdf_render.py` | independent render (PDFium) of the printed result, incl. label sides read back from the glyph boxes |

All pass for both documents (16 and 37 pages, 42 pairs each). All take `--only`, `--scale`, `--spacing`, `--max-rows` and `--max-page-height`
to match a non-default build.
