# Plan — split `pages_to_pdf.py` into sheet building and PDF assembly

**Status: proposal.** Nothing is changed yet. `pages_to_pdf.py` is as committed
in `d0cf1eb` through `0ec54a7`; `make_logical_pages.py` is untouched by this plan.

**Scope:** `pages_to_pdf.py` only, plus the two files it becomes and the
documentation that names them. `make_logical_pages.py` keeps owning
`logical-pages/page-NNN.svg` exactly as it does now.

**The ask:** (1) a script that lays the logical pages out onto SVGs targeting a
particular print page size; (2) a script that renders a set of SVGs to PDF and
concatenates them.

**Verdict:** the seam is already there. `pages_to_pdf.py` renders nothing until
`render_sheets()` (line 234) and computes nothing after it; the only real cost is
deciding where the two checks live and stopping the two halves from each
delete-then-rewrite `print/sheets/`.

## 1. What the current script does

`pages_to_pdf.py`, 374 lines, in the order it runs:

| stage | lines | what it owns |
|---|---|---|
| constants | 56–70 | `PAPER_W/H`, `MARGIN`, `OVERLAP`, `FIT_SLACK`, and the derived `pw`, `ph`, `stride_x`, `stride_y` |
| read | 122–159 | `read_page()` — pulls title, W, H, CSS and content out of a page SVG by string slicing |
| fit/tile | 193–227 | `build_sheets()` — the single-sheet fast path, or the cols x rows grid with a clip path, corner ticks and a tile note |
| render | 234–254 | writes `sheets/sheet-NNN.svg`, `cairosvg.svg2pdf`s each, merges with `pypdf` into `feathers-letter-landscape.pdf` |
| thumbnails | 257–272 | `contact-sheet.png` from the merged PDF |
| verify | 279–328 | `verify_tiling()` (re-derive the grid and each transform) and `verify_scale()` (rasterise the cover, measure both calibration bars) |
| driver | 335–370 | reads pages, builds sheets, verifies, renders, writes the contact sheet, prints the summary |

Two couplings worth naming before touching anything:

- **`verify_tiling()` is the only thing that checks the arithmetic in
  `build_sheets()`.** It re-derives `cols`, `rows` and every tile transform from
  the paper constants and the emitted sheet. If the split puts those in different
  scripts, the self-check is orphaned and the tiling goes unverified.
- **`verify_scale()` measures the *cover*, and knows how to find it.** It assumes
  the cover is logical page 1 and that a page that fits is placed at
  `(MARGIN, MARGIN)`, so the bars drawn at page coords `(40, 70)` and `(40, 115)`
  land at `+MARGIN`. That assumption is about *layout*, which Script 1 owns, and
  it is checked in script 2 by rasterising the output.

## 2. The split

| | Script 1 — `make_print_sheets.py` | Script 2 — `sheets_to_pdf.py` |
|---|---|---|
| reads | `logical-pages/page-*.svg` | `sheets/sheet-*.svg` |
| writes | `sheets/sheet-NNN.svg` | `sheets/sheet-NNN.pdf`, `feathers-letter-landscape.pdf`, `contact-sheet.png` |
| owns | paper size, margins, overlap, fit slack, the fit/tile decision, clip, ticks, tile notes | rasterisation, merge order, thumbnails |
| checks | tiling (re-derived from its own constants); that its output is one SVG per record; that every sheet is exactly the paper size | every named SVG exists, is the paper size, and appears in the merged PDF in filename order; the scale bars |
| needs to know | nothing about the pages beyond what `read_page()` extracts | nothing about tiling or paper geometry |

The interface is a directory of same-size SVGs plus a manifest. Script 2 does not
need to know what a tile is, and Script 1 does not need cairosvg or pypdf.

### 2a. Paper size

Today the size is four module constants. The ask is "targeting a specific print
page size", so Script 1 takes it as parameters with today's Letter-landscape
values as the defaults:

```
--paper WxH     279.4x215.9   sheet size in mm
--margin MM     5.0           unprintable border
--overlap MM    12.0          printed twice on adjacent tiles
--slack MM      2.0           overshoot that still gets one sheet
```

`pw`, `ph`, `stride_x`, `stride_y` stay *derived*, never passed, so a caller
cannot hand in a combination the tiling formula disagrees with — which is exactly
the drift `verify_tiling()` exists to catch. A4 landscape
(`297x210`) is the obvious second value and belongs in a test, not a default.

### 2b. The manifest

Script 2 needs one thing it cannot re-derive: which sheet carries the cover's
calibration bars, and with what offset. Script 1 writes
`sheets/manifest.json`:

```json
{
  "paper": {"w": 279.4, "h": 215.9}, "margin": 5.0,
  "stride": {"x": 257.4, "y": 193.9},
  "sheets": [
    {"file": "sheet-001.svg", "page": "page-001.svg", "title": "cover",
     "tile": 1, "cols": 1, "rows": 1, "transform": "translate(5 5)"}
  ]
}
```

Everything in it is already computed by `build_sheets()`; the manifest only
records it. It is also what makes Script 2's own check possible — "every sheet in
the manifest is present, is the paper size, and was merged in order" — and it
retires the `verify_scale()` assumption above, because the cover's offset comes
from the manifest rather than from a hardcoded `MARGIN`.

Rejected: having Script 2 read each sheet's `<text class="note">` tile label. It
works, but it makes the renderer parse a human-readable caption to recover
machine state, and the note is not emitted at all for the single-sheet fast path.

### 2c. Verification, split

| check | goes to | why |
|---|---|---|
| tiling re-derivation | Script 1 | it is arithmetic about tiling; the constants live here |
| each emitted sheet is the paper size, one per tile | Script 1 | same reason |
| every manifest SVG exists and is paper-sized | Script 2 | it is the renderer's input contract |
| merged PDF page count == sheet count, in order | Script 2 | it is the renderer's output contract |
| calibration bars measure 100 mm / 101.6 mm | Script 2 | it needs a rasterised sheet, which is Script 2's job |
| contact sheet | Script 2 | already there |

The scale check itself does not change: same 300 dpi render, same two bar probes,
same ±1 mm tolerance. Only its *input* changes — it measures the sheet named in
the manifest instead of `doc[0]`. That is a strict improvement: `doc[0]` was
right only while the cover stayed logical page 1 and fitted untitled.

## 3. What must not move

The emitted sheet SVGs are the contract between the halves and the record of the
tiling. Splitting the script must not change a single byte of them.

- `read_page()`, `build_sheets()`, `sheet_svg()`, `corner_ticks()`, `CLIP_DEF`,
  `CSS2`, and every derived constant move to Script 1 **unchanged**.
- `render_sheets()`'s render loop, `contact_sheet()`, and `OUT_PDF` move to
  Script 2 **unchanged**.
- `logical-pages/page-*.svg` and `feathers-letter-landscape.pdf` keep their paths.
- `sheets/` keeps its path, so the existing `.gitignore` entries for `sheets/` and
  `contact-sheet.png` still cover the intermediates.

## 4. Hazards

| hazard | containment |
|---|---|
| the two scripts each clear `sheets/` and delete the other's output | Script 1 unlinks only `sheet-*.svg` (plus its own `manifest.json`); Script 2 unlinks only `sheet-*.pdf`. Today's `render_sheets()` clears **both** — splitting that loop is the one edit that must not be a copy/paste |
| Script 2 silently renders a stale sheet set | Script 1 rewrites every `sheet-*.svg` and the manifest in one run; Script 2 asserts the PDF page count equals the manifest length. A stale `.pdf` next to a fresh `.svg` cannot survive the count check |
| the scale check loses its fixed reference point | the manifest carries the cover's sheet and offset (§2b) |
| a paper-size flag combination the formula disagrees with | keep `pw`/`ph`/`stride` derived; `verify_tiling()` re-derives from the same numbers Script 1 used |
| the split changes sheet bytes | Script 1 must produce byte-identical `sheet-*.svg` for the default Letter arguments; capture hashes before the split and compare after |
| someone runs the old name | delete `pages_to_pdf.py` in the same commit; there is no README to redirect, so the module docstring is the only place a stale command could linger |

## 5. Acceptance test

Baseline first (step 0): run the current `pages_to_pdf.py`, hash every
`sheets/sheet-*.svg`, hash `feathers-letter-landscape.pdf`, and record the tile
grid and sheet count it prints.

1. `make_print_sheets.py` with default arguments emits the **same sheet count**
   and **byte-identical** `sheet-*.svg` files to the baseline;
2. `sheets_to_pdf.py` produces a `feathers-letter-landscape.pdf` whose page count
   equals the sheet count and whose pages match the baseline's page-for-page
   (compare extracted page sizes; the rendered bytes may differ harmlessly if
   cairosvg's metadata is nondeterministic, so state which it is);
3. both scripts pass their own checks and print them;
4. `make_print_sheets.py --paper 297x210` runs and produces sheets 297x210 mm
   with a **larger** sheet count than Letter for the same pages — a second paper
   size is the whole point of the flag, and this is the cheap proof it is wired
   through rather than accepted and ignored;
5. `grep -r pages_to_pdf` returns only the historical plan docs;
6. neither script writes into the other's file set: after Script 2 runs, every
   `sheet-*.svg` from Script 1 is still present and unmodified.

## 6. Risks

| risk | containment |
|---|---|
| splitting orphans the tiling self-check | §2c puts it with the constants it checks; step 3 requires Script 1 to print it |
| the scale check becomes vacuous (passes because it measured nothing) | `verify_scale()` already returns `None` on no ink and `main()` fails on `None`; keep that, and assert the manifest named a cover sheet |
| the manifest drifts from the sheets | it is written in the same loop that emits them, and Script 2 asserts the sheet list matches |
| a second paper size silently keeps Letter geometry | step 4 checks the sheet *size*, not just that the run exits 0 |
| `contact-sheet.png` layout assumes a page count | `contact_sheet()` already takes `n_pages` and derives rows; unchanged |

## 7. Open questions

1. **Names.** `make_print_sheets.py` / `sheets_to_pdf.py` above. Alternatives:
   `pages_to_sheets.py` / `sheets_to_pdf.py` (mirrors the existing
   `make_logical_pages.py` / `pages_to_pdf.py` pairing), or keep the first as
   `pages_to_pdf.py` and add a rendering flag. Proposal: the pair above, because
   "print sheets" says what the output is.
2. **Paper size as flags or as a config constant?** Flags make a second size
   reachable without editing the script; constants keep one blessed geometry and
   make the drift impossible. Proposal: flags, defaults unchanged, because the
   ask was explicitly to target a size.
3. **Should Script 1 also emit a page-size summary (mm of paper used, tiles per
   page) for the README that does not exist yet?** Proposal: not now.
4. **Does Script 2 need a `--dpi` or render-quality knob?** Today `cairosvg`
   renders vector-clean at the PDF's own resolution, so there is nothing to tune.
   Proposal: no.
5. **Delete `pages_to_pdf.py`, or leave it as a thin two-line wrapper that calls
   both scripts in order?** Proposal: delete it — a wrapper is a third thing to
   keep honest, and the two commands are easy to run in sequence.

## Appendix — measurements taken for this plan

| probe | result |
|---|---|
| `pages_to_pdf.py` length | 374 lines |
| render boundary | `render_sheets()` starts at line 234; nothing above it renders, nothing below it computes layout |
| shared state the split must not duplicate | the `sheets/` cleanup in `render_sheets()` (lines 237–240) unlinks **both** `.svg` and `.pdf` |
| the only layout assumption outside `build_sheets()` | `verify_scale()`'s `doc[0]` + `MARGIN` offset (lines 323–327) |
| page size now | Letter landscape 279.4 x 215.9 mm, margin 5, overlap 12, slack 2 |
| files named by both scripts | `sheets/sheet-NNN.svg`, `sheets/sheet-NNN.pdf`, `feathers-letter-landscape.pdf`, `contact-sheet.png` |
| third-party imports by half | Script 1: none. Script 2: `cairosvg`, `pypdf`, `pdfium`, `PIL` |
