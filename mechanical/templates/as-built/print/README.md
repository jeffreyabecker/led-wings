# As-built feather templates

Printable cutting templates derived from the measured feather outlines of the
built wing. The source of truth is `vectors/individuals/*.svg`: one file per
feather, authored so that **one user unit equals one millimetre**, with the
geometry already placed by the calibration matrix that was fitted to the
photographed grid (`outlines/calibration.json`).

The feather set is the **right-hand (as built)** side. The left wing is the
side-to-side mirror of it.

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

## Regenerating

```sh
python tools/make_feather_template_pdf.py                      # the 14-page document
python tools/make_feather_template_pdf.py --list               # page plan, no output
python tools/make_feather_template_pdf.py --only P1 B5 LC1     # a subset
python tools/make_feather_template_pdf.py --spacing 50         # wider gap within a row
python tools/make_feather_template_pdf.py --max-page-height 900 # shorter pages, more of them
python tools/make_feather_template_pdf.py --scale 0.5 --out half.pdf
```

`tools/feather_geometry.py` holds the SVG parsing (path data, transform
composition, curve flattening) and is shared by the generator and the verifiers.

## Verification

The generated file is checked by four independent passes:

| script | what it establishes |
| --- | --- |
| `_check_feather_geometry.py` | parsed outlines match each SVG's declared page size |
| `_verify_mirror_layout.py` | placement, handedness, exact mirroring, the half-to-half gap, pair spacing and page fit (rasterised by Chrome) |
| `_verify_pdf_contents.py` | PDF objects, xref, MediaBoxes, and the emitted geometry stream rebuilt from the layout and compared line for line |
| `_verify_pdf_pypdf.py` | independent parse (pypdf) of pages, boxes and text layer |
| `_verify_pdf_render.py` | independent render (PDFium) of the printed result, incl. label sides read back from the glyph boxes |

All pass for all 16 pages / 42 pairs. All take `--only`, `--scale`, `--spacing`, `--max-rows` and `--max-page-height`
to match a non-default build.
